"""
文件上传 API
支持：图片上传（用于 Wiki、课题背景等富文本）
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..services.auth import get_current_user
from ..services.storage import upload_file, upload_image, delete_file

router = APIRouter()


@router.post("/image")
async def upload_image_api(
    file: UploadFile = File(...),
    folder: str = "images",
    current_user: User = Depends(get_current_user)
):
    """
    上传图片
    
    支持格式：JPEG, PNG, GIF, WebP, SVG, BMP
    返回：图片 URL
    """
    try:
        result = await upload_image(file, folder)
        return {
            "success": True,
            "url": result["url"],
            "filename": result["filename"],
            "originalName": result["originalName"],
            "mimeType": result["mimeType"],
            "size": result["size"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/file")
async def upload_file_api(
    file: UploadFile = File(...),
    folder: str = "files",
    current_user: User = Depends(get_current_user)
):
    """
    上传通用文件
    
    支持所有文件类型
    返回：文件 URL
    """
    try:
        result = await upload_file(file, folder)
        return {
            "success": True,
            "url": result["url"],
            "filename": result["filename"],
            "originalName": result["originalName"],
            "mimeType": result["mimeType"],
            "size": result["size"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.delete("")
async def delete_file_api(
    object_name: str,
    current_user: User = Depends(get_current_user)
):
    """删除文件"""
    success = delete_file(object_name)
    if success:
        return {"success": True, "message": "文件已删除"}
    else:
        raise HTTPException(status_code=404, detail="文件不存在或删除失败")
