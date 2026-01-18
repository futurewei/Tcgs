// User & Auth Types
export type UserRole = 'ADMIN' | 'MEMBER' | 'REVIEWER' | 'EXTERNAL' | 'CUSTOMER';

export interface User {
  id: number;
  email: string;
  name: string;
  avatar?: string;
  role: UserRole;
  createdAt: string;
  updatedAt: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  accessToken: string;
  tokenType: string;
  user: User;
}

// Stage Template Types
export interface StageTemplateStage {
  id: number;
  templateId: number;
  name: string;
  description: string;
  order: number;
  isTerminal: boolean;
  allowResult: boolean;
  requireArtifact: boolean;
}

export interface StageTemplate {
  id: number;
  name: string;
  description: string;
  stages: StageTemplateStage[];
  createdAt: string;
  updatedAt: string;
}

// Topic Types
export type TopicType = 'UNCERTAINTY' | 'EVOLUTION';
export type TopicResult = 'OPEN' | 'SUCCESS' | 'UNSOLVABLE';
export type TopicUrgency = 'P0' | 'P1' | 'P2' | 'P3';
export type StageStatus = 'pending' | 'active' | 'done';

export interface TopicStageState {
  id: number;
  topicId: number;
  stageId: number;
  stage: StageTemplateStage;
  status: StageStatus;
  completedAt?: string;
}

export interface Topic {
  id: number;
  title: string;
  description: string;
  type: TopicType;
  urgency: TopicUrgency;
  result: TopicResult;
  driId: number;
  dri: User;
  templateId: number;
  template: StageTemplate;
  stageStates: TopicStageState[];
  currentStageId?: number;
  requesterName: string;
  requesterUserId?: number;
  requesterUser?: User;
  artifacts: Artifact[];
  reviews: ReviewComment[];
  bindings: Binding[];
  createdAt: string;
  updatedAt: string;
}

export interface TopicCreateRequest {
  title: string;
  description: string;
  type: TopicType;
  urgency: TopicUrgency;
  driId: number;
  templateId: number;
  requesterName: string;
  requesterUserId?: number;
}

export interface TopicUpdateRequest {
  title?: string;
  description?: string;
  urgency?: TopicUrgency;
  result?: TopicResult;
  driId?: number;
  currentStageId?: number;
}

// Artifact Types
export interface Artifact {
  id: number;
  topicId: number;
  stageId: number;
  title: string;
  content: string;
  attachments: Attachment[];
  createdById: number;
  createdBy: User;
  createdAt: string;
}

export interface ArtifactCreateRequest {
  topicId: number;
  stageId: number;
  title: string;
  content: string;
}

// Review Types
export interface ReviewComment {
  id: number;
  topicId: number;
  stageId: number;
  content: string;
  createdById: number;
  createdBy: User;
  createdAt: string;
}

export interface ReviewCreateRequest {
  topicId: number;
  stageId: number;
  content: string;
}

// Capacity Slot Types
export type SlotType = 'ALGO' | 'EXTERNAL';
export type SlotStatus = 'available' | 'partial' | 'occupied';

export interface CapacitySlot {
  id: number;
  name: string;
  type: SlotType;
  userId?: number;
  user?: User;
  totalCapacity: number;
  bindings: Binding[];
  createdAt: string;
  updatedAt: string;
}

export interface SlotCreateRequest {
  name: string;
  type: SlotType;
  userId?: number;
  totalCapacity: number;
}

// Binding Types
export interface Binding {
  id: number;
  topicId: number;
  topic?: Topic;
  slotId: number;
  slot?: CapacitySlot;
  percentage: number;
  isForced: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface BindingCreateRequest {
  topicId: number;
  slotId: number;
  percentage: number;
  isForced?: boolean;
}

// Wiki Types
export interface WikiDirection {
  id: number;
  name: string;
  description: string;
  icon?: string;
  pages: WikiPage[];
  createdAt: string;
  updatedAt: string;
}

export interface WikiPage {
  id: number;
  directionId: number;
  title: string;
  parentId?: number;
  children?: WikiPage[];
  currentRevisionId?: number;
  currentRevision?: WikiRevision;
  createdAt: string;
  updatedAt: string;
}

export interface WikiRevision {
  id: number;
  pageId: number;
  content: string;
  version: number;
  createdById: number;
  createdBy: User;
  createdAt: string;
}

export interface WikiPageCreateRequest {
  directionId: number;
  title: string;
  parentId?: number;
  content: string;
}

export interface WikiRevisionCreateRequest {
  pageId: number;
  content: string;
}

// Attachment Types
export interface Attachment {
  id: number;
  filename: string;
  originalName: string;
  mimeType: string;
  size: number;
  url: string;
  artifactId?: number;
  createdById: number;
  createdAt: string;
}

// Audit Log Types
export type AuditAction =
  | 'TOPIC_CREATE'
  | 'TOPIC_UPDATE'
  | 'TOPIC_DELETE'
  | 'DRI_CHANGE'
  | 'RESULT_CHANGE'
  | 'STAGE_CHANGE'
  | 'SLOT_CREATE'
  | 'SLOT_UPDATE'
  | 'SLOT_DELETE'
  | 'BINDING_CREATE'
  | 'BINDING_UPDATE'
  | 'BINDING_DELETE'
  | 'BINDING_FORCE'
  | 'USER_CREATE'
  | 'USER_UPDATE'
  | 'USER_DELETE'
  | 'WIKI_CREATE'
  | 'WIKI_UPDATE';

export interface AuditLog {
  id: number;
  action: AuditAction;
  entityType: string;
  entityId: number;
  oldValue?: string;
  newValue?: string;
  userId: number;
  user: User;
  createdAt: string;
}

// Insights Types
export interface DashboardKPI {
  totalTopics: number;
  openTopics: number;
  successTopics: number;
  unsolvableTopics: number;
  avgCycleDays: number;
  uncertaintyCount: number;
  evolutionCount: number;
}

export interface ThroughputData {
  month: string;
  newTopics: number;
  closedTopics: number;
  uncertainty: number;
  evolution: number;
}

export interface PersonLoadData {
  userId: number;
  userName: string;
  driTopics: number;
  collaborationTopics: number;
  totalPercentage: number;
}

export interface ExternalCollabData {
  userId: number;
  userName: string;
  topicCount: number;
  stageDistribution: Record<string, number>;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// API Response
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}
