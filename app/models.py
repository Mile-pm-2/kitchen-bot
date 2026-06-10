import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    COOK = "cook"
    SOUS_CHEF = "sous_chef"
    CHEF = "chef"
    ADMIN = "admin"


class ChecklistPeriod(str, enum.Enum):
    OPENING = "opening"
    CLOSING = "closing"


class ChecklistStatus(str, enum.Enum):
    TODO = "todo"
    DONE = "done"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.COOK)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shifts: Mapped[list["Shift"]] = relationship(back_populates="user")
    revision_entries: Mapped[list["RevisionEntry"]] = relationship(back_populates="user")


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    opened_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="shifts")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    unit: Mapped[str] = mapped_column(String(50), default="кг")
    min_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    current_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_revision_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    revision_entries: Mapped[list["RevisionEntry"]] = relationship(back_populates="ingredient")
    recipe_items: Mapped[list["RecipeIngredient"]] = relationship(back_populates="ingredient")


class RevisionEntry(Base):
    __tablename__ = "revision_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    quantity: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    ingredient: Mapped["Ingredient"] = relationship(back_populates="revision_entries")
    user: Mapped["User"] = relationship(back_populates="revision_entries")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"))
    quantity_at_trigger: Mapped[float] = mapped_column(Float)
    min_quantity: Mapped[float] = mapped_column(Float)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    ingredient: Mapped["Ingredient"] = relationship()


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period: Mapped[ChecklistPeriod] = mapped_column(Enum(ChecklistPeriod), index=True)
    title: Mapped[str] = mapped_column(String(240))
    status: Mapped[ChecklistStatus] = mapped_column(
        Enum(ChecklistStatus), default=ChecklistStatus.TODO, index=True
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    completed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    cancelled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_id])
    completed_by: Mapped["User | None"] = relationship(foreign_keys=[completed_by_id])
    cancelled_by: Mapped["User | None"] = relationship(foreign_keys=[cancelled_by_id])


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str] = mapped_column(Text)
    portion_weight: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    ingredient_id: Mapped[int | None] = mapped_column(
        ForeignKey("ingredients.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(50), default="г")

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
    ingredient: Mapped["Ingredient | None"] = relationship(back_populates="recipe_items")
