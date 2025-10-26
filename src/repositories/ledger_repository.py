"""Repositorio para acceso y persistencia de gastos."""
import json
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    delete,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config.settings import settings
from src.schemas import Gasto
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()


def _default_state() -> Dict[str, Any]:
    return {"update_offset": 0, "sessions": {}}


class LedgerEntry(Base):
    """Tabla de movimientos registrados por el bot."""

    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    ts = Column(BigInteger, nullable=False)
    date_iso = Column(String(32), nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String(12), nullable=False)
    category = Column(String(128), nullable=False)
    description = Column(Text, default="")
    payee = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("chat_id", "message_id", name="uq_ledger_chat_message"),
    )

    @classmethod
    def from_gasto(cls, gasto: Gasto) -> "LedgerEntry":
        return cls(
            chat_id=gasto.chat_id,
            message_id=gasto.message_id,
            user_id=gasto.user_id,
            ts=int(gasto.ts),
            date_iso=gasto.date_iso,
            amount=int(gasto.amount),
            currency=gasto.currency,
            category=gasto.category,
            description=gasto.description,
            payee=gasto.payee,
        )

    def to_gasto(self) -> Gasto:
        return Gasto(
            chat_id=self.chat_id,
            message_id=self.message_id,
            user_id=self.user_id,
            ts=self.ts,
            date_iso=self.date_iso,
            amount=self.amount,
            currency=self.currency,
            category=self.category,
            description=self.description or "",
            payee=self.payee or "",
        )


