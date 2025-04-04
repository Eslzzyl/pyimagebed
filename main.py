import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import hashlib
import json
import mimetypes
import uuid
from pathlib import Path
from datetime import datetime

from storage.storage_manager import StorageManager
from storage.local_storage import LocalStorage
from storage.s3_storage import S3Storage

# 创建应用
app = FastAPI(title="PyImageBed", description="Python图床服务")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保目录存在
for dir_path in ["static", "uploads", "data"]:
    os.makedirs(dir_path, exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 创建存储管理器
storage_manager = StorageManager()

# 添加默认存储
storage_manager.add_storage("local", LocalStorage(base_dir="uploads"))

# 尝试从配置加载S3存储
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        if "s3" in config:
            storage_manager.add_storage(
                "s3",
                S3Storage(
                    aws_access_key_id=config["s3"]["aws_access_key_id"],
                    aws_secret_access_key=config["s3"]["aws_secret_access_key"],
                    region_name=config["s3"]["region_name"],
                    bucket_name=config["s3"]["bucket_name"],
                ),
            )
except FileNotFoundError:
    print("配置文件未找到，仅使用本地存储")
except Exception as e:
    print(f"加载配置出错: {str(e)}")


# 哈希图片内容
def hash_image(image_data: bytes) -> str:
    return hashlib.md5(image_data).hexdigest()


# 保存元数据
def save_metadata(
    file_id: str,
    original_filename: str,
    content_type: str,
    storage_type: str,
    file_hash: str,
    file_size: int,
):
    data_file = Path("data/metadata.json")

    if data_file.exists():
        with open(data_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = []

    # 添加新记录
    metadata.append(
        {
            "id": file_id,
            "original_filename": original_filename,
            "content_type": content_type,
            "storage_type": storage_type,
            "hash": file_hash,
            "size": file_size,
            "upload_time": datetime.now().isoformat(),
        }
    )

    # 保存回文件
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


# 根据哈希值查找图片
def find_by_hash(file_hash: str):
    data_file = Path("data/metadata.json")

    if not data_file.exists():
        return None

    with open(data_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    for item in metadata:
        if item["hash"] == file_hash:
            return item

    return None


# 获取所有图片的元数据
def get_all_metadata():
    data_file = Path("data/metadata.json")

    if not data_file.exists():
        return []

    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)


# 删除元数据
def delete_metadata(file_id: str):
    data_file = Path("data/metadata.json")

    if not data_file.exists():
        return False

    with open(data_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    original_count = len(metadata)
    metadata = [item for item in metadata if item["id"] != file_id]

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return len(metadata) < original_count


# API路由


@app.get("/")
async def read_root():
    return FileResponse("static/index.html")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), storage_type: str = Form("local")):
    # 读取文件内容
    file_content = await file.read()
    file_size = len(file_content)

    # 生成文件哈希
    file_hash = hash_image(file_content)

    # 检查是否已存在相同哈希的图片
    existing = find_by_hash(file_hash)
    if existing:
        return {
            "success": True,
            "message": "文件已存在",
            "file_id": existing["id"],
            "url": f"/images/{existing['id']}",
            "is_duplicate": True,
        }

    # 确定文件扩展名
    original_filename = file.filename
    ext = os.path.splitext(original_filename)[1].lower() if original_filename else ""
    if not ext and file.content_type:
        ext = mimetypes.guess_extension(file.content_type) or ""

    # 生成唯一ID
    file_id = str(uuid.uuid4())

    # 存储文件
    if storage_type not in storage_manager.storages:
        raise HTTPException(status_code=400, detail=f"不支持的存储类型: {storage_type}")

    storage = storage_manager.get_storage(storage_type)
    await storage.save(file_id + ext, file_content)

    # 保存元数据
    save_metadata(
        file_id=file_id,
        original_filename=original_filename,
        content_type=file.content_type or "application/octet-stream",
        storage_type=storage_type,
        file_hash=file_hash,
        file_size=file_size,
    )

    return {
        "success": True,
        "message": "文件上传成功",
        "file_id": file_id,
        "url": f"/images/{file_id}",
        "is_duplicate": False,
    }


@app.get("/images/{file_id}")
async def get_image(file_id: str):
    # 查找元数据
    all_metadata = get_all_metadata()
    file_metadata = None

    for item in all_metadata:
        if item["id"] == file_id or item["id"] == os.path.splitext(file_id)[0]:
            file_metadata = item
            break

    if not file_metadata:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 获取存储
    storage_type = file_metadata["storage_type"]
    if storage_type not in storage_manager.storages:
        raise HTTPException(status_code=500, detail="存储类型不可用")

    storage = storage_manager.get_storage(storage_type)

    # 确定扩展名
    ext = os.path.splitext(file_metadata["original_filename"])[1]

    # 读取文件
    try:
        file_data = await storage.read(file_id + ext)
        from fastapi.responses import Response

        return Response(content=file_data, media_type=file_metadata["content_type"])
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"读取图片失败: {str(e)}")


@app.delete("/images/{file_id}")
async def delete_image(file_id: str):
    # 查找元数据
    all_metadata = get_all_metadata()
    file_metadata = None

    for item in all_metadata:
        if item["id"] == file_id or item["id"] == os.path.splitext(file_id)[0]:
            file_metadata = item
            break

    if not file_metadata:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 获取存储
    storage_type = file_metadata["storage_type"]
    if storage_type not in storage_manager.storages:
        raise HTTPException(status_code=500, detail="存储类型不可用")

    storage = storage_manager.get_storage(storage_type)

    # 确定扩展名
    ext = os.path.splitext(file_metadata["original_filename"])[1]

    # 删除文件
    try:
        await storage.delete(file_id + ext)
        delete_metadata(file_metadata["id"])
        return {"success": True, "message": "图片删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除图片失败: {str(e)}")


@app.get("/list")
async def list_images():
    return {"images": get_all_metadata()}


@app.get("/storage-types")
async def list_storage_types():
    return {"storage_types": list(storage_manager.storages.keys())}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7899)
