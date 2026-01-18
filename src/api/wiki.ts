import client from './client';
import type {
  WikiDirection,
  WikiPage,
  WikiRevision,
  WikiPageCreateRequest,
  WikiRevisionCreateRequest
} from '@/types';

export const wikiApi = {
  // Directions
  listDirections: async (): Promise<WikiDirection[]> => {
    const response = await client.get<WikiDirection[]>('/wiki/directions');
    return response.data;
  },

  getDirection: async (id: number): Promise<WikiDirection> => {
    const response = await client.get<WikiDirection>(`/wiki/directions/${id}`);
    return response.data;
  },

  createDirection: async (data: { name: string; description: string; icon?: string }): Promise<WikiDirection> => {
    const response = await client.post<WikiDirection>('/wiki/directions', data);
    return response.data;
  },

  updateDirection: async (id: number, data: Partial<{ name: string; description: string; icon?: string }>): Promise<WikiDirection> => {
    const response = await client.put<WikiDirection>(`/wiki/directions/${id}`, data);
    return response.data;
  },

  deleteDirection: async (id: number): Promise<void> => {
    await client.delete(`/wiki/directions/${id}`);
  },

  // Pages
  getPage: async (id: number): Promise<WikiPage> => {
    const response = await client.get<WikiPage>(`/wiki/pages/${id}`);
    return response.data;
  },

  createPage: async (data: WikiPageCreateRequest): Promise<WikiPage> => {
    const response = await client.post<WikiPage>('/wiki/pages', data);
    return response.data;
  },

  updatePage: async (id: number, data: Partial<{ title: string; parentId?: number }>): Promise<WikiPage> => {
    const response = await client.put<WikiPage>(`/wiki/pages/${id}`, data);
    return response.data;
  },

  deletePage: async (id: number): Promise<void> => {
    await client.delete(`/wiki/pages/${id}`);
  },

  // Revisions
  listRevisions: async (pageId: number): Promise<WikiRevision[]> => {
    const response = await client.get<WikiRevision[]>(`/wiki/pages/${pageId}/revisions`);
    return response.data;
  },

  createRevision: async (data: WikiRevisionCreateRequest): Promise<WikiRevision> => {
    const response = await client.post<WikiRevision>(`/wiki/pages/${data.pageId}/revisions`, data);
    return response.data;
  },

  getRevision: async (id: number): Promise<WikiRevision> => {
    const response = await client.get<WikiRevision>(`/wiki/revisions/${id}`);
    return response.data;
  },
};
