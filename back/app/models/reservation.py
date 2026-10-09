from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = {"comment": "预约信息表"}

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), comment="预约人ID", nullable=False)
    lab_id: Mapped[int] = mapped_column(Integer, ForeignKey("lab.id"), comment="实验室ID", nullable=False)
    equipment_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("equipments.id"),
        comment="设备ID，空表示仅预约实验室",
        nullable=True,
    )
    date: Mapped[str] = mapped_column(String(50), comment="预约日期", nullable=False)
    start_time: Mapped[str] = mapped_column(String(50), comment="预约开始时间", nullable=False)
    end_time: Mapped[str] = mapped_column(String(50), comment="预约结束时间", nullable=False)
    remarks: Mapped[str | None] = mapped_column(String(255), comment="备注")
    status: Mapped[int] = mapped_column(
        Integer,
        comment="状态:0-待审核,1-已通过,2-已拒绝,3-已取消",
        nullable=False,
        default=0,
    )

    user: Mapped[User] = relationship(lazy="selectin")
    lab: Mapped[Lab] = relationship(lazy="selectin")
    equipment: Mapped[Equipment | None] = relationship(lazy="selectin")
