from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import Recipe, RecipeIngredient, User, UserRole
from app.schemas import RecipeCreate, RecipeIngredientOut, RecipeOut, RecipeUpdate

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


def _recipe_out(recipe: Recipe) -> RecipeOut:
    return RecipeOut(
        id=recipe.id,
        name=recipe.name,
        description=recipe.description,
        instructions=recipe.instructions,
        portion_weight=recipe.portion_weight,
        ingredients=[
            RecipeIngredientOut(
                id=ri.id,
                name=ri.name,
                quantity=ri.quantity,
                unit=ri.unit,
                ingredient_id=ri.ingredient_id,
            )
            for ri in recipe.ingredients
        ],
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
    )


@router.get("", response_model=list[RecipeOut])
async def list_recipes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recipe).options(selectinload(Recipe.ingredients)).order_by(Recipe.name)
    )
    recipes = result.scalars().all()
    return [_recipe_out(r) for r in recipes]


@router.get("/{recipe_id}", response_model=RecipeOut)
async def get_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(selectinload(Recipe.ingredients))
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    return _recipe_out(recipe)


@router.post("", response_model=RecipeOut)
async def create_recipe(
    data: RecipeCreate,
    user: User = Depends(require_role(UserRole.CHEF)),
    db: AsyncSession = Depends(get_db),
):
    recipe = Recipe(
        name=data.name,
        description=data.description,
        instructions=data.instructions,
        portion_weight=data.portion_weight,
    )
    db.add(recipe)
    await db.flush()

    for ing in data.ingredients:
        ri = RecipeIngredient(
            recipe_id=recipe.id,
            name=ing.name,
            quantity=ing.quantity,
            unit=ing.unit,
            ingredient_id=ing.ingredient_id,
        )
        db.add(ri)

    await db.flush()
    await db.refresh(recipe, ["ingredients"])
    return _recipe_out(recipe)


@router.put("/{recipe_id}", response_model=RecipeOut)
async def update_recipe(
    recipe_id: int,
    data: RecipeUpdate,
    user: User = Depends(require_role(UserRole.CHEF)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(selectinload(Recipe.ingredients))
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    if data.name is not None:
        recipe.name = data.name
    if data.description is not None:
        recipe.description = data.description
    if data.instructions is not None:
        recipe.instructions = data.instructions
    if data.portion_weight is not None:
        recipe.portion_weight = data.portion_weight

    if data.ingredients is not None:
        for ri in recipe.ingredients:
            await db.delete(ri)
        await db.flush()

        for ing in data.ingredients:
            ri = RecipeIngredient(
                recipe_id=recipe.id,
                name=ing.name,
                quantity=ing.quantity,
                unit=ing.unit,
                ingredient_id=ing.ingredient_id,
            )
            db.add(ri)

    await db.flush()
    await db.refresh(recipe, ["ingredients"])
    return _recipe_out(recipe)


@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: int,
    user: User = Depends(require_role(UserRole.CHEF)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    await db.delete(recipe)
    return {"ok": True}
