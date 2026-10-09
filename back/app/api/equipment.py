from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.equipment import (
    add_equipment,
    delete_equipment,
    get_equipment_by_id,
    get_equipment_with_lab_by_id,
    get_equipments_paginated,
    update_equipment,
)
from app.crud.lab import get_lab_by_id
from app.database import get_db
from app.schemas.common import Result
from app.schemas.equipment import (
    EquipmentCreateRequest,
    EquipmentPageResult,
    EquipmentRequest,
    EquipmentUpdateRequest,
)
from app.utils.auth import get_current_user, get_user_by_main

router = APIRouter(prefix="/api/equipment", tags=["设备管理"])


def build_equipment_response(
    equipment,
    lab_name: str | None = None,
) -> EquipmentRequest:
    response = EquipmentRequest.model_validate(equipment)
    return response.model_copy(update={"lab_name": lab_name})


# 创建实验室设备
@router.post("/create")
async def create_equipment(
    data: EquipmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user_by_main),
) -> Result[EquipmentRequest]:
    lab = await get_lab_by_id(data.lab_id, db)
    if not lab:
        raise HTTPException(status_code=404, detail="所属实验室不存在")

    try:
        equipment = await add_equipment(data, db)
    except IntegrityError as error:
        raise HTTPException(status_code=409, detail="设备关联数据冲突") from error

    return Result[EquipmentRequest](
        result=build_equipment_response(equipment, lab.name)
    )


# 修改实验室设备
@router.post("/update/{id}")
async def update_equipment_api(
    id: int,
    data: EquipmentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user_by_main),
) -> Result[EquipmentRequest]:
    equipment = await get_equipment_by_id(id, db)
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")

    if data.lab_id is not None:
        lab = await get_lab_by_id(data.lab_id, db)
        if not lab:
            raise HTTPException(status_code=404, detail="所属实验室不存在")

    try:
        await update_equipment(equipment, data, db)
    except IntegrityError as error:
        raise HTTPException(status_code=409, detail="设备关联数据冲突") from error

    item = await get_equipment_with_lab_by_id(id, db)
    if not item:
        raise HTTPException(status_code=404, detail="设备不存在")

    updated_equipment, lab_name = item
    return Result[EquipmentRequest](
        result=build_equipment_response(updated_equipment, lab_name)
    )


# 删除实验室设备
@router.post("/delete/{id}")
async def delete_equipment_api(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user_by_main),
) -> Result[bool]:
    equipment = await get_equipment_by_id(id, db)
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")

    await delete_equipment(equipment, db)
    return Result[bool](result=True)


# 查询实验室设备列表，所有登录用户可查看
@router.get("/list")
async def list_equipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None, max_length=100),
    lab_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Result[EquipmentPageResult]:
    equipments, total = await get_equipments_paginated(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        lab_id=lab_id,
    )

    return Result[EquipmentPageResult](
        result=EquipmentPageResult(
            items=[
                build_equipment_response(equipment, lab_name)
                for equipment, lab_name in equipments
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )
    )