"""
文件上传服务 - 使用 MinIO 存储
"""
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
from datetime import timedelta
import uuid
import os
from io import BytesIO
import json
from ..config import get_settings

settings = get_settings()


def get_minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )


def ensure_bucket_exists(client: Minio, bucket_name: str):
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }]
            }
            client.set_bucket_policy(bucket_name, json.dumps(policy))
    except S3Error as e:
        print(f"MinIO error: {e}")


def get_public_url(object_name: str) -> str:
    """
    返回浏览器可访问的公开 URL
    
    MinIO endpoint 在 docker 内部是 minio:9000
    但浏览器需要访问 localhost:9000
    """
    # 获取公开访问的 endpoint（浏览器可访问）
    public_endpoint = os.environ.get("MINIO_PUBLIC_ENDPOINT", "localhost:9000")
    scheme = "https" if settings.MINIO_SECURE else "http"
    return f"{scheme}://{public_endpoint}/{settings.MINIO_BUCKET}/{object_name}"


async def upload_file(file: UploadFile, folder: str = "uploads", allowed_types: list = None) -> dict:
    if allowed_types and file.content_type not in allowed_types:
        raise ValueError(f"不支持的文件类型: {file.content_type}")
    
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    object_name = f"{folder}/{unique_name}"
    
    content = await file.read()
    file_size = len(content)
    
    client = get_minio_client()
    ensure_bucket_exists(client, settings.MINIO_BUCKET)
    
    client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        BytesIO(content),
        file_size,
        content_type=file.content_type
    )
    
    # 使用公开 URL
    url = get_public_url(object_name)
    
    return {
        "url": url,
        "filename": unique_name,
        "originalName": file.filename,
        "mimeType": file.content_type,
        "size": file_size,
        "objectName": object_name
    }


async def upload_image(file: UploadFile, folder: str = "images") -> dict:
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml", "image/bmp"]
    return await upload_file(file, folder, allowed_types)


def delete_file(object_name: str) -> bool:
    try:
        client = get_minio_client()
        client.remove_object(settings.MINIO_BUCKET, object_name)
        return True
    except S3Error:
        return False
