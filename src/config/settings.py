"""Configuración centralizada del bot."""
import os
import yaml
from typing import List


class Settings:
    """Clase de configuración singleton."""

    def __init__(self):
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """Carga configuración desde config.yaml."""
        config_path = os.getenv("CONFIG_PATH", "config.yaml")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Sobrescribir con variables de entorno si existen
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            config["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN")

        return config

    @property
    def TELEGRAM_BOT_TOKEN(self) -> str:
        """Token del bot de Telegram."""
        token = self._config.get("bot_token")
        if not token or token == "TU_TOKEN_DE_BOTFATHER":
            raise ValueError("TELEGRAM_BOT_TOKEN no configurado en config.yaml")
        return token

    @property
    def DEFAULT_CURRENCY(self) -> str:
        """Moneda por defecto."""
        return self._config.get("default_currency", "ARS")

    @property
    def TIMEZONE(self) -> str:
        """Zona horaria."""
        return self._config.get("timezone", "America/Argentina/Buenos_Aires")

    @property
    def CATEGORIES(self) -> List[str]:
        """Lista de categorías disponibles."""
        return self._config.get("categories", [
            "Comida", "Supermercado", "Transporte", "Servicios",
            "Alquiler", "Salud", "Educación", "Ocio", "Ropa", "Varios"
        ])

    @property
    def PAYEE_DEFAULT(self) -> str:
        """Pagador por defecto."""
        return self._config.get("payee_default", "")

    @property
    def LOG_LEVEL(self) -> str:
        """Nivel de logging."""
        return self._config.get("log_level", "INFO")

    @property
    def POLLING_INTERVAL(self) -> int:
        """Intervalo de polling en segundos."""
        return self._config.get("polling_interval", 5)

    def validate(self):
        """Valida que la configuración esté completa."""
        _ = self.TELEGRAM_BOT_TOKEN  # Lanza error si no está configurado


# Singleton
settings = Settings()
