"""Punto de entrada principal del Bot de Gastos."""
import asyncio
from src.bot import GastosBot
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Función principal."""
    bot = GastosBot()
    asyncio.run(bot.start())


if __name__ == "__main__":
    main()
