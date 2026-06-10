from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routes import checklist, inventory, recipes, shifts, users
from bot.telegram_app import setup_webhook, webhook_router

WEB_DIR = Path(__file__).parent.parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if settings.webhook_mode and settings.bot_token:
        await setup_webhook()
    yield


app = FastAPI(title="Kitchen Bot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(shifts.router)
app.include_router(checklist.router)
app.include_router(inventory.router)
app.include_router(recipes.router)
app.include_router(users.router)
app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
