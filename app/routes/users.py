from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserOut, UserRoleUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


ROLE_ASSIGNMENTS = {
    UserRole.COOK: set(),
    UserRole.SOUS_CHEF: {UserRole.COOK, UserRole.SOUS_CHEF},
    UserRole.CHEF: {UserRole.COOK, UserRole.SOUS_CHEF, UserRole.CHEF},
    UserRole.ADMIN: {UserRole.COOK, UserRole.SOUS_CHEF, UserRole.CHEF, UserRole.ADMIN},
}


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.get("", response_model=list[UserOut])
async def list_users(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.first_name))
    return result.scalars().all()


@router.put("/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if target.id == current_user.id:
        raise HTTPException(status_code=403, detail="Нельзя менять собственную роль")

    allowed_roles = ROLE_ASSIGNMENTS[current_user.role]
    if data.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Недостаточно прав для назначения роли")

    if target.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Недостаточно прав для изменения админа")

    target.role = data.role
    await db.flush()
    return target
