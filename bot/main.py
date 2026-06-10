import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import settings
from app.database import init_db
from bot.handlers import register_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    if not settings.bot_token:
        logger.error("BOT_TOKEN не задан в .env файле!")
        return

    await init_db()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    register_handlers(dp)

    logger.info("Бот запущен (режим polling)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
