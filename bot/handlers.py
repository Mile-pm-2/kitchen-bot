from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models import User, UserRole


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


async def ensure_user_from_message(message: Message) -> User | None:
    user_data = message.from_user
    if not user_data:
        return None

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_data.id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.username = user_data.username
            user.first_name = user_data.first_name or "Пользователь"
        else:
            role = (
                UserRole.ADMIN
                if user_data.id == settings.admin_telegram_id
                else UserRole.COOK
            )
            user = User(
                telegram_id=user_data.id,
                username=user_data.username,
                first_name=user_data.first_name or "Пользователь",
                role=role,
            )
            session.add(user)

        await session.commit()
        return user


async def cmd_start(message: Message):
    user = await ensure_user_from_message(message)
    is_admin = user and user.role == UserRole.ADMIN

    if is_admin:
        text = (
            "Добро пожаловать в систему управления кухней.\n\n"
            "Вы — главный администратор.\n"
            "После открытия приложения зайдите во вкладку «Роли» "
            "и назначьте роли сотрудникам.\n\n"
            "<b>Как добавить сотрудника:</b>\n"
            "1. Отправьте коллеге ссылку на этого бота\n"
            "2. Он нажимает /start и «Открыть кухню»\n"
            "3. В приложении откройте вкладку «Роли» и выберите ему роль\n\n"
            "Роли:\n"
            "• <b>Повар</b> — ревизия, просмотр ТТК, просмотр ролей\n"
            "• <b>Су-шеф</b> — ингредиенты, ТТК, заказы, назначение до су-шефа\n"
            "• <b>Шеф</b> — всё + назначение поваров, су-шефов и шефов"
        )
    else:
        text = (
            "Добро пожаловать в систему управления кухней.\n\n"
            "Нажмите кнопку ниже, чтобы открыть приложение. "
            "Если нужные разделы недоступны, попросите администратора назначить вам роль."
        )

    await message.answer(
        text,
        reply_markup=get_webapp_keyboard(),
        parse_mode="HTML",
    )


async def cmd_app(message: Message):
    await ensure_user_from_message(message)
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
    user = await ensure_user_from_message(message)
    if user and user.role == UserRole.ADMIN:
        text = (
            "<b>Команды:</b>\n"
            "/start — приветствие и кнопка приложения\n"
            "/app — открыть приложение\n"
            "/myid — узнать свой Telegram ID\n"
            "/help — эта справка\n\n"
            "<b>Добавление сотрудников</b>:\n"
            "Отправьте коллеге ссылку на бота. "
            "Когда он нажмёт /start, он появится во вкладке «Роли»."
        )
    else:
        text = (
            "<b>Команды:</b>\n"
            "/start — приветствие и кнопка приложения\n"
            "/app — открыть приложение\n"
            "/myid — узнать свой Telegram ID\n"
            "/help — эта справка\n\n"
            "Если вам нужен доступ к разделам приложения, обратитесь к администратору."
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )


def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_app, Command("app"))
    dp.message.register(cmd_myid, Command("myid"))
    dp.message.register(cmd_help, Command("help"))
