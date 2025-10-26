"""Cliente simple para interactuar con Actual Budget."""
from __future__ import annotations

import uuid
from typing import Dict, Optional
from urllib.parse import urljoin

import aiohttp

from src.config.settings import settings
from src.schemas import Gasto
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ActualBudgetService:
    """Servicio HTTP mínimo para insertar transacciones en Actual Budget."""

    IMPORT_ENDPOINT = "api/v1/budgets/{budget_id}/import-transactions"
    TRANSACTIONS_ENDPOINT = "api/v1/budgets/{budget_id}/transactions"

    def __init__(self):
        self.base_url = settings.ACTUAL_BUDGET_API_URL.rstrip("/") if settings.ACTUAL_BUDGET_API_URL else None
        self.api_token = settings.ACTUAL_BUDGET_API_TOKEN
        self.budget_id = settings.ACTUAL_BUDGET_BUDGET_ID
        self.account_id = settings.ACTUAL_BUDGET_ACCOUNT_ID
        self.encryption_key = settings.ACTUAL_BUDGET_ENCRYPTION_KEY
        self._session: Optional[aiohttp.ClientSession] = None

    def is_configured(self) -> bool:
        """Indica si hay suficiente configuración para sincronizar."""
        return bool(self.base_url and self.budget_id and self.account_id)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session

        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        if self.encryption_key:
            headers["X-Actual-Encryption-Key"] = self.encryption_key

        timeout = aiohttp.ClientTimeout(total=15)
        self._session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self._session

    def _build_transaction_payload(self, gasto: Gasto, account_id: str = None) -> Dict[str, object]:
        """Genera el payload compatible con la API de Actual Budget."""

        date_iso = gasto.date_iso.split(" ")[0] if gasto.date_iso else None
        amount_milliunits = int(gasto.amount) * 1000
        payee = gasto.payee or settings.PAYEE_DEFAULT or None

        # Usar el account_id pasado como parámetro, o el configurado por defecto
        target_account_id = account_id or self.account_id

        payload: Dict[str, object] = {
            "id": str(uuid.uuid4()),
            "accountId": target_account_id,
            "amount": amount_milliunits,
            "date": date_iso,
            "notes": gasto.description or None,
            "importedId": f"telegram:{gasto.chat_id}:{gasto.message_id}",
            "metadata": {
                "chatId": gasto.chat_id,
                "messageId": gasto.message_id,
                "userId": gasto.user_id,
            },
        }

        if payee:
            payload["payeeName"] = payee

        if gasto.category:
            payload["categoryName"] = gasto.category

        return payload

    async def create_transaction(self, gasto: Gasto, account_id: str = None):
        """Inserta una transacción en Actual Budget."""
        if not self.is_configured():
            logger.debug("Actual Budget no configurado, omitiendo sincronización")
            return

        # Usar el account_id pasado como parámetro, o el configurado por defecto
        target_account_id = account_id or self.account_id

        payload = self._build_transaction_payload(gasto, account_id=target_account_id)
        session = await self._get_session()

        endpoints = [
            self.IMPORT_ENDPOINT.format(budget_id=self.budget_id),
            self.TRANSACTIONS_ENDPOINT.format(budget_id=self.budget_id),
        ]

        for path in endpoints:
            endpoint = urljoin(f"{self.base_url}/", path)
            body = {"accountId": target_account_id, "transactions": [payload]}
            logger.debug("Intentando sincronizar en %s", endpoint)

            try:
                async with session.post(endpoint, json=body) as response:
                    if response.status == 404 and path == endpoints[0]:
                        # Algunas versiones del server no soportan import-transactions
                        logger.debug("Endpoint import-transactions no disponible, probando fallback")
                        continue

                    if response.status >= 400:
                        error_body = await response.text()
                        logger.error(
                            "Actual Budget rechazó la transacción (%s): %s",
                            response.status,
                            error_body,
                        )
                        return

                    logger.info("Transacción sincronizada con Actual Budget (%s)", path)
                    return
            except aiohttp.ClientError as exc:
                logger.error("Error HTTP al sincronizar con Actual Budget: %s", exc, exc_info=True)
                return
            except Exception as exc:  # pragma: no cover - fallback ante errores inesperados
                logger.error("No se pudo sincronizar con Actual Budget: %s", exc, exc_info=True)
                return

        logger.error("No se pudo sincronizar con Actual Budget: endpoints agotados")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

