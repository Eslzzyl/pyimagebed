from .base_storage import BaseStorage
from typing import Dict


class StorageManager:
    """存储管理器，用于管理多个存储源"""

    def __init__(self):
        # 存储源字典 {名称: 存储实例}
        self.storages: Dict[str, BaseStorage] = {}

        # 默认存储源名称
        self.default_storage = None

    def add_storage(self, name: str, storage: BaseStorage):
        """
        添加存储源
        :param name: 存储名称
        :param storage: 存储实例
        """
        self.storages[name] = storage

        # 如果没有默认存储，设置第一个添加的为默认
        if self.default_storage is None:
            self.default_storage = name

    def remove_storage(self, name: str):
        """
        移除存储源
        :param name: 存储名称
        """
        if name in self.storages:
            del self.storages[name]

            # 如果删除的是默认存储，重新设置默认
            if self.default_storage == name:
                self.default_storage = (
                    next(iter(self.storages)) if self.storages else None
                )

    def get_storage(self, name: str = None) -> BaseStorage:
        """
        获取存储源
        :param name: 存储名称，不指定则返回默认存储
        :return: 存储实例
        """
        if name is None:
            name = self.default_storage

        if name not in self.storages:
            raise KeyError(f"存储源不存在: {name}")

        return self.storages[name]

    def set_default(self, name: str):
        """
        设置默认存储源
        :param name: 存储名称
        """
        if name not in self.storages:
            raise KeyError(f"存储源不存在: {name}")

        self.default_storage = name
