from abc import ABC, abstractmethod

class BaseStorage(ABC):
    """存储源基类，定义存储源需要实现的接口"""
    
    @abstractmethod
    async def save(self, filename: str, content: bytes) -> bool:
        """
        保存文件
        :param filename: 文件名
        :param content: 文件内容
        :return: 是否成功
        """
        pass
    
    @abstractmethod
    async def read(self, filename: str) -> bytes:
        """
        读取文件
        :param filename: 文件名
        :return: 文件内容
        """
        pass
    
    @abstractmethod
    async def delete(self, filename: str) -> bool:
        """
        删除文件
        :param filename: 文件名
        :return: 是否成功
        """
        pass
    
    @abstractmethod
    async def exists(self, filename: str) -> bool:
        """
        检查文件是否存在
        :param filename: 文件名
        :return: 是否存在
        """
        pass
