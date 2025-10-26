"""Configuración centralizada del bot."""
import os
import yaml
from typing import List, Optional


class Settings:
    """Clase de configuración singleton."""

    def __init__(self):
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """
        Carga configuración desde config.yaml (local) o env vars (producción).

        Prioridad: ENV VARS > config.yaml > DEFAULTS
        """
        config = {}
        config_path = os.getenv("CONFIG_PATH", "config.yaml")

        # Intentar cargar config.yaml si existe (local development)
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️  No se pudo cargar {config_path}: {e}")
                config = {}

        # Normalizar secciones
        config.setdefault("actual_budget", {})

        # Sobrescribir/agregar con variables de entorno (production)
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            config["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN")

        if os.getenv("DEFAULT_CURRENCY"):
            config["default_currency"] = os.getenv("DEFAULT_CURRENCY")

        if os.getenv("TIMEZONE"):
            config["timezone"] = os.getenv("TIMEZONE")

        if os.getenv("LOG_LEVEL"):
            config["log_level"] = os.getenv("LOG_LEVEL")

        # Categorías desde env (separadas por comas)
        if os.getenv("CATEGORIES"):
            config["categories"] = [cat.strip() for cat in os.getenv("CATEGORIES").split(",")]

        if os.getenv("DATABASE_URL"):
            config["database_url"] = os.getenv("DATABASE_URL")

        if os.getenv("ACTUAL_BUDGET_DATABASE_URL"):
            config["actual_budget"]["database_url"] = os.getenv("ACTUAL_BUDGET_DATABASE_URL")

        if os.getenv("ACTUAL_BUDGET_API_URL"):
            config["actual_budget"]["api_url"] = os.getenv("ACTUAL_BUDGET_API_URL")

        if os.getenv("ACTUAL_BUDGET_API_TOKEN"):
            config["actual_budget"]["api_token"] = os.getenv("ACTUAL_BUDGET_API_TOKEN")

        if os.getenv("ACTUAL_BUDGET_BUDGET_ID"):
            config["actual_budget"]["budget_id"] = os.getenv("ACTUAL_BUDGET_BUDGET_ID")

        if os.getenv("ACTUAL_BUDGET_ACCOUNT_ID"):
            config["actual_budget"]["account_id"] = os.getenv("ACTUAL_BUDGET_ACCOUNT_ID")

        if os.getenv("ACTUAL_BUDGET_ENCRYPTION_KEY"):
            config["actual_budget"]["encryption_key"] = os.getenv("ACTUAL_BUDGET_ENCRYPTION_KEY")

        if os.getenv("ACTUAL_BUDGET_PASSWORD"):
            config["actual_budget"]["password"] = os.getenv("ACTUAL_BUDGET_PASSWORD")

        # Cuentas de Actual Budget (múltiples)
        accounts = {}
        if os.getenv("ACTUAL_BUDGET_ACCOUNT_MERCADOPAGO"):
            accounts["MercadoPago"] = os.getenv("ACTUAL_BUDGET_ACCOUNT_MERCADOPAGO")
        if os.getenv("ACTUAL_BUDGET_ACCOUNT_CREDICOOP"):
            accounts["Credicoop"] = os.getenv("ACTUAL_BUDGET_ACCOUNT_CREDICOOP")
        if os.getenv("ACTUAL_BUDGET_ACCOUNT_EFECTIVO"):
            accounts["Efectivo"] = os.getenv("ACTUAL_BUDGET_ACCOUNT_EFECTIVO")

        if accounts:
            config["actual_budget"]["accounts"] = accounts

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

    @property
    def DATABASE_URL(self) -> Optional[str]:
        """Cadena de conexión a la base de datos del bot."""
        url = self._config.get("database_url")
        return url if url else None

    @property
    def ACTUAL_BUDGET_DATABASE_URL(self) -> str:
        """Cadena de conexión utilizada por Actual Budget (opcional)."""
        return self._config.get("actual_budget", {}).get("database_url")

    @property
    def ACTUAL_BUDGET_API_URL(self) -> str:
        """Endpoint base de la API de Actual Budget."""
        return self._config.get("actual_budget", {}).get("api_url")

    @property
    def ACTUAL_BUDGET_API_TOKEN(self) -> str:
        """Token de autenticación para la API de Actual Budget."""
        return self._config.get("actual_budget", {}).get("api_token")

    @property
    def ACTUAL_BUDGET_BUDGET_ID(self) -> str:
        """Identificador del presupuesto en Actual Budget."""
        return self._config.get("actual_budget", {}).get("budget_id")

    @property
    def ACTUAL_BUDGET_ACCOUNT_ID(self) -> str:
        """Identificador de la cuenta destino en Actual Budget."""
        return self._config.get("actual_budget", {}).get("account_id")

    @property
    def ACTUAL_BUDGET_ENCRYPTION_KEY(self) -> str:
        """Clave de cifrado para instancias auto-gestionadas de Actual Budget."""
        return self._config.get("actual_budget", {}).get("encryption_key")

    @property
    def ACTUAL_BUDGET_ACCOUNTS(self) -> dict:
        """Diccionario de cuentas disponibles {nombre: account_id}."""
        return self._config.get("actual_budget", {}).get("accounts", {})

    @property
    def ACTUAL_BUDGET_PASSWORD(self) -> Optional[str]:
        """Contraseña del servidor de Actual Budget."""
        return self._config.get("actual_budget", {}).get("password")

    def validate(self):
        """Valida que la configuración esté completa."""
        _ = self.TELEGRAM_BOT_TOKEN  # Lanza error si no está configurado


# Singleton
settings = Settings()
