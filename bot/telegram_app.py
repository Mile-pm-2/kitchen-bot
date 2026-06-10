import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Request

from app.config import settings
from bot.handlers import register_handlers

logger = logging.getLogger(__name__)

bot: Bot | None = None
dp: Dispatcher | None = None
webhook_router = APIRouter()


def get_bot_and_dp() -> tuple[Bot, Dispatcher]:
    global bot, dp
    if bot is None or dp is None:
        bot = Bot(token=settings.bot_token)
        dp = Dispatcher()
        register_handlers(dp)
    return bot, dp


@webhook_router.post("/webhook")
async def telegram_webhook(request: Request):
    bot_instance, dp_instance = get_bot_and_dp()
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot_instance})
    await dp_instance.feed_update(bot_instance, update)
    return {"ok": True}


async def setup_webhook():
    if not settings.bot_token:
        logger.warning("BOT_TOKEN не задан — бот не запущен")
        return

    bot_instance, _ = get_bot_and_dp()
    webhook_url = f"{settings.webapp_url.rstrip('/')}/webhook"
    await bot_instance.set_webhook(webhook_url, drop_pending_updates=True)
    logger.info("Webhook установлен: %s", webhook_url)


async def remove_webhook():
    if bot:
        await bot.delete_webhook()
        await bot.session.close()
