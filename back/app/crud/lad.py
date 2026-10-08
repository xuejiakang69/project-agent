from  sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lad import Lad




#根据名称查找实验室
async def get_lab_by_name(name:str,db:AsyncSession):
    lad = select(Lad).where(Lad.name==name)
    result =await db.execute(lad)
    return result.scalar_one_or_none()


#添加实验室
async def add_lab(data,db:AsyncSession):
    exi = await get_lab_by_name(data.name,db)
    if exi:
         return None
    lad = Lad(
        name=data.name,
        description=data.description,
        address=data.address,
        phone=data.phone
    )
    db.add(lad)
    await db.flush()
    await db.refresh(lad)
    return lad

#修改实验室
async def update_lab(lab:Lad,data,db:AsyncSession):
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(lab, field, value)

    await db.flush()
    await db.refresh(lab)
    return lab

#删除实验室
async def delete_lab(lab:Lad,db:AsyncSession):
    await db.delete(lab)
    await db.flush()
    return True

#查询所有实验室
async def get_labs_paginated(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    keyword: str | None,
) -> tuple[list[Lad], int]:
    query = select(Lad)
    if keyword:
        query = query.where(Lad.name.ilike(f"%{keyword}%"))
    total_result = await db.execute(query)
    total_count = total_result.scalars().count()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    labs = result.scalars().all()
    return labs, total_count