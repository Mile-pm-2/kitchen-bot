from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.config import settings


def get_webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🍳 Открыть кухню",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            ]
        ]
    )


async def cmd_start(message: Message):
    role_hint = ""
    if message.from_user and message.from_user.id == settings.admin_telegram_id:
        role_hint = (
            "\n\n👑 Вы — главный администратор.\n"
            "После открытия приложения зайдите во вкладку «Роли» "
            "и назначьте роли сотрудникам."
        )

    await message.answer(
        "👋 Добро пожаловать в систему управления кухней!\n\n"
        "Нажмите кнопку ниже, чтобы открыть приложение.\n\n"
        "📌 <b>Как добавить сотрудника:</b>\n"
        "1. Отправьте ему ссылку на этого бота\n"
        "2. Он нажимает /start и «Открыть кухню»\n"
        "3. Вы (админ) в приложении → вкладка «Роли» → выбираете роль\n\n"
        "Роли:\n"
        "• <b>Повар</b> — смена, ревизия, просмотр ТТК\n"
        "• <b>Су-шеф/Шеф</b> — всё + ингредиенты, ТТК, заказы"
        f"{role_hint}",
        reply_markup=get_webapp_keyboard(),
        parse_mode="HTML",
    )


async def cmd_app(message: Message):
    await message.answer(
        "Откройте приложение кухни:",
        reply_markup=get_webapp_keyboard(),
    )


async def cmd_myid(message: Message):
    user = message.from_user
    if not user:
        return
    await message.answer(
        f"🆔 Ваш Telegram ID: <code>{user.id}</code>\n\n"
        "Этот ID нужен для настройки ADMIN_TELEGRAM_ID в .env "
        "(только для главного администратора).",
        parse_mode="HTML",
    )


async def cmd_help(message: Message):
    await message.answer(
        "<b>Команды:</b>\n"
        "/start — приветствие и кнопка приложения\n"
        "/app — открыть приложение\n"
        "/myid — узнать свой Telegram ID\n"
        "/help — эта справка\n\n"
        "<b>Добавление сотрудников</b> (для админа):\n"
        "Просто отправьте коллеге ссылку на бота. "
        "Когда он откроет приложение, он появится во вкладке «Роли».",
        parse_mode="HTML",
    )


def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_app, Command("app"))
    dp.message.register(cmd_myid, Command("myid"))
    dp.message.register(cmd_help, Command("help"))
