TCGS – Technical Collaboration & Governance System

TCGS 是一个面向技术团队的协作与治理系统，核心目标是：

把“课题 / 项目”与“人、阶段、产出、容量”放在同一个可视化系统中，
让技术工作从「隐性经验」变成「可管理结构」。

它并不是传统意义上的 Jira / Trello / Asana，而是更偏向 技术课题治理 + 人力容量管理 + 决策过程可追溯 的系统。

⸻

✨ 核心理念
	•	技术工作 ≠ 简单任务堆叠
	•	真正重要的是：
	•	课题从哪里来
	•	由谁负责
	•	经过了哪些阶段
	•	产出了什么
	•	消耗了多少真实能力

TCGS 尝试用结构化模型回答这些问题。

⸻

🧠 核心能力概览

1. Topic（课题 / 项目）治理

每一个 Topic 都不是“随便建一个任务”，而是一个有生命周期的技术对象：
	•	明确的 课题类型
	•	Uncertainty（探索型 / 不确定性）
	•	Evolution（演进型 / 工程推进）
	•	明确的 紧急程度（P0 / P1 / P2）
	•	明确的 DRI（Directly Responsible Individual）
	•	明确的 委托人 / 来源人（Requester）
	•	可绑定系统内 CUSTOMER 用户
	•	也可记录外部 / 未注册委托人（仅记录名称，不绑定账号）

⸻

2. Stage Workflow（阶段化流程）

每个 Topic 绑定一个 阶段模板（Stage Template），例如：
	•	Definition → Analysis → Implementation → Closure
	•	POC / 快速验证流程等

系统能力包括：
	•	当前所处阶段可视化
	•	阶段推进（Advance）
	•	每个阶段的状态记录（pending / active / done）
	•	阶段是否要求产出（Artifact）
	•	终态阶段是否允许结论（Result）

这使得“项目进行到哪一步”不再靠口头同步。

⸻

3. Artifact & Review（产出与评审）
	•	每个阶段可以产生 Artifact
	•	文档
	•	方案说明
	•	实现结果
	•	支持 Review 评论
	•	所有操作都有用户与时间记录

👉 形成可回溯的技术决策链路。

4. Capacity（能力 / 人力槽位）

TCGS 引入了一个核心概念：Capacity Slot
	•	Algo / External 等不同类型槽位
	•	每个槽位有总容量（例如 100%）
	•	Topic 可绑定容量
	•	用于表达：
	•	谁在被占用
	•	占用强度如何
	•	是否已超载

这不是 HR 系统，而是 工程现实世界的能力建模。

⸻

5. 用户角色与权限模型

系统内置多角色体系：
| **角色**     | **说明**                      |
| ------------ | ----------------------------- |
| Admin        | 系统管理、用户管理、全权限    |
| Member       | 技术成员，可创建和推进课题    |
| Reviewer     | 评审角色                      |
| External     | 外部协作者（有限能力）        |
| **Customer** | **委托人 / 需求方，只读浏览** |

Customer 角色特点：
	•	❌ 不能创建 / 修改 Topic
	•	❌ 不能推进阶段、创建 Artifact
	•	❌ 不能绑定 Capacity
	•	✅ 可以登录系统
	•	✅ 可以查看自己相关的 Topic
	•	✅ 作为 Topic 的“委托人 / 来源人”被记录

⸻

🖥️ 前端功能
	•	Dashboard：
	•	不同类型 Topic 池
	•	当前阶段可视化（Stage Timeline）
	•	容量槽位概览
	•	Topic 列表 & 详情页
	•	Topic 创建 / 编辑（权限控制）
	•	User Management（用户管理）
	•	Capacity 管理

技术栈：
	•	Vue 3 + TypeScript
	•	Element Plus
	•	Pinia
	•	Vite

⸻

⚙️ 后端架构
	•	Python + FastAPI
	•	SQLAlchemy
	•	PostgreSQL
	•	Alembic（数据库迁移）
	•	JWT 鉴权
	•	Docker / Docker Compose

后端关注点：
	•	严格的权限校验（前后端双层）
	•	数据模型与业务规则强一致
	•	所有关键行为可审计

⸻

🗄️ 数据库设计亮点
	•	Enum 级别的角色与状态约束
	•	Topic ↔ Stage ↔ Artifact 结构化关系
	•	Requester 与 User 解耦（支持未注册委托人）
	•	Capacity 与 User 绑定但不强制

⸻

🚀 快速启动
```
docker compose up -d --build
```

默认会启动：
	•	PostgreSQL
	•	Backend API
	•	Frontend
	•	MinIO（文件存储）

🎯 适用场景
	•	技术团队课题治理
	•	复杂工程项目推进
	•	探索型研发 / POC 管理
	•	需要“对外可解释”的技术团队
	•	希望把经验沉淀为系统能力的组织
🧩 系统边界（刻意不做的事）
	•	❌ 不做工时打卡
	•	❌ 不做 KPI 评分
	•	❌ 不替代代码管理工具
	•	❌ 不追求流程复杂化

TCGS 更关心的是：

结构是否清晰、责任是否明确、过程是否可追溯。


## License

MIT License
