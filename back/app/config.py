from pydantic_settings import BaseSettings,SettingsConfigDict
from pathlib import Path


BASE_DIR=Path(__file__).resolve().parent.parent #后端根路径

class Setting(BaseSettings):
    DATABASE_URL:str
    JWT_KEY :str
    JWT_ALGORITHM:str = "HS256"
    JWT_EXPIRE : int

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",env_file_encoding="utf-8"
    )

settings = Setting()


UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
MAX_FILE_SIZE = 1000*1024*1024
ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip"
}