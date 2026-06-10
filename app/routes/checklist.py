from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import ChecklistItem, ChecklistStatus, User
from app.schemas import ChecklistItemCreate, ChecklistItemOut

router = APIRouter(prefix="/api/checklist", tags=["checklist"])


def _item_out(item: ChecklistItem) -> ChecklistItemOut:
    return ChecklistItemOut(
        id=item.id,
        period=item.period,
        title=item.title,
        status=item.status,
        created_by_id=item.created_by_id,
        created_by_name=item.created_by.first_name,
        completed_by_name=item.completed_by.first_name if item.completed_by else None,
        cancelled_by_name=item.cancelled_by.first_name if item.cancelled_by else None,
        created_at=item.created_at,
        completed_at=item.completed_at,
        cancelled_at=item.cancelled_at,
    )


@router.get("", response_model=list[ChecklistItemOut])
async def list_checklist_items(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChecklistItem)
        .options(
            selectinload(ChecklistItem.created_by),
            selectinload(ChecklistItem.completed_by),
            selectinload(ChecklistItem.cancelled_by),
        )
        .order_by(ChecklistItem.created_at.desc())
    )
    return [_item_out(item) for item in result.scalars().all()]


@router.post("", response_model=ChecklistItemOut)
async def create_checklist_item(
    data: ChecklistItemCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    title = data.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Введите задачу")

    item = ChecklistItem(
        period=data.period,
        title=title,
        created_by_id=user.id,
    )
    db.add(item)
    await db.flush()
    item.created_by = user
    return _item_out(item)


@router.post("/{item_id}/done", response_model=ChecklistItemOut)
async def complete_checklist_item(
    item_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_item(db, item_id)
    item.status = ChecklistStatus.DONE
    item.completed_by_id = user.id
    item.completed_at = datetime.utcnow()
    item.cancelled_by_id = None
    item.cancelled_at = None
    await db.flush()
    item.completed_by = user
    item.cancelled_by = None
    return _item_out(item)


@router.post("/{item_id}/cancel", response_model=ChecklistItemOut)
async def cancel_checklist_item(
    item_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_item(db, item_id)
    item.status = ChecklistStatus.CANCELLED
    item.cancelled_by_id = user.id
    item.cancelled_at = datetime.utcnow()
    item.completed_by_id = None
    item.completed_at = None
    await db.flush()
    item.cancelled_by = user
    item.completed_by = None
    return _item_out(item)


async def _get_item(db: AsyncSession, item_id: int) -> ChecklistItem:
    result = await db.execute(
        select(ChecklistItem)
        .where(ChecklistItem.id == item_id)
        .options(
            selectinload(ChecklistItem.created_by),
            selectinload(ChecklistItem.completed_by),
            selectinload(ChecklistItem.cancelled_by),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return item
