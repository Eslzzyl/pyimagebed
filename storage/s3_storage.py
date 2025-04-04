import boto3
import botocore.exceptions
from io import BytesIO

from .base_storage import BaseStorage


class S3Storage(BaseStorage):
    """Amazon S3存储实现"""

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
        bucket_name: str,
    ):
        self.bucket_name = bucket_name

        # 初始化S3客户端
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

        # 检查并确保bucket存在
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except botocore.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                # Bucket不存在，尝试创建
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region_name},
                )
            else:
                # 其他错误，抛出异常
                raise

    async def save(self, filename: str, content: bytes) -> bool:
        try:
            self.s3_client.upload_fileobj(BytesIO(content), self.bucket_name, filename)
            return True
        except Exception as e:
            print(f"S3保存文件失败: {str(e)}")
            return False

    async def read(self, filename: str) -> bytes:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=filename)
            return response["Body"].read()
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"文件不存在: {filename}")
            raise

    async def delete(self, filename: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=filename)
            return True
        except Exception as e:
            print(f"S3删除文件失败: {str(e)}")
            return False

    async def exists(self, filename: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=filename)
            return True
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            # 其他错误，抛出异常
            raise
