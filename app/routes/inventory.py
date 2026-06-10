from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import Ingredient, OrderItem, RevisionEntry, User, UserRole
from app.schemas import (
    IngredientCreate,
    IngredientOut,
    IngredientUpdate,
    OrderItemCreate,
    OrderItemOut,
    RevisionUpdate,
)

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _ingredient_out(ing: Ingredient) -> IngredientOut:
    needs_order = (
        ing.current_quantity is not None
        and ing.min_quantity > 0
        and ing.current_quantity <= ing.min_quantity
    )
    return IngredientOut(
        id=ing.id,
        name=ing.name,
        unit=ing.unit,
        min_quantity=ing.min_quantity,
        current_quantity=ing.current_quantity,
        last_revision_at=ing.last_revision_at,
        needs_order=needs_order,
    )


def _order_item_out(item: OrderItem) -> OrderItemOut:
    return OrderItemOut(
        id=item.id,
        ingredient_id=item.ingredient_id,
        ingredient_name=item.ingredient.name,
        unit=item.ingredient.unit,
        quantity_at_trigger=item.quantity_at_trigger,
        min_quantity=item.min_quantity,
        created_at=item.created_at,
    )


async def _check_and_create_order(db: AsyncSession, ingredient: Ingredient):
    if (
        ingredient.current_quantity is not None
        and ingredient.min_quantity > 0
        and ingredient.current_quantity <= ingredient.min_quantity
    ):
        existing = await db.execute(
            select(OrderItem).where(
                OrderItem.ingredient_id == ingredient.id,
                OrderItem.is_resolved.is_(False),
            )
        )
        if not existing.scalar_one_or_none():
            order = OrderItem(
                ingredient_id=ingredient.id,
                quantity_at_trigger=ingredient.current_quantity,
                min_quantity=ingredient.min_quantity,
            )
            db.add(order)


@router.get("/ingredients", response_model=list[IngredientOut])
async def list_ingredients(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Ingredient).order_by(Ingredient.name))
    ingredients = result.scalars().all()
    return [_ingredient_out(i) for i in ingredients]


@router.post("/ingredients", response_model=IngredientOut)
async def create_ingredient(
    data: IngredientCreate,
    user: User = Depends(require_role(UserRole.CHEF)),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Ingredient).where(Ingredient.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ингредиент уже существует")

    ingredient = Ingredient(
        name=data.name,
        unit=data.unit,
        min_quantity=data.min_quantity,
    )
    db.add(ingredient)
    await db.flush()
    return _ingredient_out(ingredient)


@router.put("/ingredients/{ingredient_id}", response_model=IngredientOut)
async def update_ingredient(
    ingredient_id: int,
    data: IngredientUpdate,
    user: User = Depends(require_role(UserRole.CHEF)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Ingredient).where(Ingredient.id == ingredient_id))
    ingredient = result.scalar_one_or_none()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ингредиент не найден")

    if data.name is not None:
        ingredient.name = data.name
    if data.unit is not None:
        ingredient.unit = data.unit
    if data.min_quantity is not None:
        ingredient.min_quantity = data.min_quantity

    await _check_and_create_order(db, ingredient)
    await db.flush()
    return _ingredient_out(ingredient)


@router.delete("/ingredients/{ingredient_id}")
async def delete_ingredient(
    ingredient_id: int,
    user: User = Depends(require_role(UserRole.CHEF)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Ingredient).where(Ingredient.id == ingredient_id))
    ingredient = result.scalar_one_or_none()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ингредиент не найден")

    await db.delete(ingredient)
    return {"ok": True}


@router.post("/ingredients/{ingredient_id}/revision", response_model=IngredientOut)
async def update_revision(
    ingredient_id: int,
    data: RevisionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Ingredient).where(Ingredient.id == ingredient_id))
    ingredient = result.scalar_one_or_none()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ингредиент не найден")

    ingredient.current_quantity = data.quantity
    ingredient.last_revision_at = datetime.utcnow()

    entry = RevisionEntry(
        ingredient_id=ingredient.id,
        user_id=user.id,
        quantity=data.quantity,
    )
    db.add(entry)

    await _check_and_create_order(db, ingredient)
    await db.flush()
    return _ingredient_out(ingredient)


@router.get("/orders", response_model=list[OrderItemOut])
async def list_orders(
    user: User = Depends(require_role(UserRole.CHEF)),
    db: AsyncSession = Depends(get_db),
    resolved: bool = False,
):
    result = await db.execute(
        select(OrderItem)
        .where(OrderItem.is_resolved == resolved)
        .options(selectinload(OrderItem.ingredient))
        .order_by(OrderItem.created_at.desc())
    )
    items = result.scalars().all()
    return [_order_item_out(item) for item in items]


@router.post("/orders", response_model=OrderItemOut)
async def create_order_item(
    data: OrderItemCreate,
    user: User = Depends(require_role(UserRole.CHEF)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Ingredient).where(Ingredient.id == data.ingredient_id)
    )
    ingredient = result.scalar_one_or_none()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ингредиент не найден")

    existing = await db.execute(
        select(OrderItem)
        .where(
            OrderItem.ingredient_id == ingredient.id,
            OrderItem.is_resolved.is_(False),
        )
        .options(selectinload(OrderItem.ingredient))
    )
    item = existing.scalar_one_or_none()
    if item:
        return _order_item_out(item)

    item = OrderItem(
        ingredient_id=ingredient.id,
        quantity_at_trigger=ingredient.current_quantity
        if ingredient.current_quantity is not None
        else 0,
        min_quantity=ingredient.min_quantity,
    )
    db.add(item)
    await db.flush()
    item.ingredient = ingredient
    return _order_item_out(item)


@router.post("/orders/{order_id}/resolve")
async def resolve_order(
    order_id: int,
    user: User = Depends(require_role(UserRole.CHEF)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OrderItem).where(OrderItem.id == order_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    item.is_resolved = True
    item.resolved_at = datetime.utcnow()
    return {"ok": True}
