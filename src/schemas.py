"""Esquemas de datos para el bot de gastos."""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class TelegramUser:
    """Usuario de Telegram."""
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]

    def get_display_name(self) -> str:
        """Retorna el nombre para mostrar."""
        if self.username:
            return f"@{self.username}"
        name = self.first_name
        if self.last_name:
            name += f" {self.last_name}"
        return name

    @classmethod
    def from_telegram_update(cls, user_data: Dict[str, Any]) -> "TelegramUser":
        """Crea instancia desde update de Telegram."""
        return cls(
            user_id=user_data["id"],
            username=user_data.get("username"),
            first_name=user_data.get("first_name", "Unknown"),
            last_name=user_data.get("last_name")
        )


@dataclass
class TelegramChat:
    """Chat de Telegram."""
    chat_id: int
    type: str  # "private", "group", "supergroup", "channel"
    title: Optional[str]

    @classmethod
    def from_telegram_update(cls, chat_data: Dict[str, Any]) -> "TelegramChat":
        """Crea instancia desde update de Telegram."""
        return cls(
            chat_id=chat_data["id"],
            type=chat_data["type"],
            title=chat_data.get("title")
        )


@dataclass
class TelegramMessage:
    """Mensaje de Telegram."""
    message_id: int
    user: TelegramUser
    chat: TelegramChat
    text: str
    date: int

    @classmethod
    def from_telegram_update(cls, update: Dict[str, Any]) -> "TelegramMessage":
        """Crea instancia desde update de Telegram."""
        message = update.get("message", {})
        return cls(
            message_id=message["message_id"],
            user=TelegramUser.from_telegram_update(message["from"]),
            chat=TelegramChat.from_telegram_update(message["chat"]),
            text=message.get("text", ""),
            date=message.get("date", 0)
        )


@dataclass
class Gasto:
    """Modelo de un gasto/ingreso."""
    chat_id: int
    message_id: int
    user_id: int
    ts: int
    date_iso: str
    amount: float
    currency: str
    category: str
    description: str
    payee: str

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para JSON."""
        return {
            "chat_id": self.chat_id,
            "message_id": self.message_id,
            "user_id": self.user_id,
            "ts": self.ts,
            "date_iso": self.date_iso,
            "amount": self.amount,
            "currency": self.currency,
            "category": self.category,
            "description": self.description,
            "payee": self.payee
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Gasto":
        """Crea instancia desde diccionario."""
        return cls(**data)


@dataclass
class SessionDraft:
    """Borrador de gasto en sesión."""
    type: str  # "expense" o "income"
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "type": self.type,
            "amount": self.amount,
            "currency": self.currency,
            "category": self.category,
            "description": self.description
        }
