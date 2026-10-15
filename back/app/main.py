from fastapi import FastAPI
from app.database import Base,engine, create_tables
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.api.auth import router as auth_router
from app.api.files import router as file_router
from app.api.user import router as user_router
from app.api.lab import router as lab_router
from app.api.reservation import router as reservation_router
from app.api.equipment import router as equipment_router
from app.agent.api.chat import router as agent_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import UPLOAD_DIR
from contextlib import asynccontextmanager
from app.agent.crud.kb import async_init_knowledge_base
import logging

logging.basicConfig(
     level=logging.INFO,  # 级别：DEBUG < INFO < WARNING < ERROR < CRITICAL
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

logger.debug("调试信息，开发用")
logger.info("普通信息，比如服务启动、用户登录")
logger.warning("警告信息")
logger.error("错误信息，比如数据库查询失败")
logger.critical("严重错误")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await create_tables()
    await async_init_knowledge_base()
    yield
    # shutdown
    await engine.dispose()




app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://test.online3.me",],
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True
)

app.include_router(auth_router,prefix="")
app.include_router(file_router,prefix="")
app.include_router(user_router,prefix="")
app.include_router(lab_router,prefix="")
app.include_router(equipment_router,prefix="")
app.include_router(reservation_router,prefix="")
app.include_router(agent_router,prefix="")

#静态目录挂载
app.mount("/uploads",StaticFiles(directory=UPLOAD_DIR),name="uploads")
