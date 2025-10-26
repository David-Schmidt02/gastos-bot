"""Repositorio para acceso a datos de gastos."""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.schemas import Gasto
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class LedgerRepository:
    """Repositorio para gestión del ledger de gastos."""

    def __init__(self, ledger_path: str = "data/ledger.json", state_path: str = "state.json"):
        self.ledger_path = ledger_path
        self.state_path = state_path
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Asegura que el directorio de datos exista."""
        Path("data").mkdir(exist_ok=True)

    def load_ledger(self) -> List[Gasto]:
        """Carga todos los gastos del ledger."""
        if not os.path.exists(self.ledger_path):
            return []

        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Gasto.from_dict(item) for item in data]
        except Exception as e:
            logger.error(f"Error cargando ledger: {e}")
            return []

    def save_ledger(self, gastos: List[Gasto]):
        """Guarda todos los gastos en el ledger."""
        try:
            with open(self.ledger_path, "w", encoding="utf-8") as f:
                data = [gasto.to_dict() for gasto in gastos]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando ledger: {e}")
            raise

    def append_gasto(self, gasto: Gasto) -> bool:
        """
        Agrega un gasto al ledger (idempotente).

        Returns:
            True si se agregó, False si ya existía
        """
        gastos = self.load_ledger()

        # Verificar duplicados por (chat_id, message_id)
        key = (gasto.chat_id, gasto.message_id)
        existing_keys = {(g.chat_id, g.message_id) for g in gastos}

        if key in existing_keys:
            logger.warning(f"Gasto duplicado (chat_id={gasto.chat_id}, message_id={gasto.message_id}), ignorando")
            return False

        gastos.append(gasto)
        self.save_ledger(gastos)
        logger.info(f"Gasto agregado: {gasto.amount} {gasto.currency} - {gasto.category}")
        return True

    def load_state(self) -> Dict[str, Any]:
        """Carga el estado del bot (offset y sesiones)."""
        if not os.path.exists(self.state_path):
            return {"update_offset": 0, "sessions": {}}

        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando state: {e}")
            return {"update_offset": 0, "sessions": {}}

    def save_state(self, state: Dict[str, Any]):
        """Guarda el estado del bot."""
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando state: {e}")
            raise

    def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene la sesión de un usuario."""
        state = self.load_state()
        return state.get("sessions", {}).get(str(user_id))

    def save_session(self, user_id: int, session_data: Dict[str, Any]):
        """Guarda la sesión de un usuario."""
        state = self.load_state()
        state.setdefault("sessions", {})[str(user_id)] = session_data
        self.save_state(state)

    def clear_session(self, user_id: int):
        """Limpia la sesión de un usuario."""
        state = self.load_state()
        state.get("sessions", {}).pop(str(user_id), None)
        self.save_state(state)

    def get_update_offset(self) -> int:
        """Obtiene el último update_id procesado."""
        state = self.load_state()
        return state.get("update_offset", 0)

    def save_update_offset(self, offset: int):
        """Guarda el último update_id procesado."""
        state = self.load_state()
        state["update_offset"] = offset
        self.save_state(state)
