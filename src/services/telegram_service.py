"""Servicio para interactuar con la API de Telegram."""
import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, List
from src.config.settings import settings
from src.utils.logger import setup_logger
from src.schemas import TelegramMessage

logger = setup_logger(__name__)


class TelegramService:
    """Servicio para interactuar con la API de Telegram usando aiohttp."""

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea la sesión de aiohttp."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Cierra la sesión de aiohttp."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_updates(self, offset: Optional[int] = None, timeout: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene las actualizaciones del bot de Telegram.

        Args:
            offset: Offset para obtener solo updates nuevos
            timeout: Timeout de long polling de Telegram (segundos)

        Returns:
            Lista de updates
        """
        url = f"{self.base_url}/getUpdates"
        params: Dict[str, int] = {"timeout": timeout}

        if offset is not None:
            params["offset"] = offset

        try:
            session = await self._get_session()
            # HTTP timeout debe ser mayor que el de Telegram
            http_timeout = aiohttp.ClientTimeout(total=timeout + 10)

            async with session.get(url, params=params, timeout=http_timeout) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get("ok"):
                    return data.get("result", [])
                else:
                    logger.error(f"Error en getUpdates: {data}")
                    return []

        except aiohttp.ClientError as e:
            logger.error(f"Error al obtener actualizaciones de Telegram: {e}")
            return []
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout al obtener actualizaciones de Telegram: {e}")
            return []

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        reply_to_message_id: Optional[int] = None
    ) -> bool:
        """
        Envía un mensaje de texto al chat.

        Args:
            chat_id: ID del chat
            text: Texto del mensaje
            reply_markup: Teclado personalizado (opcional)
            reply_to_message_id: ID del mensaje al que responde (opcional)

        Returns:
            True si se envió correctamente
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            session = await self._get_session()
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("ok", False)

        except aiohttp.ClientError as e:
            logger.error(f"Error al enviar mensaje: {e}")
            return False

    def make_keyboard_buttons(self, buttons: List[str], columns: int = 3) -> Dict[str, Any]:
        """
        Crea un teclado con botones.

        Args:
            buttons: Lista de textos de botones
            columns: Número de columnas

        Returns:
            Reply markup para Telegram
        """
        rows = []
        row = []

        for i, button in enumerate(buttons, 1):
            row.append({"text": button})
            if i % columns == 0:
                rows.append(row)
                row = []

        if row:
            rows.append(row)

        return {
            "keyboard": rows,
            "resize_keyboard": True,
            "one_time_keyboard": True
        }

    def make_main_menu(self) -> Dict[str, Any]:
        """Crea el menú principal del bot."""
        return {
            "keyboard": [
                [{"text": "💸 Nuevo Gasto"}, {"text": "💰 Nuevo Ingreso"}],
                [{"text": "📊 Ver Categorías"}, {"text": "📤 Exportar CSV"}],
                [{"text": "❓ Ayuda"}]
            ],
            "resize_keyboard": True,
            "persistent": True
        }

    async def start_polling(self, on_message_callback):
        """
        Inicia el polling de mensajes.

        Args:
            on_message_callback: Callback async para procesar cada mensaje
        """
        offset = 0
        consecutive_empty = 0  # Contador de polls vacíos consecutivos

        logger.info("Iniciando polling de Telegram...")

        try:
            while True:
                try:
                    # Solo loguear cada 10 polls vacíos
                    if consecutive_empty % 10 == 0:
                        logger.debug(f"Polling... (offset={offset+1})")

                    updates = await self.get_updates(offset=offset+1 if offset > 0 else None, timeout=settings.POLLING_INTERVAL)

                    if not updates:
                        consecutive_empty += 1
                        continue

                    # Reseteamos contador si hay mensajes
                    consecutive_empty = 0
                    logger.info(f"📥 {len(updates)} mensaje(s) nuevo(s)")

                    for update in updates:
                        offset = max(offset, update["update_id"])

                        # Procesar el mensaje
                        try:
                            await on_message_callback(update)
                        except Exception as e:
                            logger.error(f"Error procesando update {update.get('update_id')}: {e}", exc_info=True)

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"Error en el polling: {e}")
                    await asyncio.sleep(5)

        except KeyboardInterrupt:
            logger.info("Polling detenido por el usuario")
        finally:
            await self.close()

        return offset
