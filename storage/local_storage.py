import os
import aiofiles
from pathlib import Path

from .base_storage import BaseStorage

class LocalStorage(BaseStorage):
    """本地文件系统存储实现"""
    
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = Path(base_dir)
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
    
    async def save(self, filename: str, content: bytes) -> bool:
        file_path = self.base_dir / filename
        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            return True
        except Exception as e:
            print(f"保存文件失败: {str(e)}")
            return False
    
    async def read(self, filename: str) -> bytes:
        file_path = self.base_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {filename}")
        
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()
    
    async def delete(self, filename: str) -> bool:
        file_path = self.base_dir / filename
        try:
            if file_path.exists():
                os.remove(file_path)
            return True
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            return False
    
    async def exists(self, filename: str) -> bool:
        file_path = self.base_dir / filename
        return file_path.exists()