class BotState(Base):
    """Tabla para almacenar estado del bot (offset, sesiones, etc.)."""

    __tablename__ = "bot_state"

    key = Column(String(64), primary_key=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class _DatabaseLedgerBackend:
    """Implementación basada en PostgreSQL."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, pool_pre_ping=True, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False, future=True)
        Base.metadata.create_all(self.engine)
        logger.info("LedgerRepository inicializado con backend de base de datos")

    @contextmanager
    def session_scope(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # === Ledger ===
    def load_ledger(self) -> List[Gasto]:
        with self.SessionLocal() as session:
            result = session.execute(select(LedgerEntry).order_by(LedgerEntry.ts))
            return [row.to_gasto() for row in result.scalars().all()]

    def save_ledger(self, gastos: List[Gasto]):
        with self.session_scope() as session:
            session.execute(delete(LedgerEntry))
            for gasto in gastos:
                session.add(LedgerEntry.from_gasto(gasto))

    def append_gasto(self, gasto: Gasto) -> bool:
        entry = LedgerEntry.from_gasto(gasto)
        session = self.SessionLocal()
        try:
            session.add(entry)
            session.commit()
            logger.info(
                "Gasto agregado en base de datos: %s %s - %s",
                gasto.amount,
                gasto.currency,
                gasto.category,
            )
            return True
        except IntegrityError:
            session.rollback()
            logger.warning(
                "Gasto duplicado en base de datos (chat_id=%s, message_id=%s), ignorando",
                gasto.chat_id,
                gasto.message_id,
            )
            return False
        finally:
            session.close()

    # === Estado ===
    def _load_state_row(self) -> Dict[str, Any]:
        with self.SessionLocal() as session:
            state = session.get(BotState, "global_state")
            if not state:
                return _default_state()
            stored = state.value or {}
            stored.setdefault("update_offset", 0)
            stored.setdefault("sessions", {})
            return stored

    def load_state(self) -> Dict[str, Any]:
        return self._load_state_row()

    def save_state(self, state: Dict[str, Any]):
        with self.session_scope() as session:
            current = session.get(BotState, "global_state")
            if current:
                current.value = state
            else:
                session.add(BotState(key="global_state", value=state))

    def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        state = self._load_state_row()
        return state.get("sessions", {}).get(str(user_id))

    def save_session(self, user_id: int, session_data: Dict[str, Any]):
        state = self._load_state_row()
        state.setdefault("sessions", {})[str(user_id)] = session_data
        self.save_state(state)

    def clear_session(self, user_id: int):
        state = self._load_state_row()
        state.get("sessions", {}).pop(str(user_id), None)
        self.save_state(state)

    def get_update_offset(self) -> int:
        state = self._load_state_row()
        return int(state.get("update_offset", 0))

    def save_update_offset(self, offset: int):
        state = self._load_state_row()
        state["update_offset"] = int(offset)
        self.save_state(state)


class _FileLedgerBackend:
    """Implementación basada en archivos JSON (legado)."""

    def __init__(self, ledger_path: str = "data/ledger.json", state_path: str = "state.json"):
        self.ledger_path = ledger_path
        self.state_path = state_path
        self._ensure_data_dir()
        logger.info("LedgerRepository inicializado con backend de archivos")

    def _ensure_data_dir(self):
        Path("data").mkdir(exist_ok=True)

    # === Ledger ===
    def load_ledger(self) -> List[Gasto]:
        if not os.path.exists(self.ledger_path):
            return []

        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Gasto.from_dict(item) for item in data]
        except Exception as e:
            logger.error("Error cargando ledger: %s", e)
            return []

    def save_ledger(self, gastos: List[Gasto]):
        try:
            with open(self.ledger_path, "w", encoding="utf-8") as f:
                data = [gasto.to_dict() for gasto in gastos]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Error guardando ledger: %s", e)
            raise

    def append_gasto(self, gasto: Gasto) -> bool:
        gastos = self.load_ledger()

        key = (gasto.chat_id, gasto.message_id)
        existing_keys = {(g.chat_id, g.message_id) for g in gastos}

        if key in existing_keys:
            logger.warning(
                "Gasto duplicado (chat_id=%s, message_id=%s), ignorando",
                gasto.chat_id,
                gasto.message_id,
            )
            return False

        gastos.append(gasto)
        self.save_ledger(gastos)
        logger.info(
            "Gasto agregado: %s %s - %s",
            gasto.amount,
            gasto.currency,
            gasto.category,
        )
        return True

    # === Estado ===
    def load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.state_path):
            return _default_state()

        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Error cargando state: %s", e)
            return _default_state()

    def save_state(self, state: Dict[str, Any]):
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Error guardando state: %s", e)
            raise

    def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        state = self.load_state()
        return state.get("sessions", {}).get(str(user_id))

    def save_session(self, user_id: int, session_data: Dict[str, Any]):
        state = self.load_state()
        state.setdefault("sessions", {})[str(user_id)] = session_data
        self.save_state(state)

    def clear_session(self, user_id: int):
        state = self.load_state()
        state.get("sessions", {}).pop(str(user_id), None)
        self.save_state(state)

    def get_update_offset(self) -> int:
        state = self.load_state()
        return state.get("update_offset", 0)

    def save_update_offset(self, offset: int):
        state = self.load_state()
        state["update_offset"] = offset
        self.save_state(state)


class LedgerRepository:
    """Fachada que expone una API uniforme para ambos backends."""

    def __init__(
        self,
        ledger_path: str = "data/ledger.json",
        state_path: str = "state.json",
        database_url: Optional[str] = None,
    ):
        db_url = database_url or settings.DATABASE_URL
        # Validar que la URL no sea None ni cadena vacía
        if db_url and db_url.strip():
            self._backend = _DatabaseLedgerBackend(db_url)
        else:
            self._backend = _FileLedgerBackend(ledger_path, state_path)

    def load_ledger(self) -> List[Gasto]:
        return self._backend.load_ledger()

    def save_ledger(self, gastos: List[Gasto]):
        self._backend.save_ledger(gastos)

    def append_gasto(self, gasto: Gasto) -> bool:
        return self._backend.append_gasto(gasto)

    def load_state(self) -> Dict[str, Any]:
        return self._backend.load_state()

    def save_state(self, state: Dict[str, Any]):
        self._backend.save_state(state)

    def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self._backend.get_session(user_id)

    def save_session(self, user_id: int, session_data: Dict[str, Any]):
        self._backend.save_session(user_id, session_data)

    def clear_session(self, user_id: int):
        self._backend.clear_session(user_id)

    def get_update_offset(self) -> int:
        return self._backend.get_update_offset()

    def save_update_offset(self, offset: int):
        self._backend.save_update_offset(offset)

