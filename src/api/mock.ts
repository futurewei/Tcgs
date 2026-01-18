// Mock data for demo when backend is not available
import type {
  User, Topic, CapacitySlot, StageTemplate,
  WikiDirection, DashboardKPI, ThroughputData,
  PersonLoadData, ExternalCollabData, AuditLog
} from '@/types';

const mockUsers: User[] = [
  { id: 1, email: 'admin@tcgs.local', name: 'Admin User', role: 'ADMIN', createdAt: '2024-01-01', updatedAt: '2024-01-01' },
  { id: 2, email: 'alice@tcgs.local', name: 'Alice Chen', role: 'MEMBER', createdAt: '2024-01-02', updatedAt: '2024-01-02' },
  { id: 3, email: 'bob@tcgs.local', name: 'Bob Wang', role: 'REVIEWER', createdAt: '2024-01-03', updatedAt: '2024-01-03' },
  { id: 4, email: 'external@tcgs.local', name: 'External Partner', role: 'EXTERNAL', createdAt: '2024-01-04', updatedAt: '2024-01-04' },
];

const mockTemplates: StageTemplate[] = [
  {
    id: 1,
    name: 'Standard Workflow',
    description: 'Standard 4-stage workflow',
    stages: [
      { id: 1, templateId: 1, name: 'Definition', description: 'Define the problem', order: 0, isTerminal: false, allowResult: false, requireArtifact: true },
      { id: 2, templateId: 1, name: 'Analysis', description: 'Analyze solutions', order: 1, isTerminal: false, allowResult: false, requireArtifact: true },
      { id: 3, templateId: 1, name: 'Implementation', description: 'Implement solution', order: 2, isTerminal: false, allowResult: false, requireArtifact: true },
      { id: 4, templateId: 1, name: 'Closure', description: 'Review and close', order: 3, isTerminal: true, allowResult: true, requireArtifact: false },
    ],
    createdAt: '2024-01-01',
    updatedAt: '2024-01-01',
  },
  {
    id: 2,
    name: 'POC Template',
    description: 'Quick proof-of-concept',
    stages: [
      { id: 5, templateId: 2, name: 'Exploration', description: 'Explore problem', order: 0, isTerminal: false, allowResult: false, requireArtifact: false },
      { id: 6, templateId: 2, name: 'POC', description: 'Build POC', order: 1, isTerminal: false, allowResult: false, requireArtifact: true },
      { id: 7, templateId: 2, name: 'Decision', description: 'Go/No-go', order: 2, isTerminal: true, allowResult: true, requireArtifact: false },
    ],
    createdAt: '2024-01-01',
    updatedAt: '2024-01-01',
  },
];

const mockTopics: Topic[] = [
  {
    id: 1,
    title: 'Algorithm Optimization Research',
    description: 'Research and optimize core algorithms',
    type: 'UNCERTAINTY',
    urgency: 'P0',
    result: 'OPEN',
    driId: 2,
    dri: mockUsers[1],
    templateId: 1,
    template: mockTemplates[0],
    currentStageId: 2,
    stageStates: [
      { id: 1, topicId: 1, stageId: 1, stage: mockTemplates[0].stages[0], status: 'done' },
      { id: 2, topicId: 1, stageId: 2, stage: mockTemplates[0].stages[1], status: 'active' },
      { id: 3, topicId: 1, stageId: 3, stage: mockTemplates[0].stages[2], status: 'pending' },
      { id: 4, topicId: 1, stageId: 4, stage: mockTemplates[0].stages[3], status: 'pending' },
    ],
    artifacts: [],
    reviews: [],
    bindings: [],
    createdAt: '2024-01-10',
    updatedAt: '2024-01-15',
  },
  {
    id: 2,
    title: 'Data Pipeline Enhancement',
    description: 'Improve data pipeline performance',
    type: 'EVOLUTION',
    urgency: 'P1',
    result: 'OPEN',
    driId: 3,
    dri: mockUsers[2],
    templateId: 1,
    template: mockTemplates[0],
    currentStageId: 1,
    stageStates: [
      { id: 5, topicId: 2, stageId: 1, stage: mockTemplates[0].stages[0], status: 'active' },
      { id: 6, topicId: 2, stageId: 2, stage: mockTemplates[0].stages[1], status: 'pending' },
      { id: 7, topicId: 2, stageId: 3, stage: mockTemplates[0].stages[2], status: 'pending' },
      { id: 8, topicId: 2, stageId: 4, stage: mockTemplates[0].stages[3], status: 'pending' },
    ],
    artifacts: [],
    reviews: [],
    bindings: [],
    createdAt: '2024-01-12',
    updatedAt: '2024-01-14',
  },
  {
    id: 3,
    title: 'ML Model Accuracy Investigation',
    description: 'Investigate and improve model accuracy',
    type: 'UNCERTAINTY',
    urgency: 'P1',
    result: 'OPEN',
    driId: 2,
    dri: mockUsers[1],
    templateId: 2,
    template: mockTemplates[1],
    currentStageId: 6,
    stageStates: [
      { id: 9, topicId: 3, stageId: 5, stage: mockTemplates[1].stages[0], status: 'done' },
      { id: 10, topicId: 3, stageId: 6, stage: mockTemplates[1].stages[1], status: 'active' },
      { id: 11, topicId: 3, stageId: 7, stage: mockTemplates[1].stages[2], status: 'pending' },
    ],
    artifacts: [],
    reviews: [],
    bindings: [],
    createdAt: '2024-01-08',
    updatedAt: '2024-01-16',
  },
];

const mockSlots: CapacitySlot[] = [
  { id: 1, name: 'Alice Chen', type: 'ALGO', userId: 2, user: mockUsers[1], totalCapacity: 100, bindings: [], createdAt: '2024-01-01', updatedAt: '2024-01-01' },
  { id: 2, name: 'Bob Wang', type: 'ALGO', userId: 3, user: mockUsers[2], totalCapacity: 100, bindings: [], createdAt: '2024-01-01', updatedAt: '2024-01-01' },
  { id: 3, name: 'Charlie Liu', type: 'ALGO', totalCapacity: 100, bindings: [], createdAt: '2024-01-01', updatedAt: '2024-01-01' },
  { id: 4, name: 'External Vendor', type: 'EXTERNAL', userId: 4, user: mockUsers[3], totalCapacity: 50, bindings: [], createdAt: '2024-01-01', updatedAt: '2024-01-01' },
];

const mockDirections: WikiDirection[] = [
  { id: 1, name: 'Documentation', description: 'System guides', pages: [], createdAt: '2024-01-01', updatedAt: '2024-01-01' },
  { id: 2, name: 'Architecture', description: 'Technical architecture', pages: [], createdAt: '2024-01-01', updatedAt: '2024-01-01' },
];

export const mockApi = {
  getUsers: () => mockUsers,
  getTopics: () => mockTopics,
  getSlots: () => mockSlots,
  getTemplates: () => mockTemplates,
  getDirections: () => mockDirections,
  getCurrentUser: () => mockUsers[0],
};

export { mockUsers, mockTopics, mockSlots, mockTemplates, mockDirections };
