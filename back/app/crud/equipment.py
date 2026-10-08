from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.equipment import Equipment
from app.models.lab import Lab


# 根据 id 查询设备
async def get_equipment_by_id(
    equipment_id: int,
    db: AsyncSession,
) -> Equipment | None:
    result = await db.execute(
        select(Equipment).where(Equipment.id == equipment_id)
    )
    return result.scalar_one_or_none()


# 根据 id 查询设备和所属实验室名称
async def get_equipment_with_lab_by_id(
    equipment_id: int,
    db: AsyncSession,
) -> tuple[Equipment, str | None] | None:
    result = await db.execute(
        select(Equipment, Lab.name)
        .outerjoin(Lab, Equipment.lab_id == Lab.id)
        .where(Equipment.id == equipment_id)
    )
    return result.one_or_none()


# 添加设备
async def add_equipment(data, db: AsyncSession) -> Equipment | None:
    equipment = Equipment(
        lab_id=data.lab_id,
        name=data.name,
        description=data.description,
        img=data.img,
        spec=data.spec,
        quantity=data.quantity,
        status=data.status,
    )
    db.add(equipment)
    await db.flush()
    await db.refresh(equipment)
    return equipment


# 修改设备
async def update_equipment(
    equipment: Equipment,
    data,
    db: AsyncSession,
) -> Equipment:
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(equipment, field, value)

    await db.flush()
    await db.refresh(equipment)
    return equipment


# 删除设备
async def delete_equipment(
    equipment: Equipment,
    db: AsyncSession,
) -> bool:
    await db.delete(equipment)
    await db.flush()
    return True


# 分页查询设备
async def get_equipments_paginated(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    keyword: str | None,
) -> tuple[list[tuple[Equipment, str | None]], int]:
    normalized_keyword = (keyword or "").strip()

    stmt = select(Equipment, Lab.name).outerjoin(Lab, Equipment.lab_id == Lab.id)
    count_stmt = select(func.count(Equipment.id)).outerjoin(
        Lab,
        Equipment.lab_id == Lab.id,
    )

    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        conditions = or_(
            Equipment.name.ilike(pattern),
            Equipment.description.ilike(pattern),
            Equipment.spec.ilike(pattern),
            Lab.name.ilike(pattern),
        )
        stmt = stmt.where(conditions)
        count_stmt = count_stmt.where(conditions)

    total = await db.scalar(count_stmt) or 0
    result = await db.execute(
        stmt.order_by(Equipment.updated_time.desc(), Equipment.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return list(result.all()), total