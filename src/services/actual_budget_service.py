"""Cliente para interactuar con Actual Budget usando actualpy."""
from __future__ import annotations

import asyncio
import datetime
from decimal import Decimal
from typing import Optional

from actual import Actual
from actual.queries import reconcile_transaction, get_account

from src.config.settings import settings
from src.schemas import Gasto
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ActualBudgetService:
    """Servicio para insertar transacciones en Actual Budget usando actualpy."""

    def __init__(self):
        self.base_url = settings.ACTUAL_BUDGET_API_URL.rstrip("/") if settings.ACTUAL_BUDGET_API_URL else None
        self.password = settings.ACTUAL_BUDGET_PASSWORD
        self.budget_id = settings.ACTUAL_BUDGET_BUDGET_ID
        self.encryption_key = settings.ACTUAL_BUDGET_ENCRYPTION_KEY

    def is_configured(self) -> bool:
        """Indica si hay suficiente configuración para sincronizar."""
        return bool(self.base_url and self.budget_id and self.password)

    def _create_transaction_sync(self, gasto: Gasto, account_id: str):
        """
        Crea una transacción usando actualpy (síncrono).

        Esta función se ejecuta en un thread separado para no bloquear el event loop.
        """
        logger.debug(f"Conectando a Actual Budget: {self.base_url}, budget: {self.budget_id}")

        with Actual(
            base_url=self.base_url,
            password=self.password,
            file=self.budget_id,
            encryption_password=self.encryption_key,
        ) as actual:
            # Obtener la cuenta
            try:
                account = get_account(actual.session, account_id)
                if not account:
                    logger.error(f"Cuenta no encontrada: {account_id}")
                    return
            except Exception as e:
                logger.error(f"Error al obtener cuenta {account_id}: {e}")
                return

            # Parsear fecha
            date_str = gasto.date_iso.split(" ")[0] if gasto.date_iso else None
            if date_str:
                try:
                    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    date = datetime.date.today()
            else:
                date = datetime.date.today()

            # Convertir monto a Decimal (actualpy usa Decimal, no milliunits)
            amount = Decimal(str(gasto.amount))

            # Payee
            payee = gasto.payee or settings.PAYEE_DEFAULT or None

            # Notes (descripción)
            notes = gasto.description or ""

            # Categoría (nombre de categoría)
            category = gasto.category if gasto.category else None

            # Crear imported_id único para evitar duplicados
            imported_id = f"telegram:{gasto.chat_id}:{gasto.message_id}"

            logger.info(f"Creando transacción: {date} | {amount} {gasto.currency} | {category} | {payee}")

            # Usar reconcile_transaction que maneja duplicados automáticamente
            try:
                t = reconcile_transaction(
                    actual.session,
                    date=date,
                    account=account,
                    payee=payee,
                    notes=notes,
                    category=category,
                    amount=amount,
                    imported_id=imported_id,
                    cleared=True,  # Marcar como cleared
                )

                # Verificar si es nueva o existente ANTES del commit
                is_new = t and t.changed()

                # Commit para sincronizar con el servidor
                actual.commit()

                if is_new:
                    logger.info(f"✅ Transacción nueva sincronizada con Actual Budget: {t.id}")
                else:
                    logger.info("ℹ️ Transacción ya existía (duplicado evitado)")

            except Exception as e:
                logger.error(f"Error al crear transacción: {e}", exc_info=True)
                raise

    async def create_transaction(self, gasto: Gasto, account_id: str = None):
        """Inserta una transacción en Actual Budget (async wrapper)."""
        logger.debug(f"create_transaction llamado - base_url={self.base_url}, budget_id={self.budget_id}, account_id={account_id}")

        if not self.is_configured():
            logger.warning(f"Actual Budget no configurado correctamente - base_url={self.base_url}, budget_id={self.budget_id}, password={'***' if self.password else None}")
            return

        # Validar que haya un account_id válido
        if not account_id:
            logger.error("No se puede sincronizar: account_id no especificado")
            return

        logger.info(f"Sincronizando transacción: {gasto.amount} {gasto.currency} - {gasto.category} → cuenta {account_id}")

        try:
            # Ejecutar la función síncrona en un thread separado
            await asyncio.to_thread(self._create_transaction_sync, gasto, account_id)
        except Exception as exc:
            logger.error(f"Fallo al sincronizar con Actual Budget: {exc}", exc_info=True)

    async def close(self):
        """Cierra recursos (no necesario para actualpy, mantiene compatibilidad)."""
        pass
