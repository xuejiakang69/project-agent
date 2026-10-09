from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.reservation import (
    audit_reservation,
    create_reservation,
    get_reservations_by_user,
    revoke_reservation,
)
from app.schemas.reservation import (
    ReservationCreateRequest,
    ReservationPageResult,
    ReservationRequest,
)
from app.database import get_db
from app.utils.auth import get_current_user, get_user_by_main
from app.models.user import User
from app.schemas.common import Result


router = APIRouter(prefix="/api/reservations", tags=["预约"])


@router.post("/create")
async def create_post(
    data: ReservationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Result[ReservationRequest]:
    """创建预约"""
    reservation = await create_reservation(data, current_user, db)
    return Result[ReservationRequest](result=reservation)


@router.get("/list")
async def list_reservations(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: int | None = Query(None, ge=0, le=3),
    keyword: str | None = Query(None, max_length=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Result[ReservationPageResult]:
    """获取预约列表"""
    items, total = await get_reservations_by_user(
        current_user,
        db,
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword,
    )
    return Result[ReservationPageResult](
        result=ReservationPageResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )
    )


@router.post("/revoke/{reservation_id}")
async def revoke_post(
    reservation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Result[ReservationRequest]:
    """撤销预约"""
    reservation = await revoke_reservation(reservation_id, current_user, db)
    return Result[ReservationRequest](result=reservation)


@router.post("/audit/{reservation_id}/{status}")
async def audit_post(
    reservation_id: int,
    status: int,
    current_admin: User = Depends(get_user_by_main),
    db: AsyncSession = Depends(get_db),
) -> Result[ReservationRequest]:
    """审核预约"""
    reservation = await audit_reservation(reservation_id, status, db)
    return Result[ReservationRequest](result=reservation)
