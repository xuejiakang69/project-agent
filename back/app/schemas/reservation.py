from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ReservationCreateRequest(BaseModel):
    lab_id: int = Field(ge=1)
    equipment_id: int | None = Field(default=None, ge=1)
    date: str = Field(min_length=8, max_length=20)
    start_time: str = Field(min_length=5, max_length=20)
    end_time: str = Field(min_length=5, max_length=20)
    remark: str | None = Field(default=None, max_length=255)


class ReservationRequest(BaseModel):
    id: int
    user_id: int
    user_name: str | None = None
    lab_id: int
    lab_name: str | None = None
    equipment_id: int | None = None
    equipment_name: str | None = None
    date: str
    start_time: str
    end_time: str
    remark: str | None = None
    status: int
    create_time: datetime
    updated_time: datetime

    model_config = ConfigDict(from_attributes=True)


class ReservationPageResult(BaseModel):
    items: list[ReservationRequest]
    total: int
    page: int
    page_size: int
    total_pages: int
