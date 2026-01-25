import client from './client';
import type {
  WikiDirection,
  WikiPage,
  WikiRevision,
  WikiPageCreateRequest,
  WikiRevisionCreateRequest,
  WikiComment
} from '@/types';

export interface LikeResponse {
  liked: boolean;
  like_count: number;
}

export const wikiApi = {
  // Directions
  listDirections: async (): Promise<WikiDirection[]> => {
    const response = await client.get<any[]>('/wiki/directions');
    return response.data.map(normalizeDirection);
  },

  getDirection: async (id: number): Promise<WikiDirection> => {
    const response = await client.get<any>(`/wiki/directions/${id}`);
    return normalizeDirection(response.data);
  },

  createDirection: async (data: { name: string; description: string; icon?: string }): Promise<WikiDirection> => {
    const response = await client.post<any>('/wiki/directions', data);
    return normalizeDirection(response.data);
  },

  updateDirection: async (id: number, data: Partial<{ name: string; description: string; icon?: string }>): Promise<WikiDirection> => {
    const response = await client.put<any>(`/wiki/directions/${id}`, data);
    return normalizeDirection(response.data);
  },

  deleteDirection: async (id: number): Promise<void> => {
    await client.delete(`/wiki/directions/${id}`);
  },

  // Pages
  getPage: async (id: number): Promise<WikiPage> => {
    const response = await client.get<any>(`/wiki/pages/${id}`);
    // Normalize response
    return {
      ...response.data,
      viewCount: response.data.view_count ?? response.data.viewCount ?? 0,
      likeCount: response.data.like_count ?? response.data.likeCount ?? 0,
      userLiked: response.data.user_liked ?? response.data.userLiked ?? false,
      currentRevisionId: response.data.current_revision_id ?? response.data.currentRevisionId,
      currentRevision: response.data.current_revision ?? response.data.currentRevision,
      directionId: response.data.direction_id ?? response.data.directionId,
      createdAt: response.data.created_at ?? response.data.createdAt,
      updatedAt: response.data.updated_at ?? response.data.updatedAt,
    };
  },

  createPage: async (data: WikiPageCreateRequest): Promise<WikiPage> => {
    const response = await client.post<WikiPage>('/wiki/pages', {
      direction_id: data.directionId,
      title: data.title,
      parent_id: data.parentId,
      content: data.content
    });
    return response.data;
  },

  updatePage: async (id: number, data: Partial<{ title: string; parentId?: number }>): Promise<WikiPage> => {
    const response = await client.put<WikiPage>(`/wiki/pages/${id}`, {
      title: data.title,
      parent_id: data.parentId
    });
    return response.data;
  },

  deletePage: async (id: number): Promise<void> => {
    await client.delete(`/wiki/pages/${id}`);
  },

  // Revisions
  listRevisions: async (pageId: number): Promise<WikiRevision[]> => {
    const response = await client.get<any[]>(`/wiki/pages/${pageId}/revisions`);
    return response.data.map(r => ({
      ...r,
      pageId: r.page_id ?? r.pageId,
      createdById: r.created_by_id ?? r.createdById,
      createdBy: r.created_by ?? r.createdBy,
      createdAt: r.created_at ?? r.createdAt,
    }));
  },

  createRevision: async (data: WikiRevisionCreateRequest): Promise<WikiRevision> => {
    const response = await client.post<WikiRevision>(`/wiki/pages/${data.pageId}/revisions`, {
      content: data.content
    });
    return response.data;
  },

  getRevision: async (id: number): Promise<WikiRevision> => {
    const response = await client.get<WikiRevision>(`/wiki/revisions/${id}`);
    return response.data;
  },

  // ============ Comments (评论) ============
  listComments: async (pageId: number): Promise<WikiComment[]> => {
    const response = await client.get<any[]>(`/wiki/pages/${pageId}/comments`);
    return response.data.map(normalizeComment);
  },

  createComment: async (pageId: number, content: string, parentId?: number): Promise<WikiComment> => {
    const response = await client.post<any>(`/wiki/pages/${pageId}/comments`, {
      content,
      parent_id: parentId
    });
    return normalizeComment(response.data);
  },

  deleteComment: async (commentId: number): Promise<void> => {
    await client.delete(`/wiki/comments/${commentId}`);
  },

  // ============ Likes (点赞) ============
  toggleLike: async (pageId: number): Promise<LikeResponse> => {
    const response = await client.post<LikeResponse>(`/wiki/pages/${pageId}/like`);
    return response.data;
  },

  getLikeStatus: async (pageId: number): Promise<LikeResponse> => {
    const response = await client.get<LikeResponse>(`/wiki/pages/${pageId}/like`);
    return response.data;
  },
};

function normalizePage(p: any): WikiPage {
  return {
    ...p,
    directionId: p.direction_id ?? p.directionId,
    parentId: p.parent_id ?? p.parentId,
    currentRevisionId: p.current_revision_id ?? p.currentRevisionId,
    currentRevision: p.current_revision ?? p.currentRevision,
    viewCount: p.view_count ?? p.viewCount ?? 0,
    likeCount: p.like_count ?? p.likeCount ?? 0,
    userLiked: p.user_liked ?? p.userLiked ?? false,
    createdAt: p.created_at ?? p.createdAt,
    updatedAt: p.updated_at ?? p.updatedAt,
    comments: (p.comments || []).map(normalizeComment),
  };
}

function normalizeDirection(d: any): WikiDirection {
  return {
    ...d,
    createdAt: d.created_at ?? d.createdAt,
    updatedAt: d.updated_at ?? d.updatedAt,
    pages: (d.pages || []).map(normalizePage),
  };
}

function normalizeComment(c: any): WikiComment {
  return {
    ...c,
    pageId: c.page_id ?? c.pageId,
    parentId: c.parent_id ?? c.parentId,
    createdById: c.created_by_id ?? c.createdById,
    createdBy: c.created_by ?? c.createdBy,
    createdAt: c.created_at ?? c.createdAt,
    updatedAt: c.updated_at ?? c.updatedAt,
    replies: (c.replies || []).map(normalizeComment),
  };
}
