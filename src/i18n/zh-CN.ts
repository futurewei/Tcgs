// src/i18n/zh-CN.ts
// 中文语言包

export const zhCN = {
  // 通用
  common: {
    confirm: '确认',
    cancel: '取消',
    save: '保存',
    delete: '删除',
    edit: '编辑',
    add: '添加',
    open: '打开',
    back: '返回',
    search: '搜索',
    filter: '筛选',
    all: '全部',
    loading: '加载中...',
    noData: '暂无数据',
    success: '成功',
    failed: '失败',
    required: '必填',
    optional: '选填',
    actions: '操作',
    status: '状态',
    type: '类型',
    name: '名称',
    description: '描述',
    createdAt: '创建时间',
    updatedAt: '更新时间',
  },

  // 导航
  nav: {
    dashboard: '工作台',
    topics: '课题管理',
    capacity: '人力管理',
    wiki: '知识库',
    insights: '数据洞察',
    audit: '操作日志',
    users: '用户管理',
  },

  // 用户角色
  role: {
    ADMIN: '管理员',
    MEMBER: '算法成员',
    REVIEWER: '评审员',
    EXTERNAL: '协调人力',
    CUSTOMER_INTERNAL: '需求方(PDU内)',
    CUSTOMER_EXTERNAL: '需求方(PDU外)',
  },

  // 课题 (Topic)
  topic: {
    title: '课题',
    topics: '课题列表',
    uncertainty: '不确定性课题',
    evolution: '演进课题',
    create: '创建课题',
    edit: '编辑课题',
    delete: '删除课题',
    detail: '课题详情',
    
    // 字段
    id: '课题编号',
    name: '课题名称',
    desc: '课题描述',
    urgency: '优先级',
    result: '结果状态',
    dri: 'DRI (负责人)',
    requester: '需求方',
    stage: '当前阶段',
    template: '流程模板',
    bindings: '人力分配',
    deliverables: '交付物',
    
    // 类型
    types: {
      UNCERTAINTY: '不确定性',
      EVOLUTION: '演进',
    },
    
    // 优先级
    urgencies: {
      P0: 'P0 (紧急)',
      P1: 'P1 (高)',
      P2: 'P2 (中)',
      P3: 'P3 (低)',
    },
    
    // 结果
    results: {
      OPEN: '进行中',
      SUCCESS: '已完成',
      UNSOLVABLE: '无法解决',
    },

    // 操作
    advanceStage: '推进到下一阶段',
    backwardStage: '回退阶段',
    goBack: '回退',
    changeDri: '更换负责人',
    markSuccess: '标记为成功',
    markUnsolvable: '标记为无法解决',
    
    // 筛选
    filterDriMe: 'DRI=我',
    
    // 消息
    created: '课题创建成功',
    updated: '课题更新成功',
    deleted: '课题删除成功',
    stageAdvanced: '已推进到下一阶段',
    stageBackward: '已回退到上一阶段',
    driChanged: '负责人已更换',
    
    // 空状态
    noTopics: '暂无课题',
    noUncertainty: '暂无不确定性课题',
    noEvolution: '暂无演进课题',
  },

  // 阶段 (Stage)
  stage: {
    title: '阶段',
    stages: '阶段列表',
    progress: '阶段进度',
    history: '阶段历史',
    
    // 状态
    statuses: {
      pending: '待开始',
      active: '进行中',
      done: '已完成',
    },
    
    // 标记
    terminal: '终止阶段',
    requireArtifact: '需要交付物',
    allowResult: '允许设置结果',
    
    // 操作
    selectStage: '选择要回退的阶段',
    completed: '已完成',
    inProgress: '进行中',
  },

  // 人力 (Capacity)
  capacity: {
    title: '人力管理',
    slots: '人力槽位',
    bindings: '人力分配',
    
    // Slot 类型
    algo: '自有人力',
    external: '协调人力',
    
    // 字段
    slotName: '人员名称',
    slotType: '人员类型',
    totalCapacity: '总容量',
    usedCapacity: '已使用',
    remainingCapacity: '剩余',
    percentage: '分配比例',
    
    // 操作
    createSlot: '添加人员',
    editSlot: '编辑人员',
    deleteSlot: '删除人员',
    addBinding: '分配人力',
    removeBinding: '释放人力',
    
    // 状态
    available: '可用',
    partial: '部分占用',
    occupied: '已满',
    overloaded: '超载',
    forced: '强制分配',
    
    // 消息
    slotCreated: '人员添加成功',
    slotUpdated: '人员更新成功',
    slotDeleted: '人员删除成功',
    bindingCreated: '人力分配成功',
    bindingDeleted: '人力释放成功',
    released: '已释放',
    exceedsCapacity: '超出容量，请使用强制分配',
    
    // 空状态
    noSlots: '暂无人员',
    noAlgoSlots: '暂无自有人力',
    noExternalSlots: '暂无协调人力',
    noBindings: '暂无人力分配',
  },

  // DRI
  dri: {
    title: 'DRI (负责人)',
    owner: '课题负责人',
    change: '更换负责人',
    current: '当前负责人',
    new: '新负责人',
    noDri: '暂无负责人',
    addBindingFirst: '请先分配人力以指定负责人',
    selectFromBindings: '从已分配人员中选择',
    addNewPerson: '添加新人员',
    allocated: '已分配',
    totalAllocation: '总分配量',
  },

  // 交付物 (Deliverable)
  deliverable: {
    title: '交付物',
    deliverables: '交付物列表',
    add: '添加交付物',
    delete: '删除交付物',
    
    // 类型
    types: {
      link: '链接',
      file: '文件',
    },
    
    // 字段
    name: '名称',
    url: '链接地址',
    desc: '描述',
    fileName: '文件名',
    fileSize: '文件大小',
    
    // 快捷模板
    quickLinks: '快捷链接',
    feishuDoc: '飞书文档',
    confluence: 'Confluence',
    notion: 'Notion',
    github: 'GitHub',
    figma: 'Figma',
    
    // 消息
    created: '交付物添加成功',
    deleted: '交付物删除成功',
    
    // 空状态
    noDeliverables: '暂无交付物',
  },

  // 笔记/评审
  artifact: {
    title: '笔记',
    notes: '笔记与备注',
    add: '添加笔记',
    noNotes: '暂无笔记',
  },
  
  review: {
    title: '评审',
    reviews: '评审记录',
    add: '添加评审',
    noReviews: '暂无评审',
  },

  // Dashboard
  dashboard: {
    title: '工作台',
    quickStats: '快速统计',
    openTopics: '进行中课题',
    completed: '已完成',
    unsolvable: '无法解决',
    dragHint: {
      assign: '拖动人员到课题上进行分配',
      release: '拖动分配块到右侧释放人力',
    },
  },

  // 洞察
  insights: {
    title: '数据洞察',
    kpi: '关键指标',
    throughput: '吞吐量趋势',
    personLoad: '人员负载',
    externalCollab: '协调人力分布',
  },

  // 审计日志
  audit: {
    title: '操作日志',
    logs: '日志列表',
    actions: {
      TOPIC_CREATE: '创建课题',
      TOPIC_UPDATE: '更新课题',
      TOPIC_DELETE: '删除课题',
      DRI_CHANGE: '更换负责人',
      RESULT_CHANGE: '修改结果',
      STAGE_CHANGE: '阶段变更',
      SLOT_CREATE: '添加人员',
      SLOT_UPDATE: '更新人员',
      SLOT_DELETE: '删除人员',
      BINDING_CREATE: '分配人力',
      BINDING_UPDATE: '更新分配',
      BINDING_DELETE: '释放人力',
      BINDING_FORCE: '强制分配',
      USER_CREATE: '创建用户',
      USER_UPDATE: '更新用户',
      USER_DELETE: '删除用户',
      WIKI_CREATE: '创建文档',
      WIKI_UPDATE: '更新文档',
    },
  },

  // 用户
  user: {
    title: '用户管理',
    users: '用户列表',
    create: '创建用户',
    edit: '编辑用户',
    delete: '删除用户',
    email: '邮箱',
    name: '姓名',
    role: '角色',
    password: '密码',
    
    // 消息
    created: '用户创建成功',
    updated: '用户更新成功',
    deleted: '用户删除成功',
  },

  // 认证
  auth: {
    login: '登录',
    logout: '退出登录',
    email: '邮箱',
    password: '密码',
    rememberMe: '记住我',
    forgotPassword: '忘记密码？',
    loginSuccess: '登录成功',
    loginFailed: '登录失败',
    logoutSuccess: '已退出登录',
  },

  // 知识库
  wiki: {
    title: '知识库',
    directions: '方向分类',
    pages: '文档页面',
    createPage: '创建文档',
    editPage: '编辑文档',
    noPages: '暂无文档',
  },

  // 流程模板
  template: {
    title: '流程模板',
    templates: '模板列表',
    stages: '阶段配置',
    
    // 默认阶段
    defaultStages: {
      problemDefinition: '问题定义',
      research: '调研分析',
      design: '方案设计',
      implementation: '开发实现',
      testing: '测试验证',
      algoSubpc: '算法SubPC',
      acceptance: '验收',
    },
  },

  // 错误消息
  error: {
    unknown: '发生未知错误',
    network: '网络连接失败',
    unauthorized: '未授权，请重新登录',
    forbidden: '没有权限执行此操作',
    notFound: '资源不存在',
    validation: '表单验证失败',
  },

  // 确认对话框
  confirm: {
    delete: '确认删除？',
    deleteDesc: '此操作不可撤销。',
    close: '确认关闭？',
    closeDesc: '此操作是最终的。',
    unsavedChanges: '有未保存的更改，确认离开？',
  },
};

export default zhCN;
