"""Bot principal - Orquestador de servicios."""
import asyncio
from src.config.settings import settings
from src.services.telegram_service import TelegramService
from src.services.gastos_service import GastosService
from src.repositories.ledger_repository import LedgerRepository
from src.schemas import TelegramMessage
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GastosBot:
    """Bot de Gastos - Orquesta todos los servicios."""

    def __init__(self):
        self.telegram_service = TelegramService()
        self.ledger_repository = LedgerRepository()
        self.gastos_service = GastosService(
            telegram_service=self.telegram_service,
            ledger_repository=self.ledger_repository
        )

    async def process_message(self, update: dict):
        """
        Procesa un update de Telegram.

        Args:
            update: Update raw de Telegram
        """
        # Extraer mensaje
        msg = update.get("message")
        if not msg:
            logger.debug(f"Update sin mensaje (tipo: {list(update.keys())})")
            return

        try:
            # Convertir a TelegramMessage
            message = TelegramMessage.from_telegram_update(update)

            logger.info(f"Mensaje de {message.user.get_display_name()}: {message.text[:50]}...")

            # Obtener sesión del usuario
            session = self.ledger_repository.get_session(message.user.user_id) or {
                "stage": None,
                "draft": {}
            }

            current_stage = session.get("stage")
            text = message.text.strip()

            # === Manejo de comandos y botones (sin sesión activa) ===

            if text == "/start":
                await self.gastos_service.handle_command_start(message)
                self.ledger_repository.clear_session(message.user.user_id)
                return

            if text == "💸 Nuevo Gasto":
                stage, draft = await self.gastos_service.handle_button_nuevo_gasto(message)
                self.ledger_repository.save_session(message.user.user_id, {"stage": stage, "draft": draft})
                return

            if text == "💰 Nuevo Ingreso":
                stage, draft = await self.gastos_service.handle_button_nuevo_ingreso(message)
                self.ledger_repository.save_session(message.user.user_id, {"stage": stage, "draft": draft})
                return

            if text == "📊 Ver Categorías":
                await self.gastos_service.handle_button_ver_categorias(message)
                return

            if text == "📤 Exportar CSV" or text == "/export":
                await self.gastos_service.handle_button_exportar_csv(message)
                return

            if text == "❓ Ayuda":
                await self.gastos_service.handle_button_ayuda(message)
                return

            # === Wizard guiado (con sesión activa) ===

            if current_stage == "amount":
                stage, draft = await self.gastos_service.process_wizard_amount(message, session)
                if stage:
                    self.ledger_repository.save_session(message.user.user_id, {"stage": stage, "draft": draft})
                else:
                    self.ledger_repository.clear_session(message.user.user_id)
                return

            if current_stage == "currency":
                stage, draft = await self.gastos_service.process_wizard_currency(message, session)
                if stage:
                    self.ledger_repository.save_session(message.user.user_id, {"stage": stage, "draft": draft})
                else:
                    self.ledger_repository.clear_session(message.user.user_id)
                return

            if current_stage == "category":
                stage, draft = await self.gastos_service.process_wizard_category(message, session)
                if stage:
                    self.ledger_repository.save_session(message.user.user_id, {"stage": stage, "draft": draft})
                else:
                    self.ledger_repository.clear_session(message.user.user_id)
                return

            if current_stage == "description":
                stage, draft = await self.gastos_service.process_wizard_description(message, session)
                self.ledger_repository.clear_session(message.user.user_id)
                return

            # Si llega acá, es un mensaje no reconocido
            logger.debug(f"Mensaje no reconocido: {text}")

        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}", exc_info=True)
            # Intentar notificar al usuario
            try:
                await self.telegram_service.send_message(
                    msg["chat"]["id"],
                    f"❌ Error inesperado: {str(e)}"
                )
            except:
                pass

    async def start(self):
        """Inicia el bot."""
        try:
            logger.info("=" * 60)
            logger.info("🤖 Bot de Gastos - Modo Servidor 24/7")
            logger.info("=" * 60)

            # Validar configuración
            settings.validate()
            logger.info("✅ Configuración validada")

            # Información del bot
            logger.info(f"📡 Intervalo de polling: {settings.POLLING_INTERVAL}s")
            logger.info(f"💰 Moneda por defecto: {settings.DEFAULT_CURRENCY}")
            logger.info(f"📂 Categorías: {len(settings.CATEGORIES)}")

            # Cargar offset anterior
            offset = self.ledger_repository.get_update_offset()
            logger.info(f"🔄 Último update procesado: {offset}")

            # Callback para procesar mensajes y actualizar offset
            async def on_message(update):
                await self.process_message(update)
                # Actualizar offset
                new_offset = update.get("update_id", 0)
                if new_offset > offset:
                    self.ledger_repository.save_update_offset(new_offset)

            # Iniciar polling
            logger.info("\n🚀 Bot iniciado. Esperando mensajes...\n")
            await self.telegram_service.start_polling(on_message)

        except ValueError as e:
            logger.error(f"❌ Error de configuración: {e}")
            logger.error("Por favor, configurá las variables en config.yaml")
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Bot detenido por el usuario")
        except Exception as e:
            logger.error(f"❌ Error fatal: {e}", exc_info=True)
        finally:
            # Cerrar conexiones
            logger.info("Cerrando conexiones...")
            await self.telegram_service.close()
            logger.info("✅ Conexiones cerradas correctamente")
