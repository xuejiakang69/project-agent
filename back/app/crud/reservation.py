from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.schemas.reservation import ReservationCreateRequest, ReservationRequest
from app.models.user import User
from app.models.reservation import Reservation
from app.crud.lab import get_lab_by_id
from app.crud.equipment import get_equipment_by_id


def reservation_options():
    return (
        selectinload(Reservation.user),
        selectinload(Reservation.lab),
        selectinload(Reservation.equipment),
    )


def to_response(model: Reservation) -> ReservationRequest:
    return ReservationRequest(
        id=model.id,
        user_id=model.user_id,
        user_name=model.user.name if model.user else None,
        lab_id=model.lab_id,
        lab_name=model.lab.name if model.lab else None,
        equipment_id=model.equipment_id,
        equipment_name=model.equipment.name if model.equipment else None,
        date=model.date,
        start_time=model.start_time,
        end_time=model.end_time,
        remark=model.remarks,
        status=model.status,
        create_time=model.create_time,
        updated_time=model.updated_time,
    )


def parse_date(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as error:
        raise HTTPException(status_code=400, detail="预约日期格式错误") from error


def parse_time(value: str):
    for date_format in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, date_format).time()
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail="预约时间格式错误")


async def get_onw_reservation(reservation_id: int, db: AsyncSession):
    stmt = (
        select(Reservation)
        .where(Reservation.id == reservation_id)
        .options(*reservation_options())
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_reservation(
    data: ReservationCreateRequest,
    current_user: User,
    db: AsyncSession,
):
    """创建预约记录"""

    reservation_date = parse_date(data.date)
    start_time = parse_time(data.start_time)
    end_time = parse_time(data.end_time)

    now = datetime.now()
    if reservation_date < now.date():
        raise HTTPException(status_code=400, detail="预约日期不能早于当前日期")
    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="预约结束时间必须晚于开始时间")
    if reservation_date == now.date() and start_time < now.time().replace(second=0, microsecond=0):
        raise HTTPException(status_code=400, detail="预约开始时间不能早于当前时间")

    data.date = reservation_date.strftime("%Y-%m-%d")
    data.start_time = start_time.strftime("%H:%M")
    data.end_time = end_time.strftime("%H:%M")

    lab = await get_lab_by_id(data.lab_id, db)
    if not lab:
        raise HTTPException(status_code=404, detail="实验室不存在")
    if lab.status != 1:
        raise HTTPException(status_code=400, detail="实验室未开放预约")

    if lab.open_time and start_time < parse_time(lab.open_time):
        raise HTTPException(status_code=400, detail="预约时间不在实验室开放时间范围内")
    if lab.close_time and end_time > parse_time(lab.close_time):
        raise HTTPException(status_code=400, detail="预约时间不在实验室开放时间范围内")

    if data.equipment_id is not None:
        equipment = await get_equipment_by_id(data.equipment_id, db)
        if not equipment:
            raise HTTPException(status_code=404, detail="设备不存在")
        if equipment.lab_id != data.lab_id:
            raise HTTPException(status_code=400, detail="设备不属于该实验室")
        if equipment.status != 1:
            raise HTTPException(status_code=400, detail="设备不可预约")

    stmt = select(Reservation.id).where(
        Reservation.lab_id == data.lab_id,
        Reservation.date == data.date,
        Reservation.start_time < data.end_time,
        Reservation.end_time > data.start_time,
        Reservation.status.in_([0, 1]),
    )
    if data.equipment_id is not None:
        stmt = stmt.where(Reservation.equipment_id == data.equipment_id)
    else:
        stmt = stmt.where(Reservation.equipment_id.is_(None))

    result = await db.execute(stmt.limit(1))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="预约时间冲突")

    model = Reservation(
        user_id=current_user.id,
        lab_id=data.lab_id,
        equipment_id=data.equipment_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        remarks=data.remark,
        status=0,
    )
    db.add(model)
    await db.flush()

    model = await get_onw_reservation(model.id, db)
    return to_response(model)


async def get_reservations_by_user(
    current_user: User,
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    status: int | None = None,
    keyword: str | None = None,
):
    """获取预约列表，普通用户查看自己的预约，管理员查看全部预约"""

    stmt = select(Reservation).options(*reservation_options())
    count_stmt = select(func.count(Reservation.id))

    if current_user.role != "admin":
        stmt = stmt.where(Reservation.user_id == current_user.id)
        count_stmt = count_stmt.where(Reservation.user_id == current_user.id)

    if status is not None:
        stmt = stmt.where(Reservation.status == status)
        count_stmt = count_stmt.where(Reservation.status == status)

    if keyword:
        keyword_filter = or_(
            User.name.ilike(f"%{keyword}%"),
            User.username.ilike(f"%{keyword}%"),
            Reservation.remarks.ilike(f"%{keyword}%"),
        )
        stmt = stmt.outerjoin(Reservation.user).where(keyword_filter)
        count_stmt = count_stmt.outerjoin(Reservation.user).where(keyword_filter)

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.order_by(Reservation.date.desc(), Reservation.start_time.desc(), Reservation.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    reservations = result.scalars().all()
    return [to_response(item) for item in reservations], total


async def revoke_reservation(
    reservation_id: int,
    current_user: User,
    db: AsyncSession,
):
    """撤销预约"""

    reservation = await get_onw_reservation(reservation_id, db)
    if not reservation:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    if reservation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限撤销该预约")
    if reservation.status not in [0, 1]:
        raise HTTPException(status_code=409, detail="当前状态不能撤销")

    reservation.status = 3
    await db.flush()
    await db.refresh(reservation)
    return to_response(reservation)


async def audit_reservation(
    reservation_id: int,
    status: int,
    db: AsyncSession,
):
    """审核预约"""

    if status not in [1, 2]:
        raise HTTPException(status_code=400, detail="审核状态错误")

    reservation = await get_onw_reservation(reservation_id, db)
    if not reservation:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    if reservation.status != 0:
        raise HTTPException(status_code=409, detail="只能审核待审核的预约")

    reservation.status = status
    await db.flush()
    await db.refresh(reservation)
    return to_response(reservation)
