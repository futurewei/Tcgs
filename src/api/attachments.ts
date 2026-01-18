import client from './client';
import type { Attachment } from '@/types';

export const attachmentsApi = {
  upload: async (file: File, artifactId?: number): Promise<Attachment> => {
    const formData = new FormData();
    formData.append('file', file);
    if (artifactId) {
      formData.append('artifactId', artifactId.toString());
    }

    const response = await client.post<Attachment>('/attachments/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  list: async (artifactId: number): Promise<Attachment[]> => {
    const response = await client.get<Attachment[]>('/attachments', {
      params: { artifactId }
    });
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/attachments/${id}`);
  },

  getDownloadUrl: async (id: number): Promise<string> => {
    const response = await client.get<{ url: string }>(`/attachments/${id}/download`);
    return response.data.url;
  },
};
