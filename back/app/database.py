from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped,DeclarativeBase,mapped_column
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL,echo=True,
    pool_pre_ping=True,)


async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession

)

#获取数据库会话
async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

class Base(DeclarativeBase):
    id:Mapped[int] = mapped_column(primary_key=True,autoincrement=True,comment="主键")
    create_time:Mapped[datetime] = mapped_column(DateTime,default=datetime.now,comment="创建时间")
    updated_time:Mapped[datetime] = mapped_column(DateTime,default=datetime.now,onupdate=datetime.now,comment="修改时间")