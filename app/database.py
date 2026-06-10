from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _prepare_database_url(database_url: str) -> tuple[str, dict]:
    """Adapt provider URLs for SQLAlchemy async drivers without storing secrets."""
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if not database_url.startswith("postgresql+asyncpg://"):
        return database_url, {}

    parts = urlsplit(database_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    ssl_required = query.pop("sslmode", "") in {"require", "verify-ca", "verify-full"}
    query.pop("channel_binding", None)

    clean_url = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )
    connect_args = {"ssl": True} if ssl_required else {}
    return clean_url, connect_args


database_url, connect_args = _prepare_database_url(settings.database_url)
engine = create_async_engine(database_url, echo=False, connect_args=connect_args)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
