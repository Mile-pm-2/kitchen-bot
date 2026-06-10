from datetime import datetime

from pydantic import BaseModel, Field

from app.models import UserRole


class UserOut(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str
    role: UserRole

    model_config = {"from_attributes": True}


class ShiftOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    opened_at: datetime
    closed_at: datetime | None

    model_config = {"from_attributes": True}


class ShiftStatusOut(BaseModel):
    is_open: bool
    current_shift: ShiftOut | None = None


class IngredientOut(BaseModel):
    id: int
    name: str
    unit: str
    min_quantity: float
    current_quantity: float | None
    last_revision_at: datetime | None
    needs_order: bool = False

    model_config = {"from_attributes": True}


class IngredientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    unit: str = Field(default="кг", max_length=50)
    min_quantity: float = Field(default=0.0, ge=0)


class IngredientUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    unit: str | None = Field(None, max_length=50)
    min_quantity: float | None = Field(None, ge=0)


class RevisionUpdate(BaseModel):
    quantity: float = Field(..., ge=0)


class OrderItemOut(BaseModel):
    id: int
    ingredient_id: int
    ingredient_name: str
    unit: str
    quantity_at_trigger: float
    min_quantity: float
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderItemCreate(BaseModel):
    ingredient_id: int


class RecipeIngredientOut(BaseModel):
    id: int
    name: str
    quantity: str
    unit: str
    ingredient_id: int | None

    model_config = {"from_attributes": True}


class RecipeOut(BaseModel):
    id: int
    name: str
    description: str | None
    instructions: str
    portion_weight: str | None
    ingredients: list[RecipeIngredientOut]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecipeIngredientCreate(BaseModel):
    name: str = Field(..., min_length=1)
    quantity: str = Field(..., min_length=1)
    unit: str = Field(default="г", max_length=50)
    ingredient_id: int | None = None


class RecipeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    instructions: str = Field(..., min_length=1)
    portion_weight: str | None = None
    ingredients: list[RecipeIngredientCreate] = []


class RecipeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    instructions: str | None = Field(None, min_length=1)
    portion_weight: str | None = None
    ingredients: list[RecipeIngredientCreate] | None = None


class UserRoleUpdate(BaseModel):
    role: UserRole
