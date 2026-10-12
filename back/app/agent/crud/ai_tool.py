from datetime import datetime, time

from langchain_core.tools import tool

from app.database import async_session_factory
from app.crud.equipment import get_equipments_paginated
from app.crud.lab import get_labs_paginated
from app.crud.reservation import get_equipment_ids_busy_at_time
from app.models.lab import Lab


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None

    fmt = "%H:%M:%S" if value.count(":") == 2 else "%H:%M"
    try:
        return datetime.strptime(value.strip(), fmt).time()
    except ValueError:
        return None


def _is_open(lab: Lab | None, now: time) -> bool:
    if lab is None or lab.status != 1:
        return False

    start = _parse_time(lab.open_time)
    end = _parse_time(lab.close_time)
    if start is None or end is None:
        return False

    if start <= end:
        return start <= now <= end

    # 开放时间跨午夜，例如 22:00 到次日 02:00。
    return now >= start or now <= end


@tool("get_open_labs")
async def get_open_labs(keyword: str | None = None) -> dict:
    """查询当前开放的实验室。keyword 可按实验室名称筛选。"""
    now = datetime.now()

    async with async_session_factory() as db:
        labs, _ = await get_labs_paginated(
            db,
            page=1,
            page_size=100,
            keyword=keyword,
            status=1,
        )

    return {
        "labs": [
            {
                "id": lab.id,
                "name": lab.name,
                "location": lab.location,
                "open_time": lab.open_time,
                "close_time": lab.close_time,
            }
            for lab in labs
            if _is_open(lab, now.time())
        ]
    }


@tool("get_available_equipment")
async def get_available_equipment(
    keyword: str | None = None,
    lab_id: int | None = None,
) -> dict:
    """查询当前可用设备。可按关键词或实验室编号筛选。"""
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    at_time = now.strftime("%H:%M:%S")

    async with async_session_factory() as db:
        rows, _ = await get_equipments_paginated(
            db,
            page=1,
            page_size=100,
            keyword=keyword,
            lab_id=lab_id,
            status=1,
        )
        busy_ids = await get_equipment_ids_busy_at_time(
            db,
            date=date,
            at_time=at_time,
        )

    return {
        "equipment": [
            {
                "id": equipment.id,
                "name": equipment.name,
                "spec": equipment.spec,
                "quantity": equipment.quantity,
                "lab_id": equipment.lab_id,
                "lab_name": lab_name,
            }
            for equipment, lab_name in rows
            if equipment.quantity > 0
            and equipment.id not in busy_ids
            and _is_open(equipment.lab, now.time())
        ]
    }