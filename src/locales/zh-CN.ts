// src/locales/zh-CN.ts
// 中文本地化字典

export const zhCN = {
  // 通用
  common: {
    save: '保存',
    cancel: '取消',
    delete: '删除',
    edit: '编辑',
    add: '添加',
    create: '创建',
    change: '更换',
    open: '打开',
    close: '关闭',
    back: '返回',
    confirm: '确认',
    search: '搜索',
    all: '全部',
    loading: '加载中...',
    noData: '暂无数据',
    success: '成功',
    failed: '失败',
    yes: '是',
    no: '否',
  },

  // 导航
  nav: {
    dashboard: '工作台',
    topics: '课题管理',
    capacity: '人力配置',
    wiki: '知识库',
    templates: '阶段模板',
    insights: '数据洞察',
    users: '用户管理',
    auditLogs: '操作日志',
    settings: '设置',
    logout: '退出登录',
  },

  // 课题相关
  topic: {
    topic: '课题',
    topics: '课题',
    uncertainty: '不确定性课题',
    evolution: '演进项目',
    createTopic: '创建课题',
    editTopic: '编辑课题',
    topicDetail: '课题详情',
    title: '标题',
    description: '描述',
    type: '类型',
    urgency: '优先级',
    result: '状态',
    requester: '需求方',
    externalRequester: '外部需求方',
    customer: '客户',
    dri: 'DRI（第一负责人）',
    owner: '负责人',
    changeDri: '更换负责人',
    // 状态
    open: '进行中',
    success: '已完成',
    unsolvable: '无法解决',
    // 类型
    uncertaintyType: '不确定性',
    evolutionType: '演进',
  },

  // 阶段相关
  stage: {
    stage: '阶段',
    stages: '阶段',
    stageProgress: '阶段进展',
    currentStage: '当前阶段',
    completed: '已完成',
    inProgress: '进行中',
    pending: '待开始',
    advance: '推进到下一阶段',
    goBack: '回退',
    goBackTo: '回退到之前阶段',
    terminal: '结束阶段',
    requiresDeliverable: '需要交付物',
    stageHistory: '阶段历史',
    // 阶段名称
    algorithmSubpc: '算法SubPC',
    acceptance: '验收',
  },

  // 交付物相关
  deliverable: {
    deliverable: '交付物',
    deliverables: '交付物',
    addDeliverable: '添加交付物',
    noDeliverables: '暂无交付物',
    name: '名称',
    type: '类型',
    link: '链接',
    file: '文件',
    url: '链接地址',
    description: '描述',
    quickTemplates: '快捷模板',
  },

  // 人力相关
  capacity: {
    slot: '人力',
    slots: '人力',
    algoSlot: '自有人力',
    algoSlots: '自有人力',
    externalSlot: '协调人力',
    externalSlots: '协调人力',
    binding: '分配',
    bindings: '人力分配',
    teamBindings: '团队成员',
    percentage: '分配比例',
    allocated: '已分配',
    totalAllocation: '总分配',
    addBinding: '添加人力',
    releaseBinding: '释放人力',
    forced: '强制分配',
    noDri: '暂未指定负责人',
    addBindingTip: '添加一个分配来指定负责人',
    noTeamMembers: '暂无其他团队成员',
    noAlgoSlots: '暂无自有人力',
    noExternalSlots: '暂无协调人力',
  },

  // 笔记和评审
  artifact: {
    notes: '笔记',
    artifacts: '笔记 & 记录',
    addNote: '添加笔记',
    noNotes: '暂无笔记',
  },

  review: {
    reviews: '评审',
    addReview: '添加评审',
    noReviews: '暂无评审',
  },

  // 统计
  stats: {
    quickStats: '快速统计',
    openTopics: '进行中课题',
    completed: '已完成',
    unsolvable: '无法解决',
    stagesCompleted: '已完成阶段',
  },

  // 仪表盘
  dashboard: {
    title: '工作台',
    dragSlotHint: '拖拽人力 → 放到课题上进行分配',
    dragBindingHint: '拖拽分配 → 放到右侧区域释放',
    noUncertaintyTopics: '暂无不确定性课题',
    noEvolutionTopics: '暂无演进项目',
    driIsMe: 'DRI=我',
  },

  // 关闭课题
  closure: {
    closure: '结题',
    markAsSuccess: '标记为完成',
    markAsUnsolvable: '标记为无法解决',
    confirmClosure: '确认结题',
    confirmSuccess: '确定将此课题标记为"已完成"？此操作不可撤销。',
    confirmUnsolvable: '确定将此课题标记为"无法解决"？此操作不可撤销。',
  },

  // 基本信息
  basicInfo: {
    title: '基本信息',
    id: '编号',
  },

  // 消息提示
  message: {
    created: '创建成功',
    updated: '更新成功',
    deleted: '删除成功',
    released: '已释放',
    advanced: '已推进到下一阶段',
    movedBack: '已回退到之前阶段',
    driChanged: '负责人已更换',
    deliverableAdded: '交付物已添加',
    deliverableDeleted: '交付物已删除',
    operationFailed: '操作失败',
    confirmDelete: '确认删除',
    deleteWarning: '此操作不可撤销',
  },

  // 用户相关
  user: {
    user: '用户',
    users: '用户',
    name: '姓名',
    email: '邮箱',
    role: '角色',
    admin: '管理员',
    member: '成员',
    reviewer: '评审员',
    external: '外部人员',
    customer: '客户',
  },

  // 登录
  login: {
    title: '登录',
    email: '邮箱',
    password: '密码',
    submit: '登录',
    loginFailed: '登录失败',
  },
};

export default zhCN;
