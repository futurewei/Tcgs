import client from './client';

export interface ProfileStats {
  userId: number | null;
  userName: string;
  userEmail: string | null;
  slotName: string | null;
  slotType: string | null;
  driTopicCount: number;
  participantTopicCount: number;
  completedTopicCount: number;
  inProgressTopicCount: number;
  unsolvableTopicCount: number;
  avgClosureDays: number | null;
  firstAuthorTechPoints: number;
  contributorTechPoints: number;
  deliverableCount: number;
}

export interface TopicItem {
  id: number;
  title: string;
  type: string;
  urgency: string;
  result: string;
  isDri: boolean;
  driName: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface TechPointItem {
  id: number;
  name: string;
  description: string | null;
  status: string;
  hypothesis: string | null;
  stageName: string | null;
  topicId: number | null;
  topicTitle: string | null;
  createdAt: string;
}

export interface DeliverableItem {
  id: number;
  name: string;
  type: string;
  category: string;
  url: string | null;
  topicId: number;
  topicTitle: string | null;
  stageId: number | null;
  stageName: string | null;
  techPointId: number | null;
  techPointName: string | null;
  isFirstAuthor: boolean;
  createdAt: string;
}

export interface TimelineEvent {
  id: number;
  action: string;
  actionLabel: string;
  entityType: string;
  entityId: number;
  entityName: string | null;
  topicId: number | null;
  topicTitle: string | null;
  details: string | null;
  createdAt: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export const profileApi = {
  // 通过用户 ID 获取档案
  getUserProfile: async (userId: number): Promise<ProfileStats> => {
    const response = await client.get<ProfileStats>(`/users/${userId}/profile`);
    return response.data;
  },

  // 通过 slot ID 获取档案
  getSlotProfile: async (slotId: number): Promise<ProfileStats> => {
    const response = await client.get<ProfileStats>(`/slots/${slotId}/profile`);
    return response.data;
  },

  // 获取用户课题列表
  getUserTopics: async (
    userId: number,
    options?: { role?: string; status?: string; page?: number; pageSize?: number }
  ): Promise<PaginatedResponse<TopicItem>> => {
    const response = await client.get<PaginatedResponse<TopicItem>>(
      `/users/${userId}/topics`,
      { params: { role: options?.role, status: options?.status, page: options?.page || 1, page_size: options?.pageSize || 20 } }
    );
    return response.data;
  },

  // 获取用户技术点列表
  getUserTechPoints: async (
    userId: number,
    page = 1,
    pageSize = 20
  ): Promise<PaginatedResponse<TechPointItem>> => {
    const response = await client.get<PaginatedResponse<TechPointItem>>(
      `/users/${userId}/techpoints`,
      { params: { page, page_size: pageSize } }
    );
    return response.data;
  },

  // 获取用户交付物
  getUserDeliverables: async (
    userId: number,
    page = 1,
    pageSize = 20
  ): Promise<PaginatedResponse<DeliverableItem>> => {
    const response = await client.get<PaginatedResponse<DeliverableItem>>(
      `/users/${userId}/deliverables`,
      { params: { page, page_size: pageSize } }
    );
    return response.data;
  },

  // 获取用户时间线
  getUserTimeline: async (
    userId: number,
    page = 1,
    pageSize = 50
  ): Promise<PaginatedResponse<TimelineEvent>> => {
    const response = await client.get<PaginatedResponse<TimelineEvent>>(
      `/users/${userId}/timeline`,
      { params: { page, page_size: pageSize } }
    );
    return response.data;
  },
};
