import client from './client';

export interface MergedCell {
  startRow: number;
  endRow: number;
  startCol: number;
  endCol: number;
}

export interface SheetData {
  name: string;
  rows: string[][];
  colWidths: number[];
  mergedCells: MergedCell[];
  maxRow: number;
  maxCol: number;
}

export interface ResponsibilityData {
  sheets: SheetData[];
  uploadedAt: string;
  originalFilename: string;
  uploadedBy: string;
  uploadedById: number;
}

export const responsibilityApi = {
  // 获取责任田数据
  getData: async (): Promise<{ success: boolean; data: ResponsibilityData | null }> => {
    const response = await client.get('/responsibility');
    return response.data;
  },

  // 上传 Excel 文件
  upload: async (file: File): Promise<{ success: boolean; message: string; data: ResponsibilityData }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await client.post('/responsibility/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 删除责任田数据
  delete: async (): Promise<{ success: boolean; message: string }> => {
    const response = await client.delete('/responsibility');
    return response.data;
  },
};
