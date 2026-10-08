import os
import shutil
import time
from pathlib import Path
import uuid
from app.schemas.common import Result
from fastapi import APIRouter, UploadFile,File,HTTPException
from app.config import ALLOWED_EXTENSIONS,MAX_FILE_SIZE,UPLOAD_DIR



router = APIRouter(prefix="/api/file",tags=["文件传输"])


@router.post("/upload")
async def upload(file:UploadFile=File(...)):
    #判断名称是否为空
    if not file.filename:
        raise HTTPException(detail="名称不能为空")

    #获取原始名称
    orignal_name = os.path.basename(file.filename)

    #获取后缀
    ext = Path(orignal_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(detail=f"不支持该后缀名：{ext}")
    if file.size and file.size > MAX_FILE_SIZE:
        return HTTPException(detail=f"不能超过{MAX_FILE_SIZE//1024//1024}MB")

    #设置唯一的名称
    disk_name = f"{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}{ext}"

    #文件的存储路径
    save_path = UPLOAD_DIR / disk_name

    with open(save_path,"wb") as f:
        shutil.copyfileobj(file.file,f)

    return Result(result={"orignal_name":orignal_name,"disk_name":disk_name,"size":file.size,"url":f"/uploads/{orignal_name}"})
