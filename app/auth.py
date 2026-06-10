import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User, UserRole


def validate_telegram_init_data(init_data: str) -> dict:
    """Проверка подписи Telegram Web App initData."""
    if not init_data:
        raise HTTPException(status_code=401, detail="Нет данных авторизации")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Неверные данные авторизации")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(
        b"WebAppData", settings.bot_token.encode(), hashlib.sha256
    ).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Неверная подпись")

    user_data = json.loads(parsed.get("user", "{}"))
    if not user_data.get("id"):
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return user_data


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if not init_data and settings.bot_token:
        init_data = request.query_params.get("initData", "")

    # Режим разработки без токена
    if not settings.bot_token:
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if user:
            return user
        user = User(
            telegram_id=0,
            first_name="Dev User",
            role=UserRole.ADMIN,
        )
        db.add(user)
        await db.flush()
        return user

    user_data = validate_telegram_init_data(init_data)
    telegram_id = user_data["id"]

    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        role = UserRole.COOK
        if telegram_id == settings.admin_telegram_id:
            role = UserRole.ADMIN

        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name", "Пользователь"),
            role=role,
        )
        db.add(user)
        await db.flush()
    else:
        user.username = user_data.get("username")
        user.first_name = user_data.get("first_name", user.first_name)

    return user


def require_role(*roles: UserRole):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role == UserRole.ADMIN:
            return user
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return user

    return checker
