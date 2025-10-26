"""Servicio para gestión de gastos e ingresos."""
import re
from datetime import datetime
from dateutil import tz
from typing import Optional, Tuple
from src.config.settings import settings
from src.schemas import TelegramMessage, Gasto, SessionDraft
from src.repositories.ledger_repository import LedgerRepository
from src.services.actual_budget_service import ActualBudgetService
from src.services.telegram_service import TelegramService
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GastosService:
    """Servicio para la lógica de negocio de gastos."""

    def __init__(
        self,
        telegram_service: TelegramService,
        ledger_repository: LedgerRepository,
        actual_budget_service: ActualBudgetService = None,
    ):
        self.telegram = telegram_service
        self.ledger = ledger_repository
        self.actual_budget = actual_budget_service

    async def sync_with_actual_budget(self, gasto: Gasto):
        """Sincroniza el gasto con Actual Budget si hay configuración."""
        if not self.actual_budget:
            return

        try:
            await self.actual_budget.create_transaction(gasto)
        except Exception as exc:
            logger.error("Fallo al sincronizar con Actual Budget: %s", exc, exc_info=True)

    def normalize_amount(self, text: str) -> int:
        """
        Normaliza un monto eliminando puntos y comas.

        Args:
            text: Texto con el monto

        Returns:
            Monto como entero

        Raises:
            ValueError: Si el formato es inválido
        """
        s = str(text).strip()
        s = s.replace(".", "").replace(",", "")
        if not re.fullmatch(r"[+-]?\d+", s):
            raise ValueError("Monto inválido")
        return int(s)

    def to_local_datetime(self, unix_ts: int) -> str:
        """
        Convierte timestamp unix a fecha/hora local.

        Args:
            unix_ts: Timestamp unix

        Returns:
            Fecha en formato "YYYY-MM-DD HH:MM"
        """
        tzinfo = tz.gettz(settings.TIMEZONE)
        dt = datetime.fromtimestamp(unix_ts, tz.UTC).astimezone(tzinfo)
        return dt.strftime("%Y-%m-%d %H:%M")

    async def process_wizard_amount(
        self,
        message: TelegramMessage,
        session: dict
    ) -> Tuple[str, Optional[dict]]:
        """
        Procesa el paso de monto en el wizard.

        Returns:
            (next_stage, updated_draft)
        """
        try:
            amount = self.normalize_amount(message.text)
        except ValueError:
            await self.telegram.send_message(
                message.chat.chat_id,
                "❌ Monto inválido. Solo números, por favor.\n\nEjemplo: 2500"
            )
            return ("amount", session.get("draft"))

        # Actualizar draft
        draft = session.get("draft", {})
        draft["amount"] = abs(amount)

        # Mostrar botones de moneda
        await self.telegram.send_message(
            message.chat.chat_id,
            f"💵 ¿En qué moneda?\n\n(Por defecto: {settings.DEFAULT_CURRENCY})",
            reply_markup=self.telegram.make_keyboard_buttons([settings.DEFAULT_CURRENCY, "USD", "EUR"])
        )

        return ("currency", draft)

    async def process_wizard_currency(
        self,
        message: TelegramMessage,
        session: dict
    ) -> Tuple[str, Optional[dict]]:
        """
        Procesa el paso de moneda en el wizard.

        Returns:
            (next_stage, updated_draft)
        """
        currency = message.text.strip().upper()

        # Validar que sea una moneda de 3 letras
        if len(currency) != 3:
            currency = settings.DEFAULT_CURRENCY

        # Actualizar draft
        draft = session.get("draft", {})
        draft["currency"] = currency

        # Mostrar botones de categorías
        await self.telegram.send_message(
            message.chat.chat_id,
            "📂 Elegí la categoría:",
            reply_markup=self.telegram.make_keyboard_buttons(settings.CATEGORIES)
        )

        return ("category", draft)

    async def process_wizard_category(
        self,
        message: TelegramMessage,
        session: dict
    ) -> Tuple[str, Optional[dict]]:
        """
        Procesa el paso de categoría en el wizard.

        Returns:
            (next_stage, updated_draft)
        """
        category = message.text.strip()

        # Validar categoría
        if category not in settings.CATEGORIES:
            await self.telegram.send_message(
                message.chat.chat_id,
                "❌ Categoría inválida. Elegí una del teclado:"
            )
            return ("category", session.get("draft"))

        # Actualizar draft
        draft = session.get("draft", {})
        draft["category"] = category

        # Pedir descripción
        await self.telegram.send_message(
            message.chat.chat_id,
            "📝 Descripción del gasto (opcional)\n\nEscribí el texto o enviá /omitir"
        )

        return ("description", draft)

    async def process_wizard_description(
        self,
        message: TelegramMessage,
        session: dict
    ) -> Tuple[Optional[str], Optional[dict]]:
        """
        Procesa el paso final (descripción) y guarda el gasto.

        Returns:
            (None, None) - Finaliza el wizard
        """
        description = ""
        if message.text.strip().lower() != "/omitir":
            description = message.text.strip()

        # Crear el gasto
        draft = session.get("draft", {})
        gasto_type = draft.get("type", "expense")

        # Determinar el monto (negativo para gastos, positivo para ingresos)
        amount = draft.get("amount", 0)
        if gasto_type == "expense":
            amount = -abs(amount)
        else:
            amount = abs(amount)

        # Crear objeto Gasto
        gasto = Gasto(
            chat_id=message.chat.chat_id,
            message_id=message.message_id,
            user_id=message.user.user_id,
            ts=message.date,
            date_iso=self.to_local_datetime(message.date),
            amount=amount,
            currency=draft.get("currency", settings.DEFAULT_CURRENCY),
            category=draft.get("category", "Varios"),
            description=description,
            payee=settings.PAYEE_DEFAULT
        )

        # Guardar en ledger
        was_created = self.ledger.append_gasto(gasto)

        if was_created:
            await self.sync_with_actual_budget(gasto)

        # Confirmar al usuario
        await self.telegram.send_message(
            message.chat.chat_id,
            f"✅ {'Gasto' if gasto_type == 'expense' else 'Ingreso'} registrado!\n\n"
            f"💰 {abs(amount)} {gasto.currency}\n"
            f"📂 {gasto.category}\n"
            f"📝 {gasto.description if gasto.description else 'Sin descripción'}\n\n"
            f"Podés seguir registrando desde el menú.",
            reply_markup=self.telegram.make_main_menu()
        )

        return (None, None)

    async def handle_button_nuevo_gasto(self, message: TelegramMessage) -> Tuple[str, dict]:
        """Maneja el botón 'Nuevo Gasto'."""
        draft = {"type": "expense"}

        await self.telegram.send_message(
            message.chat.chat_id,
            "💸 Nuevo Gasto\n\n¿Cuál es el monto?\n\nEjemplo: 2500"
        )

        return ("amount", draft)

    async def handle_button_nuevo_ingreso(self, message: TelegramMessage) -> Tuple[str, dict]:
        """Maneja el botón 'Nuevo Ingreso'."""
        draft = {"type": "income"}

        await self.telegram.send_message(
            message.chat.chat_id,
            "💰 Nuevo Ingreso\n\n¿Cuál es el monto?\n\nEjemplo: 50000"
        )

        return ("amount", draft)

    async def handle_button_ver_categorias(self, message: TelegramMessage):
        """Maneja el botón 'Ver Categorías'."""
        categorias_text = "📋 Categorías disponibles:\n\n"
        for i, cat in enumerate(settings.CATEGORIES, 1):
            categorias_text += f"{i}. {cat}\n"

        await self.telegram.send_message(message.chat.chat_id, categorias_text)

    async def handle_button_exportar_csv(self, message: TelegramMessage):
        """Maneja el botón 'Exportar CSV'."""
        from src.services.export_service import export_to_csv

        gastos = self.ledger.load_ledger()
        n = export_to_csv(gastos)

        await self.telegram.send_message(
            message.chat.chat_id,
            f"✅ CSV generado!\n\n"
            f"📊 {n} movimientos exportados\n"
            f"📁 data/import_actual.csv\n\n"
            f"Importalo en Actual Budget:\n"
            f"Cuenta → Import → CSV"
        )

    async def handle_button_ayuda(self, message: TelegramMessage):
        """Maneja el botón 'Ayuda'."""
        help_text = (
            "📖 *Ayuda del Bot de Gastos*\n\n"
            "🔹 *Menú principal:*\n"
            "Usá los botones para registrar gastos guiados.\n\n"
            "🔹 *Comandos disponibles:*\n"
            "• /start - Mostrar menú\n"
            "• /export - Exportar CSV\n\n"
            "🔹 *Flujo de registro:*\n"
            "1. Click en 💸 Nuevo Gasto\n"
            "2. Ingresá el monto\n"
            "3. Seleccioná moneda\n"
            "4. Seleccioná categoría\n"
            "5. Agregá descripción (opcional)\n\n"
            "💡 Los gastos se sincronizan automáticamente."
        )

        await self.telegram.send_message(message.chat.chat_id, help_text)

    async def handle_command_start(self, message: TelegramMessage):
        """Maneja el comando /start."""
        await self.telegram.send_message(
            message.chat.chat_id,
            "¡Hola! 👋 Bienvenido al Bot de Gastos para Actual Budget.\n\n"
            "Usá los botones del menú para registrar gastos de forma guiada.",
            reply_markup=self.telegram.make_main_menu()
        )
