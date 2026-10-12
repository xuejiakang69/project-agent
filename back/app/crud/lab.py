from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab


#根据名称查找实验室
async def get_lab_by_name(name: str, db: AsyncSession) -> Lab | None:
    result = await db.execute(select(Lab).where(Lab.name == name))
    return result.scalar_one_or_none()


#根据id查找实验室
async def get_lab_by_id(id: int, db: AsyncSession) -> Lab | None:
    result = await db.execute(select(Lab).where(Lab.id == id))
    return result.scalar_one_or_none()


#添加实验室
async def add_lab(data, db: AsyncSession) -> Lab | None:
    existing = await get_lab_by_name(data.name, db)
    if existing:
        return None

    lab = Lab(
        name=data.name,
        description=data.description,
        img=data.img,
        status=data.status,
        location=data.location,
        open_time=data.open_time,
        close_time=data.close_time,
        capacity=data.capacity,
    )
    db.add(lab)
    await db.flush()
    await db.refresh(lab)
    return lab


#修改实验室
async def update_lab(lab: Lab, data, db: AsyncSession) -> Lab:
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(lab, field, value)

    await db.flush()
    await db.refresh(lab)
    return lab


#删除实验室
async def delete_lab(lab: Lab, db: AsyncSession) -> bool:
    await db.delete(lab)
    await db.flush()
    return True


#分页查询实验室
async def get_labs_paginated(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    keyword: str | None,
    status: int | None = None,
) -> tuple[list[Lab], int]:
    stmt = select(Lab)
    count_stmt = select(func.count(Lab.id))
    normalized_keyword = (keyword or "").strip()

    if status is not None:
        stmt = stmt.where(Lab.status == status)
        count_stmt = count_stmt.where(Lab.status == status)

    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        keyword_filter = Lab.name.ilike(pattern)
        stmt = stmt.where(keyword_filter)
        count_stmt = count_stmt.where(keyword_filter)

    total = await db.scalar(count_stmt) or 0
    result = await db.execute(
        stmt.order_by(Lab.create_time.desc(), Lab.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return list(result.scalars().all()), total
