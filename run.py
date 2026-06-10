import asyncio
import logging
import sys

import uvicorn

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_bot():
    from bot.main import main as bot_main
    await bot_main()


def run_api():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=False,
    )


async def run_all():
    import threading

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.info(f"API сервер запущен на порту {settings.api_port}")
    await run_bot()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "api":
        run_api()
    elif mode == "bot":
        asyncio.run(run_bot())
    else:
        asyncio.run(run_all())
