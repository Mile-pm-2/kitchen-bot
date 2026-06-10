from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Shift, User
from app.schemas import ShiftOut, ShiftStatusOut

router = APIRouter(prefix="/api/shifts", tags=["shifts"])


@router.get("/status", response_model=ShiftStatusOut)
async def get_shift_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Shift)
        .where(Shift.user_id == user.id, Shift.closed_at.is_(None))
        .options(selectinload(Shift.user))
        .order_by(Shift.opened_at.desc())
        .limit(1)
    )
    shift = result.scalar_one_or_none()

    if shift:
        return ShiftStatusOut(
            is_open=True,
            current_shift=ShiftOut(
                id=shift.id,
                user_id=shift.user_id,
                user_name=shift.user.first_name,
                opened_at=shift.opened_at,
                closed_at=shift.closed_at,
            ),
        )
    return ShiftStatusOut(is_open=False)


@router.post("/open", response_model=ShiftOut)
async def open_shift(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Shift).where(Shift.user_id == user.id, Shift.closed_at.is_(None))
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Смена уже открыта")

    shift = Shift(user_id=user.id)
    db.add(shift)
    await db.flush()
    await db.refresh(shift)

    return ShiftOut(
        id=shift.id,
        user_id=shift.user_id,
        user_name=user.first_name,
        opened_at=shift.opened_at,
        closed_at=shift.closed_at,
    )


@router.post("/close", response_model=ShiftOut)
async def close_shift(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Shift).where(Shift.user_id == user.id, Shift.closed_at.is_(None))
    )
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=400, detail="Нет открытой смены")

    shift.closed_at = datetime.utcnow()
    await db.flush()

    return ShiftOut(
        id=shift.id,
        user_id=shift.user_id,
        user_name=user.first_name,
        opened_at=shift.opened_at,
        closed_at=shift.closed_at,
    )


@router.get("/history", response_model=list[ShiftOut])
async def shift_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(Shift)
        .where(Shift.user_id == user.id)
        .options(selectinload(Shift.user))
        .order_by(Shift.opened_at.desc())
        .limit(limit)
    )
    shifts = result.scalars().all()
    return [
        ShiftOut(
            id=s.id,
            user_id=s.user_id,
            user_name=s.user.first_name,
            opened_at=s.opened_at,
            closed_at=s.closed_at,
        )
        for s in shifts
    ]


@router.get("/all", response_model=list[ShiftOut])
async def all_shifts_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    """История всех смен (для шефов)."""
    from app.models import UserRole

    if user.role not in (UserRole.CHEF, UserRole.SOUS_CHEF, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Только для шефов")

    result = await db.execute(
        select(Shift)
        .options(selectinload(Shift.user))
        .order_by(Shift.opened_at.desc())
        .limit(limit)
    )
    shifts = result.scalars().all()
    return [
        ShiftOut(
            id=s.id,
            user_id=s.user_id,
            user_name=s.user.first_name,
            opened_at=s.opened_at,
            closed_at=s.closed_at,
        )
        for s in shifts
    ]
