"""
Middleware para manejo centralizado de errores.
"""
import aiohttp
from functools import wraps
from typing import Callable
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_telegram_errors():
    """Decorador para manejar errores en callbacks de Telegram."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)

            except aiohttp.ClientResponseError as e:
                logger.error(f"Error HTTP de API: {e}")
                raise

            except aiohttp.ClientError as e:
                logger.error(f"Error de conexión con API: {e}")
                raise

            except ValueError as e:
                logger.error(f"Error de validación: {e}")
                raise

            except Exception as e:
                logger.error(f"Error inesperado en {func.__name__}: {e}", exc_info=True)
                raise

        return wrapper
    return decorator
