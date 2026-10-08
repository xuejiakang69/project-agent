from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.lab import (
    add_lab,
    delete_lab,
    get_lab_by_id,
    get_lab_by_name,
    get_labs_paginated,
    update_lab,
)
from app.database import get_db
from app.schemas.common import Result
from app.schemas.lab import (
    LabCreateRequest,
    LabPageResult,
    LabRequest,
    LabUpdateRequest,
)
from app.utils.auth import get_current_user, get_user_by_main

router = APIRouter(prefix="/api/lab", tags=["实验室管理"])


# 创建实验室
@router.post("/create")
async def create_laboratory(
    data: LabCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user_by_main),
) -> Result[LabRequest]:
    try:
        lab = await add_lab(data, db)
    except IntegrityError as error:
        raise HTTPException(status_code=409, detail="实验室名称已存在") from error

    if not lab:
        raise HTTPException(status_code=409, detail="实验室名称已存在")

    return Result[LabRequest](
        result=LabRequest.model_validate(lab)
    )


#修改实验室
@router.post("/update/{id}")
async def update_laboratory(
    id: int,
    data: LabUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user_by_main),
) -> Result[LabRequest]:
    lab = await get_lab_by_id(id, db)
    if not lab:
        raise HTTPException(status_code=404, detail="实验室不存在")

    if data.name is not None:
        existing = await get_lab_by_name(data.name, db)
        if existing and existing.id != id:
            raise HTTPException(status_code=409, detail="实验室名称已存在")

    try:
        updated_lab = await update_lab(lab, data, db)
    except IntegrityError as error:
        raise HTTPException(status_code=409, detail="实验室名称已存在") from error

    return Result[LabRequest](
        result=LabRequest.model_validate(updated_lab)
    )


#删除实验室
@router.post("/delete/{id}")
async def delete_laboratory(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user_by_main),
) -> Result[bool]:
    lab = await get_lab_by_id(id, db)
    if not lab:
        raise HTTPException(status_code=404, detail="实验室不存在")

    await delete_lab(lab, db)

    return Result[bool](
        result=True
    )


#查询实验室列表，所有登录用户可查看
@router.get("/list")
async def list_laboratories(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None, max_length=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Result[LabPageResult]:
    labs, total = await get_labs_paginated(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
    )

    return Result[LabPageResult](
        result=LabPageResult(
            items=[LabRequest.model_validate(lab) for lab in labs],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )
    )