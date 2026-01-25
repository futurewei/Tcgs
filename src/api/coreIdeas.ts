import client from './client';

export type IdeaType = 
  | 'problem_redefine'      // 问题重定义
  | 'algorithm_hypothesis'  // 算法假设
  | 'model_structure'       // 模型结构
  | 'parameter_strategy'    // 参数策略
  | 'data_perspective'      // 数据视角
  | 'engineering_tradeoff'; // 工程取舍

export type IdeaStatus = 
  | 'hypothesizing'  // 假设中
  | 'verified'       // 已验证
  | 'rejected'       // 被否决
  | 'superseded';    // 被替代

export interface CoreIdea {
  id: number;
  topicId: number;
  title: string;
  ideaType: IdeaType;
  status: IdeaStatus;
  proposerId: number;
  proposerName: string;
  ideaBody: string | null;
  motivation: string | null;
  evidence: string | null;
  impact: string | null;
  supersededById: number | null;
  relatedStageIds: number[];
  relatedStageNames: string[];
  createdAt: string;
  updatedAt: string;
}

export interface CoreIdeaCreate {
  title: string;
  idea_type?: IdeaType;  // 可选，默认 algorithm_hypothesis
  proposer_id: number;
  proposer_name?: string;  // 提出人显示名（Slot 名字）
  idea_body?: string;
  motivation?: string;
  evidence?: string;
  impact?: string;
  related_stage_ids?: number[];
}

export interface CoreIdeaUpdate {
  title?: string;
  idea_type?: IdeaType;
  status?: IdeaStatus;
  idea_body?: string;
  motivation?: string;
  evidence?: string;
  impact?: string;
  related_stage_ids?: number[];
  superseded_by_id?: number;
}

// 类型标签映射
export const ideaTypeLabels: Record<IdeaType, string> = {
  problem_redefine: '问题重定义',
  algorithm_hypothesis: '算法假设',
  model_structure: '模型结构',
  parameter_strategy: '参数策略',
  data_perspective: '数据视角',
  engineering_tradeoff: '工程取舍',
};

// 状态标签映射
export const ideaStatusLabels: Record<IdeaStatus, string> = {
  hypothesizing: '假设中',
  verified: '已验证',
  rejected: '被否决',
  superseded: '被替代',
};

// 状态颜色映射
export const ideaStatusColors: Record<IdeaStatus, string> = {
  hypothesizing: 'warning',
  verified: 'success',
  rejected: 'danger',
  superseded: 'info',
};

// 类型颜色映射
export const ideaTypeColors: Record<IdeaType, string> = {
  problem_redefine: '#6366f1',    // indigo
  algorithm_hypothesis: '#8b5cf6', // violet
  model_structure: '#0ea5e9',     // sky
  parameter_strategy: '#14b8a6',  // teal
  data_perspective: '#f59e0b',    // amber
  engineering_tradeoff: '#64748b', // slate
};

export const coreIdeasApi = {
  // 获取课题的所有 Core Ideas
  list: async (topicId: number): Promise<CoreIdea[]> => {
    const response = await client.get<CoreIdea[]>(`/topics/${topicId}/ideas`);
    return response.data;
  },

  // 获取时间线视图
  getTimeline: async (topicId: number): Promise<CoreIdea[]> => {
    const response = await client.get<CoreIdea[]>(`/topics/${topicId}/ideas/timeline`);
    return response.data;
  },

  // 获取单个 Core Idea
  get: async (topicId: number, ideaId: number): Promise<CoreIdea> => {
    const response = await client.get<CoreIdea>(`/topics/${topicId}/ideas/${ideaId}`);
    return response.data;
  },

  // 创建 Core Idea
  create: async (topicId: number, data: CoreIdeaCreate): Promise<CoreIdea> => {
    const response = await client.post<CoreIdea>(`/topics/${topicId}/ideas`, data);
    return response.data;
  },

  // 更新 Core Idea
  update: async (topicId: number, ideaId: number, data: CoreIdeaUpdate): Promise<CoreIdea> => {
    const response = await client.put<CoreIdea>(`/topics/${topicId}/ideas/${ideaId}`, data);
    return response.data;
  },

  // 删除 Core Idea
  delete: async (topicId: number, ideaId: number): Promise<void> => {
    await client.delete(`/topics/${topicId}/ideas/${ideaId}`);
  },
};
