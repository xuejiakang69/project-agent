from fastapi import FastAPI
from app.database import Base,engine, create_tables
from app.models.user import User
from app.api.auth import router as auth_router
from app.api.files import router as file_router
from app.api.user import router as user_router
from app.api.lab import router as lab_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import UPLOAD_DIR
from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await create_tables()
    yield
    # shutdown
    await engine.dispose()




app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True
)

app.include_router(auth_router,prefix="")
app.include_router(file_router,prefix="")
app.include_router(user_router,prefix="")
app.include_router(lab_router,prefix="")

#静态目录挂载
app.mount("/uploads",StaticFiles(directory=UPLOAD_DIR),name="uploads")
