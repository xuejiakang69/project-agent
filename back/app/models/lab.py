from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from app.database import Base


class Lab(Base):
    __tablename__ = "lab"
    __table_args__ = {"comment": "实验室信息表", "mysql_engine": "InnoDB"}

    name: Mapped[str] = mapped_column(
        String(50), comment="实验室名称", unique=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(255), comment="实验室描述")
    img: Mapped[str | None] = mapped_column(String(200), comment="图片", nullable=True)
    status: Mapped[int] = mapped_column(
        Integer, default=1, comment="状态:0-禁用,1-正常"
    )
    location: Mapped[str | None] = mapped_column(String(50), comment="实验室位置")
    open_time: Mapped[str | None] = mapped_column(String(50), comment="开放时间")
    close_time: Mapped[str | None] = mapped_column(String(50), comment="关闭时间")
    capacity: Mapped[int | None] = mapped_column(Integer, comment="容量")
