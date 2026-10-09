from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LabStatus = Literal[0, 1]


#实验室的信息
class LabRequest(BaseModel):
    id: int
    name: str
    description: str | None = Field(default=None, max_length=255)
    img: str | None = Field(default=None, max_length=200)
    status: LabStatus
    location: str | None = Field(default=None, max_length=50)
    open_time: str | None = Field(default=None, max_length=50)
    close_time: str | None = Field(default=None, max_length=50)
    capacity: int | None = Field(default=None, ge=0)

    model_config = ConfigDict(from_attributes=True)


#修改实验室信息
class LabUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    img: str | None = Field(default=None, max_length=200)
    status: LabStatus | None = None
    location: str | None = Field(default=None, max_length=50)
    open_time: str | None = Field(default=None, max_length=50)
    close_time: str | None = Field(default=None, max_length=50)
    capacity: int | None = Field(default=None, ge=0)


#增加实验室信息
class LabCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    img: str | None = Field(default=None, max_length=200)
    status: LabStatus = 1
    location: str | None = Field(default=None, max_length=50)
    open_time: str | None = Field(default=None, max_length=50)
    close_time: str | None = Field(default=None, max_length=50)
    capacity: int | None = Field(default=None, ge=0)


#实验室分页信息
class LabPageResult(BaseModel):
    items: list[LabRequest]
    total: int
    page: int
    page_size: int
    total_pages: int