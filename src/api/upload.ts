// src/api/upload.ts
import client from './client';

export interface UploadResult {
  success: boolean;
  url: string;
  filename: string;
  originalName: string;
  mimeType: string;
  size: number;
}

export const uploadApi = {
  /**
   * 上传图片
   * 支持格式：JPEG, PNG, GIF, WebP, SVG, BMP
   */
  uploadImage: async (file: File, folder: string = 'images'): Promise<UploadResult> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await client.post<UploadResult>(`/upload/image?folder=${encodeURIComponent(folder)}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  /**
   * 上传通用文件
   */
  uploadFile: async (file: File, folder: string = 'files'): Promise<UploadResult> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await client.post<UploadResult>(`/upload/file?folder=${encodeURIComponent(folder)}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  /**
   * 删除文件
   */
  deleteFile: async (objectName: string): Promise<void> => {
    await client.delete(`/upload?object_name=${encodeURIComponent(objectName)}`);
  }
};
