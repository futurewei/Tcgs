# TCGS 项目技术架构报告

## 目录
1. [技术演进：从石器时代到现代Web](#1-技术演进从石器时代到现代web)
2. [项目概述与技术栈总览](#2-项目概述与技术栈总览)
3. [数据存储演进：SQL、PostgreSQL 与关系型数据库](#3-数据存储演进sqlpostgresql-与关系型数据库)
4. [后端框架之争：FastAPI vs Java Spring Boot](#4-后端框架之争fastapi-vs-java-spring-boot)
5. [数据库迁移：Alembic 的前世今生](#5-数据库迁移alembic-的前世今生)
6. [前端架构：Vue 3 与 Pinia 状态管理](#6-前端架构vue-3-与-pinia-状态管理)
7. [容器化革命：Docker 如何解决依赖地狱](#7-容器化革命docker-如何解决依赖地狱)
8. [反向代理：为什么需要 Nginx](#8-反向代理为什么需要-nginx)
9. [对象存储：MinIO 是什么](#9-对象存储minio-是什么)
10. [系统架构图与请求流转](#10-系统架构图与请求流转)
11. [Vue 响应式原理](#11-vue-响应式原理)
12. [4+1 视图模型](#12-41-视图模型)

---

## 1. 技术演进：从石器时代到现代Web

要理解现代 Web 技术栈的设计，我们需要先回顾一下 Web 开发的演进历程。这不仅能帮助我们理解"为什么需要这些技术"，还能让我们明白它们各自解决了什么问题。

### 1.1 石器时代：静态 HTML (1990s 初期)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    1990年代初期：静态网页时代                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   用户请求                        服务器响应                            │
│   ─────────                       ─────────                             │
│   GET /index.html    ──────▶     返回 index.html 文件                  │
│                                                                         │
│   特点:                                                                 │
│   - 所有内容都是写死的 HTML 文件                                        │
│   - 没有数据库，信息直接写在文件里                                      │
│   - 每次更新内容都要手动编辑 HTML 文件                                  │
│   - 没有用户登录、没有个性化内容                                        │
│                                                                         │
│   示例网站结构:                                                         │
│   /var/www/html/                                                        │
│   ├── index.html         ← 首页                                         │
│   ├── about.html         ← 关于页面                                     │
│   ├── contact.html       ← 联系页面                                     │
│   └── images/                                                           │
│       └── logo.gif                                                      │
│                                                                         │
│   问题: 如果要显示1000个产品，就要创建1000个HTML文件！                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 青铜时代：CGI 动态网页 (1990s 中后期)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CGI (Common Gateway Interface) 时代                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   革命性突破: 网页内容可以由程序动态生成！                              │
│                                                                         │
│   工作流程:                                                             │
│   ┌────────┐     ┌────────┐     ┌────────────┐     ┌────────┐          │
│   │ 浏览器 │────▶│ Web服务器│────▶│ Perl/C程序 │────▶│ 数据库 │          │
│   └────────┘     └────────┘     └────────────┘     └────────┘          │
│        │                              │                                 │
│        │◀─────── HTML字符串 ──────────┘                                 │
│                                                                         │
│   示例 Perl CGI 脚本:                                                   │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  #!/usr/bin/perl                                                │  │
│   │  print "Content-type: text/html\n\n";                           │  │
│   │  print "<html><body>";                                          │  │
│   │  print "当前时间: " . localtime();                               │  │
│   │  print "</body></html>";                                        │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   问题:                                                                 │
│   - 每个请求都要启动一个新进程，性能极差                               │
│   - 代码和 HTML 混在一起，难以维护                                      │
│   - 安全漏洞多（SQL注入、命令注入）                                     │
│   - 没有会话管理，每个请求都是独立的                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 铁器时代：PHP/JSP/ASP 与 MVC 框架 (2000s)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    服务端渲染 + MVC 架构时代                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   什么是 MVC？                                                          │
│   ───────────                                                           │
│   MVC (Model-View-Controller) 是一种软件架构模式，将应用程序分成三个    │
│   相互关联但职责分离的部分：                                            │
│                                                                         │
│   • Model (模型层):                                                     │
│     - 负责数据和业务逻辑                                                │
│     - 与数据库交互，定义数据结构                                        │
│     - 例如: User 类定义用户有哪些属性，如何保存到数据库                 │
│                                                                         │
│   • View (视图层):                                                      │
│     - 负责展示数据给用户                                                │
│     - 不包含业务逻辑，只负责"长什么样"                                 │
│     - 例如: HTML 模板、JSP 页面                                         │
│                                                                         │
│   • Controller (控制层):                                                │
│     - 负责接收用户请求，协调 Model 和 View                              │
│     - 处理业务流程：收到请求 → 调用Model获取数据 → 选择View渲染        │
│     - 例如: UserController 处理 /users 请求                             │
│                                                                         │
│   为什么需要 MVC？                                                      │
│   ───────────────                                                       │
│   没有 MVC 之前，所有代码混在一起：                                     │
│   - HTML 里嵌 PHP，PHP 里写 SQL，SQL 旁边是 CSS...                      │
│   - 改个按钮颜色可能破坏数据库查询                                      │
│   - 想换个数据库？整个文件都要改                                        │
│                                                                         │
│   MVC 的好处：                                                          │
│   - 关注点分离: 改 UI 不影响业务逻辑，改数据库不影响页面                │
│   - 代码复用: 同一个 Model 可以给多个 View 用                           │
│   - 团队协作: 前端改 View，后端改 Model/Controller，互不干扰            │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   关键进步:                                                             │
│   1. PHP/JSP/ASP 等语言可以嵌入在 HTML 中                               │
│   2. MVC 模式分离了数据、逻辑和展示                                     │
│   3. ORM 出现，不用手写 SQL                                             │
│   4. 框架出现: Struts, Spring, Rails, Django                           │
│                                                                         │
│   MVC 模式示意:                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                 │  │
│   │   ┌───────────┐      ┌────────────┐      ┌───────────┐         │  │
│   │   │   Model   │◀────▶│ Controller │◀────▶│   View    │         │  │
│   │   │  (数据)   │      │   (逻辑)   │      │  (展示)   │         │  │
│   │   └───────────┘      └────────────┘      └───────────┘         │  │
│   │        │                   │                   │                │  │
│   │        ▼                   ▼                   ▼                │  │
│   │   User.java          UserController    user_list.jsp           │  │
│   │   Topic.java         TopicController   topic_detail.jsp        │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   Java Servlet 示例 (2000年代风格):                                     │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  // ========== Controller 层 ==========                         │  │
│   │  @WebServlet("/users")                                          │  │
│   │  public class UserServlet extends HttpServlet {                 │  │
│   │      protected void doGet(HttpServletRequest req,               │  │
│   │                           HttpServletResponse resp) {           │  │
│   │          // 调用 Model 层获取数据                                │  │
│   │          List<User> users = userDao.findAll();                  │  │
│   │          req.setAttribute("users", users);                      │  │
│   │          // 转发给 View 层渲染                                   │  │
│   │          req.getRequestDispatcher("/users.jsp")                 │  │
│   │             .forward(req, resp);                                │  │
│   │      }                                                          │  │
│   │  }                                                              │  │
│   │                                                                 │  │
│   │  // ========== Model 层 (User.java) ==========                  │  │
│   │  public class User {                                            │  │
│   │      private Long id;                                           │  │
│   │      private String name;                                       │  │
│   │      private String email;                                      │  │
│   │      // getters, setters...                                     │  │
│   │  }                                                              │  │
│   │                                                                 │  │
│   │  // ========== View 层 (users.jsp) ==========                   │  │
│   │  <html>                                                         │  │
│   │  <body>                                                         │  │
│   │    <h1>用户列表</h1>                                            │  │
│   │    <c:forEach items="${users}" var="user">                      │  │
│   │      <p>${user.name} - ${user.email}</p>                        │  │
│   │    </c:forEach>                                                 │  │
│   │  </body>                                                        │  │
│   │  </html>                                                        │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   问题:                                                                 │
│   - 服务端渲染，每次操作都要刷新整个页面                                │
│   - 前后端代码耦合严重                                                  │
│   - 部署复杂（Tomcat/WebLogic 配置繁琐）                                │
│   - 扩展困难，单体应用越来越臃肿                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.4 工业时代：前后端分离 + SPA (2010s)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    前后端分离 + 单页应用 (SPA) 时代                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   革命性变化:                                                           │
│   1. 前端不再只是"模板"，而是独立的应用                                │
│   2. 后端只提供数据 API (JSON)，不管页面渲染                            │
│   3. AJAX/Fetch 实现局部刷新，用户体验大幅提升                          │
│   4. 前后端可以独立开发、独立部署                                       │
│                                                                         │
│   架构对比:                                                             │
│                                                                         │
│   传统服务端渲染:                      前后端分离:                      │
│   ─────────────────                    ────────────                      │
│   浏览器 ──▶ 服务器                    浏览器 ──▶ 静态服务器 (HTML/JS)  │
│              │                                      │                   │
│              ▼                                      ▼ (AJAX)            │
│         渲染完整HTML                           API 服务器 (JSON)        │
│              │                                      │                   │
│              ▼                                      ▼                   │
│         返回HTML                               返回数据                 │
│                                                     │                   │
│                                                     ▼                   │
│                                               前端渲染 DOM              │
│                                                                         │
│   关键技术栈演进:                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                 │  │
│   │   2010: jQuery + Backbone.js                                    │  │
│   │   2013: AngularJS (Google)                                      │  │
│   │   2014: React (Facebook)                                        │  │
│   │   2014: Vue.js (尤雨溪)                                          │  │
│   │   2016: Vue 2.0 + Vuex                                          │  │
│   │   2020: Vue 3.0 + Pinia (Composition API)                       │  │
│   │                                                                 │  │
│   │   后端 API 框架:                                                 │  │
│   │   2010: Express.js (Node.js)                                    │  │
│   │   2014: Spring Boot (简化 Spring)                               │  │
│   │   2018: FastAPI (Python, 异步, 类型提示)                         │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.5 现代：云原生与容器化 (2020s)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    云原生 + 容器化 + 微服务时代                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   现代 Web 应用面临的挑战 (详解):                                       │
│   ─────────────────────────────                                         │
│                                                                         │
│   1. "在我机器上能跑" 问题                                              │
│      ─────────────────────────                                          │
│      场景: 开发者 A 用 Python 3.9，开发者 B 用 Python 3.11              │
│            生产服务器是 Python 3.8，某个库只支持 3.9+                   │
│      痛点: 代码在 A 电脑上跑得好好的，部署到服务器就报错                │
│            "但是在我机器上能跑啊！" ← 经典名言                          │
│      解决: Docker 容器把代码+依赖+环境打包成一个镜像                    │
│            在哪都是同一个环境，彻底消除"环境差异"问题                  │
│                                                                         │
│   2. 手动部署易出错问题                                                 │
│      ────────────────────                                               │
│      场景: 每次部署需要: SSH登录 → 拉代码 → 装依赖 → 改配置 → 重启服务 │
│      痛点: 步骤多、容易漏掉一步；不同人部署方式不一样                   │
│            凌晨 3 点紧急修 bug，手忙脚乱操作失误导致线上崩溃            │
│      解决: CI/CD 自动化流水线，git push 自动触发部署                    │
│            Docker Compose 一个命令启动所有服务，操作标准化              │
│                                                                         │
│   3. 数据库结构变更混乱                                                 │
│      ──────────────────                                                 │
│      场景: 开发者 A 加了个字段，开发者 B 不知道，直接拉代码跑报错       │
│            线上数据库是谁改的？改了什么？能回滚吗？                     │
│      痛点: 数据库变更没有记录，出问题无法追溯                           │
│            多人开发时数据库结构冲突，手动 SQL 容易写错                  │
│      解决: Alembic/Flyway 把数据库变更写成"迁移脚本"                   │
│            每次变更都有版本号，可追溯、可回滚、可自动执行               │
│                                                                         │
│   4. 前端状态管理复杂                                                   │
│      ──────────────────                                                 │
│      场景: 用户登录状态要在 20 个组件里用；购物车数据要在 10 个页面同步 │
│      痛点: 数据散落在各个组件里，改一处忘改另一处                       │
│            组件之间传数据像"击鼓传花"，中间组件被迫接收它不需要的数据 │
│      解决: Pinia/Redux 把共享状态集中管理                               │
│            任何组件都能直接访问和修改，数据源唯一，不会不一致           │
│                                                                         │
│   5. API 文档维护困难                                                   │
│      ──────────────────                                                 │
│      场景: 后端改了接口参数，忘记更新文档；前端按旧文档开发，联调时炸了 │
│      痛点: 文档和代码分离，文档永远是"上个版本"的                      │
│            前后端扯皮："你文档写的是这样" "我代码改了你没看到吗"       │
│      解决: FastAPI/Swagger 从代码自动生成文档                           │
│            代码即文档，改代码文档自动更新，永远同步                     │
│                                                                         │
│   6. 文件存储分散                                                       │
│      ──────────────                                                     │
│      场景: 用户上传的头像、文档、附件存在服务器本地                     │
│      痛点: 服务器扩容到多台时，文件只在其中一台，其他服务器访问不到     │
│            服务器硬盘满了怎么办？文件备份怎么做？                       │
│      解决: MinIO/S3 提供统一的文件存储服务                              │
│            所有服务器都从同一个地方读写文件，支持 CDN、备份、扩容       │
│                                                                         │
│   7. 跨域、负载均衡问题                                                 │
│      ──────────────────                                                 │
│      场景: 前端 localhost:3000，后端 localhost:8000，浏览器拦截请求     │
│            用户量大了，一台服务器扛不住                                 │
│      痛点: 跨域配置繁琐，每个后端服务都要配一遍                         │
│            静态文件和 API 混在一起，无法分别优化                        │
│      解决: Nginx 作为统一入口，反向代理解决跨域                         │
│            静态文件直接返回，API 请求转发给后端，各司其职               │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   TCGS 项目采用的现代技术栈:                                            │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                 │  │
│   │   问题                    │  解决方案                           │  │
│   │   ────────────────────────│───────────────────────────────────  │  │
│   │   前端 UI                 │  Vue 3 + TypeScript                 │  │
│   │   前端状态管理            │  Pinia                              │  │
│   │   后端 API                │  FastAPI + Pydantic                 │  │
│   │   数据持久化              │  PostgreSQL + SQLAlchemy            │  │
│   │   数据库版本控制          │  Alembic                            │  │
│   │   文件存储                │  MinIO (S3 兼容)                    │  │
│   │   反向代理 + 静态服务     │  Nginx                              │  │
│   │   环境一致性              │  Docker + Docker Compose            │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   这就是为什么我们需要这么多技术——每个都在解决特定的工程问题！          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.6 技术选型的核心原则

在理解了技术演进后，我们的技术选型遵循以下原则：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       技术选型核心原则                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   1. 解决实际问题，而非追求时髦                                         │
│      ─────────────────────────────                                      │
│      - Vue 3: 成熟稳定，中文社区活跃，学习曲线平缓                      │
│      - FastAPI: Python 生态丰富，AI/算法团队熟悉                        │
│      - PostgreSQL: 开源免费，功能强大，生产级稳定                       │
│                                                                         │
│   2. 开发效率与运行效率的平衡                                           │
│      ─────────────────────────────                                      │
│      - Python 写起来快，FastAPI 运行性能接近 Go                         │
│      - TypeScript 有类型检查，减少运行时错误                            │
│      - Docker 一次配置，处处运行                                        │
│                                                                         │
│   3. 团队技能与技术匹配                                                 │
│      ─────────────────────                                              │
│      - 算法团队熟悉 Python → FastAPI                                    │
│      - 前端工程师熟悉 Vue → Vue 3                                       │
│      - 运维熟悉 Docker → 容器化部署                                     │
│                                                                         │
│   4. 可维护性与可扩展性                                                 │
│      ─────────────────────                                              │
│      - Alembic 管理数据库变更，可追溯可回滚                             │
│      - Pinia 管理前端状态，逻辑清晰                                     │
│      - Docker Compose 定义服务依赖，一键部署                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 项目概述与技术栈总览

### 2.1 项目简介

**TCGS (Topic & Capability Governance System)** 是一个算法能力管理平台，用于组织研发工作流程。核心功能包括：

- **课题管理 (Topics)**: 管理研究课题的完整生命周期
- **阶段管理 (Stages)**: 工作流阶段推进和交付物追踪
- **产能管理 (Capacity)**: 人员和资源分配
- **知识库 (Wiki)**: 文档和知识沉淀
- **洞察分析 (Insights)**: KPI 统计和分析

### 2.2 技术栈总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                          技术栈架构                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    前端 (Frontend)                           │   │
│   │  Vue 3 + TypeScript + Pinia + Vue Router + Element Plus     │   │
│   │  TailwindCSS + Vite + Axios                                 │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    反向代理 (Proxy)                          │   │
│   │                    Nginx Alpine                              │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    后端 (Backend)                            │   │
│   │  FastAPI + SQLAlchemy + Pydantic + Alembic + JWT            │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│              ┌───────────────┼───────────────┐                       │
│              ▼                               ▼                       │
│   ┌─────────────────────┐         ┌─────────────────────┐           │
│   │   PostgreSQL 15     │         │   MinIO (S3存储)     │           │
│   │   关系型数据库       │         │   文件对象存储       │           │
│   └─────────────────────┘         └─────────────────────┘           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 技术组件清单

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **前端框架** | Vue.js | 3.5.13 | 响应式 UI 框架 |
| **类型系统** | TypeScript | 5.7.2 | 静态类型检查 |
| **状态管理** | Pinia | 3.0.4 | 全局状态管理 |
| **路由** | Vue Router | 4.x | SPA 路由 |
| **UI 组件库** | Element Plus | 2.13.1 | 企业级 UI 组件 |
| **CSS 框架** | TailwindCSS | 4.1.10 | 原子化 CSS |
| **构建工具** | Vite | 6.4.1 | 快速开发服务器和构建 |
| **HTTP 客户端** | Axios | 1.13.2 | API 请求 |
| **后端框架** | FastAPI | 0.115.0 | 异步 Python Web 框架 |
| **ORM** | SQLAlchemy | 2.0.35 | 对象关系映射 |
| **数据验证** | Pydantic | 2.9.2 | 数据校验和序列化 |
| **数据库迁移** | Alembic | 1.13.2 | 数据库版本控制 |
| **数据库** | PostgreSQL | 15 | 关系型数据库 |
| **文件存储** | MinIO | latest | S3 兼容对象存储 |
| **Web 服务器** | Nginx | Alpine | 反向代理和静态文件服务 |
| **容器化** | Docker | Compose | 应用容器化部署 |

---

## 3. 数据存储演进：SQL、PostgreSQL 与关系型数据库

很多初学者会问：**SQL 和 PostgreSQL 是什么关系？MySQL、SQLite 又是什么？** 这一章我们来彻底搞清楚这些概念。

### 3.1 SQL 是一种语言，不是数据库

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    核心概念澄清                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   SQL (Structured Query Language) = 结构化查询语言                      │
│   ─────────────────────────────────────────────────                     │
│   - SQL 是一种"语言"，就像 Python、Java 是编程语言一样                 │
│   - SQL 专门用来操作数据库：查询、插入、更新、删除数据                  │
│   - SQL 本身不存储数据，它只是告诉数据库"要做什么"                      │
│                                                                         │
│   类比:                                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │   SQL 语言  ←→  中文/英文                                        │  │
│   │   数据库系统 ←→  使用这种语言的国家/地区                          │  │
│   │                                                                 │  │
│   │   你说"请给我一杯水"(SQL语句)                                   │  │
│   │   不同的服务员(数据库)都能理解，但可能有口音差异(方言/扩展)      │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   常见的关系型数据库系统 (都使用 SQL 语言):                             │
│   ─────────────────────────────────────────                             │
│   ┌─────────────┬────────────────────────────────────────────────────┐ │
│   │ 数据库系统  │ 特点                                               │ │
│   ├─────────────┼────────────────────────────────────────────────────┤ │
│   │ PostgreSQL  │ 功能最强大，完全开源，企业级                       │ │
│   │ MySQL       │ 最流行，Oracle 旗下，Web 应用常用                  │ │
│   │ SQLite      │ 轻量级，单文件，嵌入式应用                         │ │
│   │ Oracle      │ 商业数据库，银行/电信等大企业使用                  │ │
│   │ SQL Server  │ 微软产品，Windows 生态                             │ │
│   └─────────────┴────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 SQL 语言基础示例

```sql
-- SQL 是所有关系型数据库通用的语言
-- 以下语句在 PostgreSQL、MySQL、SQLite 中都能运行

-- 1. 创建表 (定义数据结构)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,          -- 自增主键
    email VARCHAR(255) NOT NULL,    -- 邮箱，不能为空
    name VARCHAR(100),              -- 姓名
    created_at TIMESTAMP DEFAULT NOW()  -- 创建时间，默认当前时间
);

-- 2. 插入数据
INSERT INTO users (email, name) VALUES ('zhang@example.com', '张三');
INSERT INTO users (email, name) VALUES ('li@example.com', '李四');

-- 3. 查询数据
SELECT * FROM users;                           -- 查询所有用户
SELECT name, email FROM users WHERE id = 1;    -- 查询 id=1 的用户
SELECT * FROM users ORDER BY created_at DESC;  -- 按创建时间倒序

-- 4. 更新数据
UPDATE users SET name = '张三丰' WHERE id = 1;

-- 5. 删除数据
DELETE FROM users WHERE id = 2;

-- 6. 关联查询 (SQL 的精髓)
SELECT topics.title, users.name as author
FROM topics
JOIN users ON topics.user_id = users.id
WHERE topics.status = 'OPEN';
```

### 3.3 为什么选择 PostgreSQL？

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PostgreSQL vs MySQL 详细对比                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   特性对比:                                                             │
│   ┌─────────────────┬────────────────────┬────────────────────┐        │
│   │ 特性            │ PostgreSQL         │ MySQL              │        │
│   ├─────────────────┼────────────────────┼────────────────────┤        │
│   │ JSON 支持       │ 原生 JSONB，可索引 │ JSON 类型，较弱    │        │
│   │ 全文搜索        │ 内置，功能强大     │ 需要插件           │        │
│   │ 事务隔离        │ 完整 ACID          │ 取决于存储引擎     │        │
│   │ 扩展性          │ 可编写自定义函数   │ 有限               │        │
│   │ 标准符合度      │ 最接近 SQL 标准    │ 有较多非标准扩展   │        │
│   │ 复杂查询        │ 窗口函数、CTE 强大 │ 8.0 后才完善       │        │
│   │ 开源协议        │ PostgreSQL License │ GPL (Oracle 控制)  │        │
│   └─────────────────┴────────────────────┴────────────────────┘        │
│                                                                         │
│   TCGS 项目选择 PostgreSQL 的理由:                                      │
│   ─────────────────────────────────                                     │
│   1. JSONB 支持: 课题的阶段配置、成功标准等都是 JSON 格式               │
│      stages = Column(JSONB)  # 可以直接存储复杂的嵌套结构               │
│                                                                         │
│   2. 全文搜索: Wiki 知识库需要搜索功能，PostgreSQL 内置支持             │
│      SELECT * FROM wiki_pages                                           │
│      WHERE to_tsvector('chinese', content) @@ to_tsquery('算法');       │
│                                                                         │
│   3. 完全开源: 不受商业公司控制，社区活跃                               │
│                                                                         │
│   4. 云服务支持: AWS RDS、阿里云、腾讯云都提供托管服务                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.4 ORM：让代码操作数据库更优雅

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    什么是 ORM？                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ORM = Object-Relational Mapping (对象关系映射)                        │
│                                                                         │
│   问题: 直接写 SQL 有什么不好？                                         │
│   ─────────────────────────────                                         │
│                                                                         │
│   # 传统方式: 手写 SQL (容易出错，难以维护)                             │
│   cursor.execute("""                                                    │
│       INSERT INTO users (email, name, created_at)                       │
│       VALUES (%s, %s, %s)                                               │
│   """, (email, name, datetime.now()))                                   │
│   # 问题: SQL 注入风险、字符串拼接繁琐、IDE 无法检查                    │
│                                                                         │
│   # ORM 方式: 用 Python 对象操作                                        │
│   user = User(email=email, name=name)                                   │
│   db.add(user)                                                          │
│   db.commit()                                                           │
│   # 优势: 类型安全、IDE 补全、自动防 SQL 注入                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**TCGS 项目中的 SQLAlchemy ORM 示例:**

```python
# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    """用户模型 - 对应数据库中的 users 表"""
    __tablename__ = "users"

    # 列定义 (对应 SQL 中的 CREATE TABLE)
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(100))
    hashed_password = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.MEMBER)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系定义 (对应 SQL 中的 JOIN)
    topics = relationship("Topic", back_populates="creator")
    bindings = relationship("Binding", back_populates="user")

# 使用示例
# 查询所有管理员
admins = db.query(User).filter(User.role == UserRole.ADMIN).all()

# 创建新用户
new_user = User(email="new@example.com", name="新用户")
db.add(new_user)
db.commit()

# 关联查询: 获取用户创建的所有课题
user = db.query(User).filter(User.id == 1).first()
for topic in user.topics:  # 自动执行 JOIN 查询
    print(topic.title)
```

### 3.5 数据库在项目中的位置

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    数据流转：从前端到数据库                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   用户点击"创建课题"                                                    │
│          │                                                              │
│          ▼                                                              │
│   ┌─────────────────┐                                                   │
│   │   Vue 组件      │  topicsStore.createTopic({ title: '新课题' })    │
│   └────────┬────────┘                                                   │
│            │                                                            │
│            ▼                                                            │
│   ┌─────────────────┐                                                   │
│   │   Axios 请求    │  POST /api/topics { "title": "新课题" }          │
│   └────────┬────────┘                                                   │
│            │                                                            │
│            ▼                                                            │
│   ┌─────────────────┐                                                   │
│   │   FastAPI 路由  │  @router.post("/topics")                         │
│   │   + Pydantic    │  验证请求数据格式                                 │
│   └────────┬────────┘                                                   │
│            │                                                            │
│            ▼                                                            │
│   ┌─────────────────┐                                                   │
│   │   SQLAlchemy    │  topic = Topic(**data.dict())                    │
│   │   ORM 模型      │  db.add(topic)                                   │
│   └────────┬────────┘                                                   │
│            │  生成 SQL:                                                 │
│            │  INSERT INTO topics (title, ...) VALUES ('新课题', ...)   │
│            ▼                                                            │
│   ┌─────────────────┐                                                   │
│   │   PostgreSQL    │  执行 SQL，写入磁盘                              │
│   │   数据库        │  返回新记录 ID                                   │
│   └─────────────────┘                                                   │
│                                                                         │
│   总结:                                                                 │
│   - SQL 是语言 (告诉数据库做什么)                                       │
│   - PostgreSQL 是数据库系统 (存储和管理数据)                            │
│   - SQLAlchemy 是 ORM (让 Python 代码生成 SQL)                          │
│   - 开发者写 Python 代码，ORM 自动生成 SQL，PostgreSQL 执行 SQL         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 后端框架之争：FastAPI vs Java Spring Boot

Java Spring 是企业级开发的老牌框架，FastAPI 是 Python 生态的新星。它们各有优势，选择哪个取决于团队技术栈和项目需求。

### 4.1 代码对比：实现同一个 API

让我们用实际代码来对比两者的开发体验。

**需求：创建一个用户注册 API**
- 接收用户名、邮箱、密码
- 验证邮箱格式
- 返回创建的用户信息

#### Spring Boot 实现 (Java)

```java
// ================== 1. 实体类 (Entity) ==================
// src/main/java/com/tcgs/entity/User.java
@Entity
@Table(name = "users")
@Data  // Lombok 注解，自动生成 getter/setter
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false)
    private String username;

    @Column(nullable = false)
    private String password;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}

// ================== 2. DTO (数据传输对象) ==================
// src/main/java/com/tcgs/dto/UserCreateRequest.java
@Data
public class UserCreateRequest {
    @NotBlank(message = "用户名不能为空")
    private String username;

    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email;

    @NotBlank(message = "密码不能为空")
    @Size(min = 6, message = "密码至少6位")
    private String password;
}

// src/main/java/com/tcgs/dto/UserResponse.java
@Data
public class UserResponse {
    private Long id;
    private String username;
    private String email;
    private LocalDateTime createdAt;
}

// ================== 3. Repository (数据访问层) ==================
// src/main/java/com/tcgs/repository/UserRepository.java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    boolean existsByEmail(String email);
}

// ================== 4. Service (业务逻辑层) ==================
// src/main/java/com/tcgs/service/UserService.java
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserResponse createUser(UserCreateRequest request) {
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new BusinessException("邮箱已被注册");
        }

        User user = new User();
        user.setUsername(request.getUsername());
        user.setEmail(request.getEmail());
        user.setPassword(passwordEncoder.encode(request.getPassword()));

        User saved = userRepository.save(user);
        return mapToResponse(saved);
    }

    private UserResponse mapToResponse(User user) {
        UserResponse response = new UserResponse();
        response.setId(user.getId());
        response.setUsername(user.getUsername());
        response.setEmail(user.getEmail());
        response.setCreatedAt(user.getCreatedAt());
        return response;
    }
}

// ================== 5. Controller (控制层) ==================
// src/main/java/com/tcgs/controller/UserController.java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;

    @PostMapping
    public ResponseEntity<UserResponse> createUser(
            @Valid @RequestBody UserCreateRequest request) {
        UserResponse response = userService.createUser(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}

// 文件数量: 5个文件，约 100+ 行代码
```

#### FastAPI 实现 (Python)

```python
# ================== 1. 模型 + Schema 合并 ==================
# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr  # 自动验证邮箱格式
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True  # 支持从 ORM 对象转换

# ================== 2. 路由 (Controller + Service 合并) ==================
# app/api/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

router = APIRouter(prefix="/api/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"])

@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db)
):
    # 检查邮箱是否已注册
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 创建用户
    user = User(
        username=request.username,
        email=request.email,
        hashed_password=pwd_context.hash(request.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user  # Pydantic 自动转换为 JSON

# 文件数量: 2个文件，约 50 行代码
```

### 4.2 详细特性对比

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FastAPI vs Spring Boot 详细对比                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────┬─────────────────────┬─────────────────────┐      │
│   │ 特性            │ FastAPI (Python)    │ Spring Boot (Java)  │      │
│   ├─────────────────┼─────────────────────┼─────────────────────┤      │
│   │ 代码量          │ 少 (约50行)         │ 多 (约100+行)       │      │
│   │ 文件数          │ 2-3个               │ 5-6个               │      │
│   │ 启动时间        │ <1秒                │ 5-15秒              │      │
│   │ 内存占用        │ ~50MB               │ ~200-500MB          │      │
│   │ API 文档        │ 自动生成 (内置)     │ 需要 Swagger 配置   │      │
│   │ 类型检查        │ Pydantic 运行时     │ 编译时              │      │
│   │ 异步支持        │ 原生 async/await    │ WebFlux (复杂)      │      │
│   │ 学习曲线        │ 平缓                │ 陡峭                │      │
│   │ 企业级特性      │ 需要额外配置        │ 开箱即用            │      │
│   │ 生态成熟度      │ 年轻但活跃          │ 非常成熟            │      │
│   │ 招聘市场        │ 数据/AI团队多       │ 企业开发团队多      │      │
│   └─────────────────┴─────────────────────┴─────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Spring Boot 的优势场景

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Spring Boot 适合的场景                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   1. 大型企业级应用                                                     │
│      ─────────────────                                                  │
│      - 复杂的事务管理 (分布式事务)                                      │
│      - 完善的安全框架 (Spring Security)                                 │
│      - 成熟的微服务生态 (Spring Cloud)                                  │
│                                                                         │
│   2. 团队主要是 Java 背景                                               │
│      ─────────────────────                                              │
│      - Java 工程师更容易上手                                            │
│      - IDE 支持完善 (IntelliJ IDEA)                                     │
│      - 编译时类型检查，大型项目更安全                                   │
│                                                                         │
│   3. 需要与 Java 生态集成                                               │
│      ─────────────────────                                              │
│      - 对接 Kafka、Elasticsearch 等 Java 生态组件                       │
│      - 使用 Hibernate 复杂 ORM 特性                                     │
│      - 需要 JVM 调优经验的高并发场景                                    │
│                                                                         │
│   代码示例 - Spring Security 配置:                                      │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  @Configuration                                                 │  │
│   │  @EnableWebSecurity                                             │  │
│   │  public class SecurityConfig {                                  │  │
│   │      @Bean                                                      │  │
│   │      public SecurityFilterChain filterChain(HttpSecurity http) │  │
│   │              throws Exception {                                 │  │
│   │          http.authorizeHttpRequests(auth -> auth                │  │
│   │              .requestMatchers("/api/public/**").permitAll()     │  │
│   │              .requestMatchers("/api/admin/**").hasRole("ADMIN") │  │
│   │              .anyRequest().authenticated()                      │  │
│   │          );                                                     │  │
│   │          return http.build();                                   │  │
│   │      }                                                          │  │
│   │  }                                                              │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.4 FastAPI 的优势场景

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FastAPI 适合的场景                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   1. AI/ML 项目 (TCGS 的情况)                                           │
│      ────────────────────────                                           │
│      - 团队主要是 Python 背景 (算法工程师)                              │
│      - 需要调用 NumPy、Pandas、PyTorch 等库                             │
│      - 快速原型开发，迭代速度快                                         │
│                                                                         │
│   2. 中小型 API 服务                                                    │
│      ─────────────────                                                  │
│      - 代码简洁，维护成本低                                             │
│      - 自动生成 API 文档，前后端协作方便                                │
│      - 部署资源占用少                                                   │
│                                                                         │
│   3. 高性能异步场景                                                     │
│      ─────────────────                                                  │
│      - 原生 async/await，无需额外配置                                   │
│      - 基于 Starlette，性能接近 Go                                      │
│      - 适合 I/O 密集型应用 (大量数据库/API调用)                         │
│                                                                         │
│   代码示例 - FastAPI 异步 + 自动文档:                                   │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  from fastapi import FastAPI, Query                             │  │
│   │  from typing import Optional                                    │  │
│   │                                                                 │  │
│   │  app = FastAPI(                                                 │  │
│   │      title="TCGS API",                                          │  │
│   │      description="算法能力管理平台 API",                         │  │
│   │      version="1.0.0"                                            │  │
│   │  )                                                              │  │
│   │                                                                 │  │
│   │  @app.get("/api/topics")                                        │  │
│   │  async def list_topics(                                         │  │
│   │      status: Optional[str] = Query(None, description="筛选状态"),│  │
│   │      limit: int = Query(10, ge=1, le=100, description="每页数量")│  │
│   │  ):                                                             │  │
│   │      """                                                        │  │
│   │      获取课题列表                                                │  │
│   │                                                                 │  │
│   │      - **status**: 可选，筛选课题状态                            │  │
│   │      - **limit**: 每页返回数量，1-100                           │  │
│   │      """                                                        │  │
│   │      # 这些注释和类型提示会自动生成 Swagger 文档！               │  │
│   │      return await topic_service.list(status=status, limit=limit)│  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   访问 http://localhost:8000/docs 自动看到交互式文档:                   │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  ┌─────────────────────────────────────────────────────────┐   │  │
│   │  │  GET /api/topics        获取课题列表              [Try it] │   │  │
│   │  ├─────────────────────────────────────────────────────────┤   │  │
│   │  │  Parameters:                                             │   │  │
│   │  │  ├─ status (query): 筛选状态                             │   │  │
│   │  │  └─ limit (query): 每页数量 (default: 10)                │   │  │
│   │  └─────────────────────────────────────────────────────────┘   │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.5 TCGS 项目选择 FastAPI 的理由

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    为什么 TCGS 选择 FastAPI                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   1. 团队背景: 算法团队，Python 是主力语言                              │
│      → 无需学习新语言，快速上手                                         │
│                                                                         │
│   2. 项目规模: 中型管理系统，非高并发场景                               │
│      → FastAPI 性能完全够用                                             │
│                                                                         │
│   3. 开发效率: 需要快速迭代，验证业务需求                               │
│      → Python 开发效率高，代码量少                                      │
│                                                                         │
│   4. API 文档: 前后端协作频繁                                           │
│      → Swagger 自动生成，减少沟通成本                                   │
│                                                                         │
│   5. 容器化部署: Docker + Docker Compose                                │
│      → Python 镜像小，启动快，资源占用少                                │
│                                                                         │
│   如果是以下情况，会考虑 Spring Boot:                                   │
│   ─────────────────────────────────                                     │
│   - 团队主要是 Java 背景                                                │
│   - 需要复杂的企业级特性 (分布式事务、RBAC)                             │
│   - 项目需要长期维护 10+ 年                                             │
│   - 公司技术栈统一为 Java                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. 数据库迁移：Alembic 的前世今生

数据库迁移是一个经常被忽视但极其重要的话题。这一章我们详细讲解：没有 Alembic 之前有多痛苦，有了 Alembic 之后工作流程如何改变。

### 5.1 没有 Alembic 的黑暗时代

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    场景：给 users 表添加 avatar 字段                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   开发者 A 在代码中添加了新字段:                                        │
│   ───────────────────────────────                                       │
│   class User(Base):                                                     │
│       id = Column(Integer, primary_key=True)                            │
│       email = Column(String(255))                                       │
│       avatar = Column(String(500))  # ← 新增字段                        │
│                                                                         │
│   然后他在本地数据库手动执行:                                           │
│   ─────────────────────────────                                         │
│   ALTER TABLE users ADD COLUMN avatar VARCHAR(500);                     │
│                                                                         │
│   代码提交到 Git，部署到测试环境...                                     │
│                                                                         │
│   ❌ 测试环境报错！                                                     │
│   sqlalchemy.exc.OperationalError: column "avatar" does not exist       │
│                                                                         │
│   因为测试环境的数据库没有执行那条 ALTER TABLE！                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**没有迁移工具时的"解决方案"：**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    传统方式的各种问题                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   方案 1: 手动维护 SQL 文件                                             │
│   ──────────────────────────                                            │
│   项目根目录下创建:                                                     │
│   /sql/                                                                 │
│   ├── 001_create_users.sql                                              │
│   ├── 002_add_avatar.sql         ← 容易忘记                             │
│   ├── 003_add_topics.sql                                                │
│   └── 004_rename_column.sql      ← 顺序搞错了怎么办？                   │
│                                                                         │
│   问题:                                                                 │
│   - 哪些 SQL 已经执行过？哪些没有？没人知道                             │
│   - 多人开发时，SQL 文件命名冲突                                        │
│   - 回滚怎么办？每个 SQL 都要写对应的 rollback                          │
│   - 不同环境（开发/测试/生产）状态不一致                                │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   方案 2: 每次部署前 DROP 所有表，重新创建                              │
│   ────────────────────────────────────────                              │
│   Base.metadata.drop_all(engine)                                        │
│   Base.metadata.create_all(engine)                                      │
│                                                                         │
│   问题:                                                                 │
│   - 生产环境敢这么干？数据全没了！                                      │
│   - 只适合开发环境，完全不可用于生产                                    │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   方案 3: 让 DBA 手动操作                                               │
│   ────────────────────────                                              │
│   开发: "张哥，帮我在生产库加个字段"                                    │
│   DBA: "行，发我 SQL"                                                   │
│   开发: "ALTER TABLE users ADD COLUMN avatar VARCHAR(500);"             │
│   DBA: (复制粘贴执行)                                                   │
│   DBA: "好了"                                                           │
│                                                                         │
│   两周后...                                                             │
│   另一个开发: "线上怎么没有 avatar_url 字段？"                          │
│   DBA: "我加的是 avatar，不是 avatar_url 啊..."                         │
│                                                                         │
│   问题:                                                                 │
│   - 效率低，每次都要人工操作                                            │
│   - 容易出错，没有版本记录                                              │
│   - 无法自动化部署                                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Alembic 是什么？

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Alembic = 数据库的 Git                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Git 管理代码版本:                    Alembic 管理数据库版本:          │
│   ─────────────────                    ────────────────────────          │
│   git init                             alembic init                     │
│   git add .                            alembic revision (生成迁移)      │
│   git commit                           alembic upgrade (应用迁移)       │
│   git log                              alembic history (查看历史)       │
│   git revert                           alembic downgrade (回滚)         │
│                                                                         │
│   核心理念:                                                             │
│   ──────────                                                            │
│   1. 每次数据库结构变更都生成一个"迁移文件"                             │
│   2. 迁移文件包含 upgrade() 和 downgrade() 两个方法                     │
│   3. 数据库中有一张表记录"当前执行到哪个版本"                           │
│   4. 任何环境执行 alembic upgrade head 就能同步到最新结构               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Alembic 工作原理详解

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Alembic 工作流程                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   步骤 1: 修改代码中的模型                                              │
│   ─────────────────────────                                             │
│   # app/models/user.py                                                  │
│   class User(Base):                                                     │
│       id = Column(Integer, primary_key=True)                            │
│       email = Column(String(255))                                       │
│       avatar = Column(String(500))  # ← 新增这一行                      │
│                                                                         │
│   步骤 2: 生成迁移文件 (Alembic 自动对比差异)                           │
│   ──────────────────────────────────────────                            │
│   $ alembic revision --autogenerate -m "add user avatar"                │
│                                                                         │
│   Alembic 做了什么:                                                     │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  1. 读取代码中的 SQLAlchemy 模型 (User.avatar)                  │  │
│   │  2. 连接数据库，读取当前表结构 (没有 avatar 列)                  │  │
│   │  3. 对比差异：代码有 avatar，数据库没有                          │  │
│   │  4. 自动生成迁移文件                                             │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   生成的迁移文件 (alembic/versions/a1b2c3d4_add_user_avatar.py):        │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  """add user avatar                                             │  │
│   │                                                                 │  │
│   │  Revision ID: a1b2c3d4                                          │  │
│   │  Revises: 9z8y7x6w (上一个版本)                                 │  │
│   │  Create Date: 2026-04-02 10:30:00                               │  │
│   │  """                                                            │  │
│   │  from alembic import op                                         │  │
│   │  import sqlalchemy as sa                                        │  │
│   │                                                                 │  │
│   │  revision = 'a1b2c3d4'                                          │  │
│   │  down_revision = '9z8y7x6w'  # 指向上一个版本                   │  │
│   │                                                                 │  │
│   │  def upgrade():                                                 │  │
│   │      # 升级：添加列                                              │  │
│   │      op.add_column('users',                                     │  │
│   │          sa.Column('avatar', sa.String(500), nullable=True))    │  │
│   │                                                                 │  │
│   │  def downgrade():                                               │  │
│   │      # 回滚：删除列                                              │  │
│   │      op.drop_column('users', 'avatar')                          │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   步骤 3: 执行迁移                                                      │
│   ────────────────                                                      │
│   $ alembic upgrade head                                                │
│                                                                         │
│   Alembic 做了什么:                                                     │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  1. 查询 alembic_version 表，获取当前版本 (9z8y7x6w)            │  │
│   │  2. 找到所有待执行的迁移文件 (a1b2c3d4)                          │  │
│   │  3. 按顺序执行每个迁移的 upgrade() 方法                          │  │
│   │  4. 更新 alembic_version 表为最新版本 (a1b2c3d4)                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   实际执行的 SQL:                                                       │
│   ALTER TABLE users ADD COLUMN avatar VARCHAR(500);                     │
│   UPDATE alembic_version SET version_num = 'a1b2c3d4';                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.4 迁移版本链 (类似 Git 提交历史)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    迁移版本链示意                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   alembic/versions/ 目录下的文件:                                       │
│   ───────────────────────────────                                       │
│   ├── 001_initial_tables.py          # 创建初始表                       │
│   ├── 002_add_user_avatar.py         # 添加头像字段                     │
│   ├── 003_add_topics_table.py        # 添加课题表                       │
│   ├── 004_add_wiki_module.py         # 添加 Wiki 模块                   │
│   └── 005_add_capacity_binding.py    # 添加产能绑定                     │
│                                                                         │
│   版本链关系 (每个文件记录自己的 down_revision):                        │
│   ──────────────────────────────────────────────                        │
│                                                                         │
│   base (空数据库)                                                       │
│     │                                                                   │
│     ▼                                                                   │
│   ┌─────────────────────┐                                               │
│   │ 001_initial_tables  │  revision = 'abc123'                          │
│   │ down_revision = None│  ← 第一个版本，没有上级                        │
│   └─────────┬───────────┘                                               │
│             │                                                           │
│             ▼                                                           │
│   ┌─────────────────────┐                                               │
│   │ 002_add_user_avatar │  revision = 'def456'                          │
│   │ down_revision='abc123'│                                             │
│   └─────────┬───────────┘                                               │
│             │                                                           │
│             ▼                                                           │
│   ┌─────────────────────┐                                               │
│   │ 003_add_topics_table│  revision = 'ghi789'                          │
│   │ down_revision='def456'│                                             │
│   └─────────┬───────────┘                                               │
│             │                                                           │
│             ▼                                                           │
│         ... 更多版本 ...                                                │
│             │                                                           │
│             ▼                                                           │
│   ┌─────────────────────┐                                               │
│   │ HEAD (最新版本)     │  ← alembic upgrade head 会升级到这里          │
│   └─────────────────────┘                                               │
│                                                                         │
│   数据库中的 alembic_version 表:                                        │
│   ────────────────────────────                                          │
│   ┌───────────────────────┐                                             │
│   │ version_num           │                                             │
│   ├───────────────────────┤                                             │
│   │ ghi789               │ ← 当前数据库在这个版本                        │
│   └───────────────────────┘                                             │
│                                                                         │
│   常用命令:                                                             │
│   ─────────                                                             │
│   alembic upgrade head      # 升级到最新版本                            │
│   alembic upgrade +1        # 升级一个版本                              │
│   alembic downgrade -1      # 回滚一个版本                              │
│   alembic downgrade base    # 回滚到初始状态                            │
│   alembic history           # 查看版本历史                              │
│   alembic current           # 查看当前版本                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.5 Alembic 解决的核心问题

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    有了 Alembic 之后                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   问题 1: "我本地能跑，测试环境报错"                                    │
│   ─────────────────────────────────                                     │
│   之前: 开发者手动在本地执行 SQL，忘记告诉别人                          │
│   现在: 迁移文件随代码一起提交，任何环境执行 alembic upgrade head       │
│                                                                         │
│   问题 2: "这个字段是谁加的？什么时候加的？"                            │
│   ───────────────────────────────────────                               │
│   之前: 没人知道，只能看数据库                                          │
│   现在: 每个迁移文件都有作者、日期、描述，可追溯                        │
│                                                                         │
│   问题 3: "上线出 bug 了，需要回滚数据库"                               │
│   ────────────────────────────────────                                  │
│   之前: DBA 手动写回滚 SQL，容易出错                                    │
│   现在: alembic downgrade -1，自动执行 downgrade() 方法                 │
│                                                                         │
│   问题 4: "多人开发，数据库结构冲突"                                    │
│   ─────────────────────────────────                                     │
│   之前: 两个人同时改表结构，部署时互相覆盖                              │
│   现在: Git 合并时发现迁移文件冲突，强制解决后再部署                    │
│                                                                         │
│   问题 5: "新人入职，如何搭建开发环境"                                  │
│   ────────────────────────────────────                                  │
│   之前: 找 DBA 要最新的数据库备份，或者手动执行 N 条 SQL                │
│   现在: alembic upgrade head，几秒钟自动同步到最新结构                  │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   TCGS 项目的实际应用:                                                  │
│   ────────────────────                                                  │
│   # docker-compose.yml 中的启动命令                                     │
│   backend:                                                              │
│     command: >                                                          │
│       sh -c "alembic upgrade head &&    # 先同步数据库结构              │
│              python seed.py &&          # 再插入初始数据                │
│              uvicorn app.main:app ..."  # 最后启动服务                  │
│                                                                         │
│   每次部署自动执行 alembic upgrade head，确保数据库结构最新！           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.6 Alembic 迁移实战示例

```python
# 示例：TCGS 项目中添加 Wiki 点赞功能的迁移

# 1. 首先在代码中添加模型
# app/models/wiki.py
class WikiLike(Base):
    __tablename__ = "wiki_likes"

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("wiki_pages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 联合唯一约束：一个用户只能给一篇文章点赞一次
    __table_args__ = (
        UniqueConstraint('page_id', 'user_id', name='uq_wiki_like'),
    )

# 2. 生成迁移文件
# $ alembic revision --autogenerate -m "add wiki likes table"

# 3. 自动生成的迁移文件 (可以手动调整)
# alembic/versions/xxx_add_wiki_likes_table.py

def upgrade():
    op.create_table(
        'wiki_likes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('page_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['page_id'], ['wiki_pages.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('page_id', 'user_id', name='uq_wiki_like')
    )
    op.create_index('ix_wiki_likes_page_id', 'wiki_likes', ['page_id'])

def downgrade():
    op.drop_index('ix_wiki_likes_page_id', 'wiki_likes')
    op.drop_table('wiki_likes')

# 4. 执行迁移
# $ alembic upgrade head
# INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, add wiki likes table
```

---

## 6. 前端架构：Vue 3 与 Pinia 状态管理

很多人混淆 Vue 和 Pinia 的关系，认为它们是同一个东西。这一章我们彻底搞清楚：**Vue 是 UI 框架，Pinia 是状态管理库**，它们解决的是完全不同的问题。

### 6.1 Vue 是什么？解决什么问题？

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Vue.js 简介                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Vue 是什么？                                                          │
│   ───────────                                                           │
│   Vue.js 是一个用于构建用户界面的 JavaScript 框架，由尤雨溪（Evan You） │
│   于 2014 年创建。它的名字来源于法语单词 "vue"（视图），表明其专注于    │
│   视图层。                                                              │
│                                                                         │
│   Vue 的定位：                                                          │
│   - React 的竞品，但更易上手                                            │
│   - 专注于视图层（View），是 MVVM 模式中的 ViewModel                   │
│   - "渐进式框架"：可以只用一部分功能，也可以用全家桶                   │
│                                                                         │
│   为什么需要 Vue？原生 JavaScript 的痛点：                              │
│   ────────────────────────────────────────                              │
│                                                                         │
│   假设我们要实现一个计数器：                                            │
│                                                                         │
│   原生 JavaScript 写法:                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  <div id="app">                                                 │  │
│   │    <p id="count">0</p>                                          │  │
│   │    <button id="btn">+1</button>                                 │  │
│   │  </div>                                                         │  │
│   │                                                                 │  │
│   │  <script>                                                       │  │
│   │    let count = 0;                                               │  │
│   │    const countEl = document.getElementById('count');            │  │
│   │    const btnEl = document.getElementById('btn');                │  │
│   │                                                                 │  │
│   │    btnEl.addEventListener('click', function() {                 │  │
│   │      count++;                                // 1. 更新数据     │  │
│   │      countEl.textContent = count;            // 2. 手动更新DOM  │  │
│   │    });                                                          │  │
│   │  </script>                                                      │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   问题：                                                                │
│   - 数据和 DOM 需要手动同步，改一处忘改另一处就出 bug                   │
│   - 代码量大：10 个输入框 = 10 次 getElementById + 10 次 addEventListener│
│   - 难以复用：想在另一个页面用？复制粘贴，然后改 ID...                  │
│   - 难以维护：数据散落各处，页面复杂后根本不知道状态在哪                │
│                                                                         │
│   Vue 的解决方案:                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  <template>                                                     │  │
│   │    <p>{{ count }}</p>                <!-- 数据绑定，自动同步 --> │  │
│   │    <button @click="count++">+1</button>  <!-- 事件绑定 -->      │  │
│   │  </template>                                                    │  │
│   │                                                                 │  │
│   │  <script setup>                                                 │  │
│   │  import { ref } from 'vue'                                      │  │
│   │  const count = ref(0)    // 响应式数据：改它，页面自动更新      │  │
│   │  </script>                                                      │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   Vue 带来的改变：                                                      │
│   - 数据驱动：只管修改数据，Vue 自动更新 DOM                           │
│   - 声明式：模板里写"这里显示 count"，不用写"怎么更新它"            │
│   - 组件化：一个 .vue 文件 = 一个可复用的 UI 单元                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Vue = UI 渲染框架                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Vue 的核心职责:                                                       │
│   ───────────────                                                       │
│   1. 声明式渲染: 用模板描述 UI，数据变化自动更新 DOM                    │
│   2. 组件化开发: 把页面拆分成可复用的组件                               │
│   3. 响应式系统: 数据变化自动触发视图更新                               │
│                                                                         │
│   一个简单的 Vue 组件:                                                  │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  <template>                                                     │  │
│   │    <div>                                                        │  │
│   │      <h1>{{ title }}</h1>           <!-- 数据绑定 -->           │  │
│   │      <p>计数: {{ count }}</p>                                   │  │
│   │      <button @click="count++">+1</button>  <!-- 事件绑定 -->    │  │
│   │    </div>                                                       │  │
│   │  </template>                                                    │  │
│   │                                                                 │  │
│   │  <script setup lang="ts">                                       │  │
│   │  import { ref } from 'vue'                                      │  │
│   │                                                                 │  │
│   │  const title = ref('Hello Vue')                                 │  │
│   │  const count = ref(0)  // 响应式数据                            │  │
│   │  // count 变化时，页面自动更新，无需手动操作 DOM                 │  │
│   │  </script>                                                      │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   Vue 解决的问题:                                                       │
│   ───────────────                                                       │
│   传统 JS: document.getElementById('count').innerHTML = newValue        │
│   Vue:     count.value++  // 自动更新 DOM                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 为什么需要 Pinia？Vue 不够吗？

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    组件间状态共享的问题                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   场景: 多个组件需要共享同一份数据                                      │
│   ─────────────────────────────────                                     │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                       App.vue                                   │  │
│   │   ┌─────────────────┐         ┌─────────────────┐              │  │
│   │   │   Sidebar.vue   │         │   TopicList.vue │              │  │
│   │   │                 │         │                 │              │  │
│   │   │ 显示课题数量    │         │  显示课题列表   │              │  │
│   │   │ "共 15 个课题"  │         │  [课题1, 课题2] │              │  │
│   │   └─────────────────┘         └─────────────────┘              │  │
│   │                                       │                         │  │
│   │                               ┌───────┴───────┐                │  │
│   │                               │               │                │  │
│   │                       ┌───────────┐   ┌───────────┐            │  │
│   │                       │TopicCard.vue│ │TopicCard.vue│           │  │
│   │                       │  编辑课题  │   │  编辑课题  │            │  │
│   │                       └───────────┘   └───────────┘            │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   问题:                                                                 │
│   - Sidebar 和 TopicList 都需要访问课题数据                            │
│   - TopicCard 编辑后，Sidebar 和 TopicList 都要更新                    │
│   - 它们不是父子关系，不能简单用 props 传递                             │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   没有 Pinia 的解决方案 (Props 层层传递):                               │
│   ────────────────────────────────────────                              │
│   App.vue (持有 topics)                                                 │
│       │                                                                 │
│       ├── :topics="topics" ──▶ Sidebar.vue                             │
│       │                                                                 │
│       └── :topics="topics" ──▶ TopicList.vue                           │
│               │                                                         │
│               └── :topic="topic" ──▶ TopicCard.vue                     │
│                       │                                                 │
│                       └── @update="???" 怎么传回去？                   │
│                                                                         │
│   问题:                                                                 │
│   - Props 层层传递，代码臃肿 ("Prop Drilling")                         │
│   - 中间组件被迫接收和传递它不需要的数据                                │
│   - 数据更新要层层往上冒，很容易出错                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Pinia = 全局状态管理

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Pinia 解决方案                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   核心理念: 把共享数据放到一个"全局仓库"(Store)                         │
│   ────────────────────────────────────────────                          │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    Pinia Store (全局仓库)                       │  │
│   │   ┌─────────────────────────────────────────────────────────┐  │  │
│   │   │  topicsStore                                            │  │  │
│   │   │  ─────────────                                          │  │  │
│   │   │  state:                                                 │  │  │
│   │   │    topics: [课题1, 课题2, ...]                          │  │  │
│   │   │    loading: false                                       │  │  │
│   │   │                                                         │  │  │
│   │   │  actions:                                               │  │  │
│   │   │    fetchTopics()                                        │  │  │
│   │   │    createTopic()                                        │  │  │
│   │   │    updateTopic()                                        │  │  │
│   │   └─────────────────────────────────────────────────────────┘  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│           │              │              │              │                │
│           │              │              │              │                │
│           ▼              ▼              ▼              ▼                │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐           │
│   │ Sidebar   │  │ TopicList │  │ TopicCard │  │  Header   │           │
│   │           │  │           │  │           │  │           │           │
│   │ 直接读取  │  │ 直接读取  │  │ 直接修改  │  │ 直接读取  │           │
│   │ store数据 │  │ store数据 │  │ store数据 │  │ store数据 │           │
│   └───────────┘  └───────────┘  └───────────┘  └───────────┘           │
│                                                                         │
│   优势:                                                                 │
│   - 任何组件都可以直接访问 Store，无需层层传递                          │
│   - 数据修改后，所有使用该数据的组件自动更新                            │
│   - 逻辑集中管理，易于维护和测试                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.4 Vue 和 Pinia 的区别总结

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Vue vs Pinia 对比                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌───────────────┬─────────────────────┬─────────────────────┐        │
│   │               │ Vue                 │ Pinia               │        │
│   ├───────────────┼─────────────────────┼─────────────────────┤        │
│   │ 是什么        │ UI 渲染框架         │ 状态管理库          │        │
│   │ 解决什么问题  │ 声明式渲染 UI       │ 组件间共享状态      │        │
│   │ 数据范围      │ 组件内部 (局部)     │ 全局 (跨组件)       │        │
│   │ 必须使用吗    │ 是，核心框架        │ 否，可选            │        │
│   │ 替代品        │ React, Angular      │ Vuex, Redux         │        │
│   └───────────────┴─────────────────────┴─────────────────────┘        │
│                                                                         │
│   类比:                                                                 │
│   ──────                                                                │
│   Vue = 房间里的家具 (每个房间有自己的家具)                             │
│   Pinia = 公共储物间 (所有房间都可以存取东西)                           │
│                                                                         │
│   什么时候需要 Pinia:                                                   │
│   ─────────────────────                                                 │
│   ✅ 多个组件需要共享同一份数据 (用户信息、课题列表)                    │
│   ✅ 数据需要跨页面保持 (登录状态、购物车)                              │
│   ✅ 数据逻辑复杂，需要集中管理                                         │
│                                                                         │
│   什么时候不需要 Pinia:                                                 │
│   ─────────────────────                                                 │
│   ❌ 数据只在一个组件内使用 → 用 ref/reactive                          │
│   ❌ 数据只在父子组件间传递 → 用 props/emit                            │
│   ❌ 简单的小应用 → 直接用 Vue 响应式就够了                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.5 TCGS 项目中的实际代码

**Pinia Store 定义 (stores/topics.ts):**

```typescript
// stores/topics.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { topicsApi } from '@/api/topics'
import type { Topic } from '@/types'

export const useTopicsStore = defineStore('topics', () => {
  // ═══════════════════════════════════════════════════════════
  // State (状态) - 存储数据
  // ═══════════════════════════════════════════════════════════
  const topics = ref<Topic[]>([])
  const loading = ref(false)
  const currentTopic = ref<Topic | null>(null)

  // ═══════════════════════════════════════════════════════════
  // Getters (计算属性) - 派生数据
  // ═══════════════════════════════════════════════════════════
  const openTopics = computed(() =>
    topics.value.filter(t => t.result === 'OPEN')
  )

  const topicCount = computed(() => topics.value.length)

  // ═══════════════════════════════════════════════════════════
  // Actions (方法) - 修改数据、调用 API
  // ═══════════════════════════════════════════════════════════
  async function fetchTopics() {
    loading.value = true
    try {
      const response = await topicsApi.list()
      topics.value = response.data  // 更新状态，所有组件自动更新
    } finally {
      loading.value = false
    }
  }

  async function createTopic(data: TopicCreate) {
    const response = await topicsApi.create(data)
    topics.value.push(response.data)  // 添加到列表，Sidebar 计数自动更新
    return response.data
  }

  async function updateTopic(id: number, data: Partial<Topic>) {
    const response = await topicsApi.update(id, data)
    const index = topics.value.findIndex(t => t.id === id)
    if (index !== -1) {
      topics.value[index] = response.data  // 更新列表项
    }
    return response.data
  }

  // 返回需要暴露的内容
  return {
    topics,
    loading,
    currentTopic,
    openTopics,
    topicCount,
    fetchTopics,
    createTopic,
    updateTopic
  }
})
```

**组件中使用 Store:**

```vue
<!-- Sidebar.vue - 显示课题数量 -->
<template>
  <div class="sidebar">
    <div class="stat">
      共 {{ topicsStore.topicCount }} 个课题
    </div>
    <div class="stat">
      进行中: {{ topicsStore.openTopics.length }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTopicsStore } from '@/stores/topics'

const topicsStore = useTopicsStore()
// 不需要 props，直接访问全局 Store
// topicsStore.topicCount 变化时，这里自动更新
</script>
```

```vue
<!-- TopicCard.vue - 编辑课题 -->
<template>
  <div class="topic-card">
    <h3>{{ topic.title }}</h3>
    <button @click="handleEdit">编辑</button>
  </div>
</template>

<script setup lang="ts">
import { useTopicsStore } from '@/stores/topics'

const props = defineProps<{ topic: Topic }>()
const topicsStore = useTopicsStore()

async function handleEdit() {
  await topicsStore.updateTopic(props.topic.id, { title: '新标题' })
  // 更新完成后，Sidebar 的计数、TopicList 的列表都会自动更新
  // 因为它们都在读取同一个 Store
}
</script>
```

### 6.6 数据流向总结

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TCGS 前端数据流                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   用户操作                                                              │
│       │                                                                 │
│       ▼                                                                 │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │  Vue 组件                                                     │    │
│   │  <button @click="handleCreate">创建课题</button>              │    │
│   └───────────────────────────────────────────────────────────────┘    │
│       │                                                                 │
│       │ 调用 Store Action                                              │
│       ▼                                                                 │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │  Pinia Store                                                  │    │
│   │  topicsStore.createTopic(data)                                │    │
│   │  - 设置 loading = true                                        │    │
│   │  - 调用 API                                                   │    │
│   │  - 更新 topics 数组                                           │    │
│   │  - 设置 loading = false                                       │    │
│   └───────────────────────────────────────────────────────────────┘    │
│       │                                                                 │
│       │ 调用 API 服务                                                  │
│       ▼                                                                 │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │  API 层 (api/topics.ts)                                       │    │
│   │  - 添加 Token                                                 │    │
│   │  - 转换命名风格                                               │    │
│   │  - 发送 HTTP 请求                                             │    │
│   └───────────────────────────────────────────────────────────────┘    │
│       │                                                                 │
│       │ HTTP 请求到后端                                                │
│       ▼                                                                 │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │  后端 (FastAPI + PostgreSQL)                                  │    │
│   └───────────────────────────────────────────────────────────────┘    │
│       │                                                                 │
│       │ 响应返回                                                       │
│       ▼                                                                 │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │  Pinia Store 更新状态                                         │    │
│   │  topics.value.push(newTopic)                                  │    │
│   └───────────────────────────────────────────────────────────────┘    │
│       │                                                                 │
│       │ Vue 响应式系统检测到变化                                       │
│       ▼                                                                 │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │  所有使用该数据的组件自动更新                                 │    │
│   │  - TopicList: 显示新课题                                      │    │
│   │  - Sidebar: 计数 +1                                           │    │
│   │  - Header: 显示最新动态                                       │    │
│   └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. 容器化革命：Docker 如何解决依赖地狱

"在我机器上能跑啊！" —— 这可能是软件开发中最令人崩溃的一句话。Docker 的出现，彻底解决了这个问题。

### 7.1 Python 依赖地狱：没有 Docker 之前

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Python 依赖地狱场景                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   场景 1: 版本冲突                                                      │
│   ─────────────────                                                     │
│   项目 A 需要: numpy==1.19.0                                            │
│   项目 B 需要: numpy==1.24.0                                            │
│   系统只能装一个版本！                                                  │
│                                                                         │
│   场景 2: 系统依赖缺失                                                  │
│   ────────────────────                                                  │
│   开发者: pip install psycopg2                                          │
│   报错: Error: pg_config executable not found                           │
│   原因: 需要先安装 PostgreSQL 开发库 (libpq-dev)                        │
│   不同系统安装方式不同:                                                 │
│     - Ubuntu: apt install libpq-dev                                     │
│     - macOS: brew install postgresql                                    │
│     - Windows: ???（更复杂）                                            │
│                                                                         │
│   场景 3: Python 版本不一致                                             │
│   ─────────────────────────                                             │
│   开发者: 使用 Python 3.11                                              │
│   服务器: 安装的是 Python 3.8                                           │
│   代码: match case 语法 (3.10+ 才支持)                                  │
│   结果: SyntaxError!                                                    │
│                                                                         │
│   场景 4: 操作系统差异                                                  │
│   ────────────────────                                                  │
│   开发者: macOS M1 芯片                                                 │
│   服务器: Linux x86_64                                                  │
│   某些 C 扩展包编译结果不兼容                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**传统解决方案及其问题：**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    传统解决方案                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   方案 1: virtualenv / venv                                             │
│   ─────────────────────────                                             │
│   python -m venv myenv                                                  │
│   source myenv/bin/activate                                             │
│   pip install -r requirements.txt                                       │
│                                                                         │
│   解决了: Python 包版本隔离                                             │
│   没解决: 系统依赖 (libpq-dev)、Python 版本、操作系统差异               │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   方案 2: Conda                                                         │
│   ─────────────                                                         │
│   conda create -n myenv python=3.11                                     │
│   conda activate myenv                                                  │
│   conda install numpy pandas                                            │
│                                                                         │
│   解决了: Python 版本 + 部分二进制依赖                                  │
│   没解决: 操作系统差异、部署环境复杂、Conda 本身也要安装                │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   方案 3: 写部署文档                                                    │
│   ─────────────────                                                     │
│   README.md:                                                            │
│   1. 安装 Python 3.11                                                   │
│   2. 安装 PostgreSQL 开发库                                             │
│   3. 创建虚拟环境                                                       │
│   4. 安装依赖                                                           │
│   5. 配置环境变量                                                       │
│   6. 启动服务                                                           │
│                                                                         │
│   问题: 步骤多、容易出错、每个环境都要手动操作                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Docker 的解决方案：把一切都打包进去

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Docker 的核心理念                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Docker 镜像 = 完整的运行环境快照                                      │
│   ─────────────────────────────────                                     │
│                                                                         │
│   镜像包含:                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                 │  │
│   │  ┌───────────────────────────────────────────────────────────┐ │  │
│   │  │  应用代码                                                  │ │  │
│   │  │  main.py, app/, templates/, ...                           │ │  │
│   │  └───────────────────────────────────────────────────────────┘ │  │
│   │  ┌───────────────────────────────────────────────────────────┐ │  │
│   │  │  Python 依赖 (pip packages)                               │ │  │
│   │  │  fastapi, sqlalchemy, pydantic, uvicorn, ...              │ │  │
│   │  └───────────────────────────────────────────────────────────┘ │  │
│   │  ┌───────────────────────────────────────────────────────────┐ │  │
│   │  │  系统依赖 (apt packages)                                  │ │  │
│   │  │  libpq-dev, gcc, curl, ...                                │ │  │
│   │  └───────────────────────────────────────────────────────────┘ │  │
│   │  ┌───────────────────────────────────────────────────────────┐ │  │
│   │  │  Python 解释器                                            │ │  │
│   │  │  Python 3.11.x                                            │ │  │
│   │  └───────────────────────────────────────────────────────────┘ │  │
│   │  ┌───────────────────────────────────────────────────────────┐ │  │
│   │  │  基础操作系统 (精简版)                                    │ │  │
│   │  │  Debian slim / Alpine Linux                               │ │  │
│   │  └───────────────────────────────────────────────────────────┘ │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   所有这些都打包在一个镜像里，任何地方运行都一样！                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Dockerfile：打包的"菜谱"

**TCGS 后端 Dockerfile 详解：**

```dockerfile
# ══════════════════════════════════════════════════════════════════════════
# 第 1 步: 选择基础镜像 (包含 Python 3.11 + Debian 精简版)
# ══════════════════════════════════════════════════════════════════════════
FROM python:3.11-slim
# 这一行就解决了 Python 版本问题！
# python:3.11-slim 包含:
#   - Debian Linux 精简版
#   - Python 3.11 解释器
#   - pip 包管理器

# ══════════════════════════════════════════════════════════════════════════
# 第 2 步: 安装系统依赖
# ══════════════════════════════════════════════════════════════════════════
RUN apt-get update && apt-get install -y \
    libpq-dev \     # PostgreSQL 客户端库 (psycopg2 需要)
    gcc \           # C 编译器 (编译某些 Python 包)
    curl \          # HTTP 工具
    && rm -rf /var/lib/apt/lists/*  # 清理缓存，减小镜像体积
# 这一步解决了"libpq-dev 找不到"的问题！

# ══════════════════════════════════════════════════════════════════════════
# 第 3 步: 安装 Python 依赖
# ══════════════════════════════════════════════════════════════════════════
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# requirements.txt 包含:
#   fastapi==0.115.0
#   sqlalchemy==2.0.35
#   psycopg2-binary==2.9.9
#   uvicorn==0.30.6
#   ...
# 这一步把所有 Python 依赖都装进镜像！

# ══════════════════════════════════════════════════════════════════════════
# 第 4 步: 复制应用代码
# ══════════════════════════════════════════════════════════════════════════
COPY . .
# 把项目所有文件复制到镜像的 /app 目录

# ══════════════════════════════════════════════════════════════════════════
# 第 5 步: 定义启动命令
# ══════════════════════════════════════════════════════════════════════════
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**构建和运行：**

```bash
# 构建镜像 (执行 Dockerfile 中的所有步骤)
docker build -t tcgs-backend .

# 运行容器 (从镜像创建一个运行实例)
docker run -p 8000:8000 tcgs-backend

# 镜像可以推送到任何地方运行
docker push myregistry/tcgs-backend:v1.0
```

### 7.4 Docker 回答的关键问题

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FAQ: Docker 与依赖                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Q: Docker 能解决 Python 依赖问题吗？                                  │
│   A: 是的，完全可以！                                                   │
│      - Python 解释器：打包在镜像里                                      │
│      - pip 包：打包在镜像里                                             │
│      - 系统库：打包在镜像里                                             │
│      镜像 = 完整的运行环境，任何地方运行都一样                          │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   Q: 依赖可以打包进 Docker 镜像吗？                                     │
│   A: 是的！这正是 Docker 的核心功能                                     │
│                                                                         │
│      构建时 (docker build):                                             │
│      ┌─────────────────────────────────────────────────────────────┐   │
│      │  FROM python:3.11-slim        ← 基础环境                    │   │
│      │  RUN apt-get install libpq-dev ← 系统依赖打包进去           │   │
│      │  RUN pip install -r requirements.txt ← Python 依赖打包进去  │   │
│      │  COPY . .                      ← 代码打包进去               │   │
│      └─────────────────────────────────────────────────────────────┘   │
│                                                                         │
│      运行时 (docker run):                                               │
│      ┌─────────────────────────────────────────────────────────────┐   │
│      │  容器直接使用镜像里的一切                                   │   │
│      │  不需要宿主机安装 Python                                    │   │
│      │  不需要宿主机安装任何依赖                                   │   │
│      │  只需要 Docker Engine                                       │   │
│      └─────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   Q: 不同电脑上运行会有差异吗？                                         │
│   A: 不会！这就是 Docker 的意义                                         │
│                                                                         │
│      开发者 A (macOS M1):                                               │
│        docker run tcgs-backend → 运行 Linux 容器，行为一致              │
│                                                                         │
│      开发者 B (Windows 11):                                             │
│        docker run tcgs-backend → 运行 Linux 容器，行为一致              │
│                                                                         │
│      服务器 (Ubuntu 22.04):                                             │
│        docker run tcgs-backend → 运行 Linux 容器，行为一致              │
│                                                                         │
│      同一个镜像，处处一致！                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.5 Docker Compose：管理多个容器

TCGS 项目有多个服务，用 Docker Compose 一键启动：

```yaml
# docker-compose.yml
version: '3.8'

services:
  # ═══════════════════════════════════════════════════════════════════
  # PostgreSQL 数据库
  # ═══════════════════════════════════════════════════════════════════
  postgres:
    image: postgres:15-alpine     # 官方镜像，不用自己装数据库
    container_name: tcgs-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: tcgs
    volumes:
      - postgres_data:/var/lib/postgresql/data  # 数据持久化

  # ═══════════════════════════════════════════════════════════════════
  # FastAPI 后端
  # ═══════════════════════════════════════════════════════════════════
  backend:
    build: ./backend              # 从 Dockerfile 构建
    container_name: tcgs-backend
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/tcgs
      # ↑ postgres 是服务名，Docker 自动解析为容器 IP
    depends_on:
      - postgres                  # 等 postgres 启动后再启动
    ports:
      - "8000:8000"

  # ═══════════════════════════════════════════════════════════════════
  # Nginx + Vue 前端
  # ═══════════════════════════════════════════════════════════════════
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: tcgs-frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:  # 命名卷，数据不会随容器删除而丢失
```

**一键启动整个项目：**

```bash
# 构建并启动所有服务
docker compose up -d --build

# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f backend

# 停止所有服务
docker compose down
```

### 7.6 Docker 带来的变革

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    有了 Docker 之后                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   之前                              之后                                │
│   ──────────────────────────────    ──────────────────────────────      │
│   1. 安装 Python 3.11               1. docker compose up                │
│   2. 安装 PostgreSQL                   (完成)                           │
│   3. 安装 libpq-dev                                                     │
│   4. 创建虚拟环境                                                       │
│   5. pip install                                                        │
│   6. 配置环境变量                                                       │
│   7. 创建数据库                                                         │
│   8. 运行迁移                                                           │
│   9. 启动服务                                                           │
│   (可能还会遇到各种报错)                                                │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   新人入职:                                                             │
│   之前: 花一天时间搭环境                                                │
│   之后: git clone → docker compose up → 5分钟开始开发                  │
│                                                                         │
│   部署上线:                                                             │
│   之前: 写部署文档、手动操作、容易出错                                  │
│   之后: docker compose up，和本地一模一样                              │
│                                                                         │
│   环境一致性:                                                           │
│   之前: "在我机器上能跑"                                                │
│   之后: 镜像一样，行为一样，没有借口                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. 反向代理：为什么需要 Nginx

很多人会问：前端和后端都能独立运行，为什么还要加一层 Nginx？直接访问不行吗？这一章我们来解答这个问题。

### 8.1 没有 Nginx 会怎样？

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    场景：没有反向代理的前后端分离                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   前端开发服务器: http://localhost:5173 (Vite)                          │
│   后端 API 服务: http://localhost:8000 (FastAPI)                        │
│                                                                         │
│   问题 1: 跨域错误 (CORS)                                               │
│   ─────────────────────────                                             │
│   浏览器访问: http://localhost:5173                                     │
│   前端调用:   fetch('http://localhost:8000/api/topics')                 │
│                                                                         │
│   ❌ 报错: Access to fetch has been blocked by CORS policy              │
│                                                                         │
│   原因: 浏览器同源策略                                                  │
│   - 源 = 协议 + 域名 + 端口                                             │
│   - localhost:5173 ≠ localhost:8000                                     │
│   - 浏览器禁止跨源请求（安全机制）                                      │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   问题 2: 生产环境访问混乱                                              │
│   ─────────────────────────                                             │
│   用户需要知道两个地址:                                                 │
│   - 页面: http://example.com:80                                         │
│   - API: http://example.com:8000/api                                    │
│                                                                         │
│   前端代码需要硬编码后端地址:                                           │
│   const API_URL = 'http://example.com:8000'  // 不同环境要改            │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   问题 3: 端口暴露，安全隐患                                            │
│   ─────────────────────────────                                         │
│   - 8000 端口对外暴露                                                   │
│   - 数据库端口 5432 可能也暴露                                          │
│   - 攻击面增大                                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Nginx 反向代理如何解决这些问题

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    有 Nginx 的架构                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   用户浏览器                                                            │
│       │                                                                 │
│       │  所有请求都发到 http://example.com (端口 80)                    │
│       ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                        Nginx (端口 80)                          │  │
│   │                                                                 │  │
│   │   请求 /              → 返回 index.html (静态文件)              │  │
│   │   请求 /assets/*      → 返回静态资源                            │  │
│   │   请求 /api/*         → 转发到 backend:8000                     │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│           │                                    │                        │
│           │ 静态文件                           │ 代理转发               │
│           ▼                                    ▼                        │
│   ┌───────────────────┐              ┌───────────────────┐             │
│   │  /usr/share/      │              │   FastAPI         │             │
│   │  nginx/html/      │              │   (端口 8000)     │             │
│   │  - index.html     │              │   内部网络,不暴露 │             │
│   │  - assets/        │              │                   │             │
│   └───────────────────┘              └───────────────────┘             │
│                                                                         │
│   解决的问题:                                                           │
│   ──────────                                                            │
│   ✅ 跨域: 所有请求都是 example.com:80，同源！                         │
│   ✅ 统一入口: 用户只需要知道一个地址                                   │
│   ✅ 安全: 后端服务不直接暴露，只有 Nginx 对外                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Nginx 配置详解

```nginx
# nginx.conf - TCGS 项目配置

server {
    listen 80;                    # 监听 80 端口
    server_name _;                # 匹配所有域名

    # ═══════════════════════════════════════════════════════════════════
    # 静态文件服务 + SPA 路由支持
    # ═══════════════════════════════════════════════════════════════════
    root /usr/share/nginx/html;   # Vue 构建产物目录
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
        #
        # 这行配置非常关键！解释：
        # 1. 用户访问 /topics
        # 2. Nginx 先找 /topics 文件 → 不存在
        # 3. 再找 /topics/ 目录 → 不存在
        # 4. 最后返回 /index.html
        # 5. Vue Router 在前端处理 /topics 路由
        #
        # 如果没有这行，刷新页面会 404！
        # 因为 /topics 是前端路由，服务器上没有这个文件
    }

    # ═══════════════════════════════════════════════════════════════════
    # API 反向代理 (核心！)
    # ═══════════════════════════════════════════════════════════════════
    location /api/ {
        proxy_pass http://backend:8000;
        #
        # 请求转发示例：
        # 用户请求: GET http://example.com/api/topics
        # Nginx 转发: GET http://backend:8000/api/topics
        #
        # backend 是 Docker 服务名，Docker 内部 DNS 自动解析

        proxy_http_version 1.1;

        # 传递客户端真实信息给后端
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ═══════════════════════════════════════════════════════════════════
    # FastAPI 自动文档
    # ═══════════════════════════════════════════════════════════════════
    location /docs {
        proxy_pass http://backend:8000/docs;
    }

    location /openapi.json {
        proxy_pass http://backend:8000/openapi.json;
    }
}
```

### 8.4 Nginx 的多重角色

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Nginx 在 TCGS 中的四个角色                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   角色 1: 静态文件服务器                                                │
│   ─────────────────────                                                 │
│   请求: /index.html, /assets/logo.png, /favicon.ico                    │
│   处理: 直接从磁盘读取文件返回                                          │
│   优势: Nginx 处理静态文件比 Python 快 10 倍以上                        │
│                                                                         │
│   角色 2: SPA 路由支持                                                  │
│   ─────────────────────                                                 │
│   请求: /topics, /capacity, /wiki/pages/123                            │
│   处理: try_files 找不到 → 返回 index.html → Vue Router 处理           │
│   意义: 让前端路由在刷新后也能正常工作                                  │
│                                                                         │
│   角色 3: API 反向代理                                                  │
│   ─────────────────────                                                 │
│   请求: /api/*                                                          │
│   处理: 转发到 backend:8000                                             │
│   意义: 解决跨域、隐藏后端服务                                          │
│                                                                         │
│   角色 4: 统一入口 (API 网关雏形)                                       │
│   ─────────────────────────────                                         │
│   所有请求通过 80 端口进入                                              │
│   未来可以扩展:                                                         │
│   - /api/v1/* → backend-v1:8000                                        │
│   - /api/v2/* → backend-v2:8000                                        │
│   - 负载均衡、限流、SSL 终止等                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.5 请求流转完整示例

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    场景：用户访问课题列表页                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   步骤 1: 用户在浏览器输入 http://example.com/topics                    │
│           │                                                             │
│           ▼                                                             │
│   步骤 2: Nginx 收到请求                                                │
│           - 匹配 location / { try_files ... }                          │
│           - 找 /topics 文件 → 不存在                                   │
│           - 返回 /index.html                                           │
│           │                                                             │
│           ▼                                                             │
│   步骤 3: 浏览器加载 index.html                                         │
│           - 下载 Vue 应用 JS/CSS                                        │
│           - Vue Router 解析 /topics 路由                                │
│           - 渲染 TopicsListView 组件                                    │
│           │                                                             │
│           ▼                                                             │
│   步骤 4: Vue 组件发起 API 请求                                         │
│           fetch('/api/topics')                                          │
│           // 注意是相对路径，同源，无跨域问题！                         │
│           │                                                             │
│           ▼                                                             │
│   步骤 5: Nginx 收到 /api/topics 请求                                   │
│           - 匹配 location /api/ { proxy_pass ... }                     │
│           - 转发到 http://backend:8000/api/topics                      │
│           │                                                             │
│           ▼                                                             │
│   步骤 6: FastAPI 处理请求                                              │
│           - 验证 JWT Token                                              │
│           - 查询数据库                                                  │
│           - 返回 JSON                                                   │
│           │                                                             │
│           ▼                                                             │
│   步骤 7: Nginx 把响应返回给浏览器                                      │
│           │                                                             │
│           ▼                                                             │
│   步骤 8: Vue 渲染课题列表                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.6 为什么不直接在 FastAPI 里配置 CORS？

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CORS vs Nginx 代理                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   方案 A: 后端配置 CORS (开发环境常用)                                  │
│   ─────────────────────────────────────                                 │
│   # FastAPI 配置                                                        │
│   app.add_middleware(                                                   │
│       CORSMiddleware,                                                   │
│       allow_origins=["http://localhost:5173"],  # 允许前端地址          │
│       allow_methods=["*"],                                              │
│       allow_headers=["*"],                                              │
│   )                                                                     │
│                                                                         │
│   问题:                                                                 │
│   - 需要维护 allow_origins 列表                                         │
│   - 每个环境地址都要加进去                                              │
│   - 安全性较低（允许跨域意味着任何网站都能调用你的 API）                │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   方案 B: Nginx 反向代理 (生产环境推荐)                                 │
│   ─────────────────────────────────────                                 │
│   所有请求都通过 Nginx，前端和 API 同源                                 │
│                                                                         │
│   优势:                                                                 │
│   - 根本不存在跨域问题（同源）                                          │
│   - 无需维护白名单                                                      │
│   - 后端服务不直接暴露，更安全                                          │
│   - 静态文件服务更高效                                                  │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   TCGS 项目的选择:                                                      │
│   ────────────────                                                      │
│   - 开发环境: FastAPI CORS (方便 Vite 热重载)                           │
│   - 生产环境: Nginx 代理 (安全、高效)                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. 对象存储：MinIO 是什么

TCGS 项目中有个 MinIO 服务，很多人不知道它是干什么的。这一章我们来解释：为什么需要对象存储，MinIO 解决什么问题。

### 9.1 传统文件存储的问题

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    场景：用户上传课题附件                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   传统方案：存到服务器本地文件系统                                      │
│   ──────────────────────────────────                                    │
│   /app/uploads/                                                         │
│   ├── topic_1/                                                          │
│   │   ├── report.pdf                                                    │
│   │   └── data.xlsx                                                     │
│   ├── topic_2/                                                          │
│   │   └── slides.pptx                                                   │
│   └── ...                                                               │
│                                                                         │
│   问题 1: 容器重启文件丢失                                              │
│   ─────────────────────────                                             │
│   Docker 容器是无状态的！                                               │
│   docker compose down → 容器删除 → /app/uploads/ 目录消失               │
│                                                                         │
│   问题 2: 多实例无法共享                                                │
│   ─────────────────────                                                 │
│   如果部署多个后端实例做负载均衡:                                       │
│   - 用户 A 上传到 backend-1                                             │
│   - 用户 B 请求到 backend-2 → 找不到文件！                              │
│                                                                         │
│   问题 3: 备份和迁移困难                                                │
│   ─────────────────────                                                 │
│   - 文件分散在服务器各处                                                │
│   - 需要手动同步到备份服务器                                            │
│   - 迁移时容易遗漏                                                      │
│                                                                         │
│   问题 4: 无法直接对外提供下载链接                                      │
│   ───────────────────────────────                                       │
│   文件在后端容器内，用户下载需要:                                       │
│   请求 → 后端读取文件 → 返回文件流                                      │
│   后端成为瓶颈，占用大量内存和带宽                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 对象存储是什么

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    对象存储 vs 文件系统                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   文件系统 (传统):                                                      │
│   ─────────────────                                                     │
│   /home/user/documents/project/report.pdf                               │
│   - 层级目录结构                                                        │
│   - 文件有路径、权限、修改时间等属性                                    │
│   - 依赖操作系统                                                        │
│                                                                         │
│   对象存储 (现代):                                                      │
│   ─────────────────                                                     │
│   Bucket: tcgs-attachments                                              │
│   Object Key: topics/1/report.pdf                                       │
│   - 扁平的键值存储 (Key → Object)                                       │
│   - 每个对象有元数据 (大小、类型、自定义属性)                           │
│   - 通过 HTTP API 访问                                                  │
│   - 天然支持分布式、高可用                                              │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                        对象存储架构                             │  │
│   │                                                                 │  │
│   │   ┌─────────────────────────────────────────────────────────┐  │  │
│   │   │                    Bucket (桶)                          │  │  │
│   │   │                    tcgs-attachments                     │  │  │
│   │   │                                                         │  │  │
│   │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │  │
│   │   │   │   Object    │  │   Object    │  │   Object    │    │  │  │
│   │   │   │ topics/1/   │  │ topics/2/   │  │ wiki/pages/ │    │  │  │
│   │   │   │ report.pdf  │  │ data.xlsx   │  │ image.png   │    │  │  │
│   │   │   │             │  │             │  │             │    │  │  │
│   │   │   │ 元数据:     │  │ 元数据:     │  │ 元数据:     │    │  │  │
│   │   │   │ size: 2MB   │  │ size: 500KB │  │ size: 100KB │    │  │  │
│   │   │   │ type: pdf   │  │ type: xlsx  │  │ type: image │    │  │  │
│   │   │   └─────────────┘  └─────────────┘  └─────────────┘    │  │  │
│   │   │                                                         │  │  │
│   │   └─────────────────────────────────────────────────────────┘  │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.3 MinIO：自己搭建的 S3

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MinIO 是什么                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Amazon S3 (Simple Storage Service):                                   │
│   ────────────────────────────────────                                  │
│   - AWS 的对象存储服务                                                  │
│   - 业界标准，几乎所有云厂商都兼容 S3 API                               │
│   - 按存储量和流量收费                                                  │
│                                                                         │
│   MinIO:                                                                │
│   ──────                                                                │
│   - 开源的 S3 兼容存储                                                  │
│   - 可以自己部署，完全免费                                              │
│   - API 与 S3 100% 兼容                                                 │
│   - 适合开发环境、私有云、边缘计算                                      │
│                                                                         │
│   类比:                                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │   MySQL (商业版)     ←→   MariaDB (开源替代)                    │  │
│   │   Amazon S3 (云服务) ←→   MinIO (开源替代)                      │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   TCGS 项目选择 MinIO 的理由:                                           │
│   ────────────────────────────                                          │
│   ✅ 开发环境免费，不需要 AWS 账号                                      │
│   ✅ Docker 一键启动                                                    │
│   ✅ 与 S3 API 兼容，生产环境可无缝切换到 AWS S3                        │
│   ✅ 自带 Web 管理界面 (端口 9001)                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.4 MinIO 在 TCGS 中的使用

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    文件上传流程                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   用户上传附件                                                          │
│       │                                                                 │
│       ▼                                                                 │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │  Vue 前端                                                     │    │
│   │  <input type="file" @change="handleUpload">                   │    │
│   │  → FormData 包装文件                                          │    │
│   │  → POST /api/attachments/upload                               │    │
│   └───────────────────────────────────────────────────────────────┘    │
│       │                                                                 │
│       ▼                                                                 │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │  FastAPI 后端                                                 │    │
│   │                                                               │    │
│   │  @router.post("/upload")                                      │    │
│   │  async def upload_file(file: UploadFile):                     │    │
│   │      # 生成唯一文件名                                         │    │
│   │      object_key = f"topics/{topic_id}/{uuid4()}_{file.name}" │    │
│   │                                                               │    │
│   │      # 上传到 MinIO                                           │    │
│   │      minio_client.put_object(                                 │    │
│   │          bucket="tcgs-attachments",                           │    │
│   │          object_key=object_key,                               │    │
│   │          data=file.file,                                      │    │
│   │          length=file.size                                     │    │
│   │      )                                                        │    │
│   │                                                               │    │
│   │      # 保存文件信息到数据库                                   │    │
│   │      attachment = Attachment(                                 │    │
│   │          topic_id=topic_id,                                   │    │
│   │          filename=file.filename,                              │    │
│   │          object_key=object_key,                               │    │
│   │          size=file.size                                       │    │
│   │      )                                                        │    │
│   │      db.add(attachment)                                       │    │
│   │      db.commit()                                              │    │
│   │                                                               │    │
│   │      return {"id": attachment.id, "url": f"/api/files/{id}"}  │    │
│   └───────────────────────────────────────────────────────────────┘    │
│       │                                                                 │
│       ▼                                                                 │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │  MinIO 存储                                                   │    │
│   │  Bucket: tcgs-attachments                                     │    │
│   │  Object: topics/1/abc123_report.pdf                           │    │
│   │                                                               │    │
│   │  数据持久化到 Docker Volume: minio_data                       │    │
│   └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.5 MinIO 解决的问题

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MinIO 带来的好处                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   问题 1: 容器重启文件丢失                                              │
│   解决: MinIO 数据存储在 Docker Volume，独立于容器                      │
│         docker compose down → 容器删除 → minio_data 保留               │
│                                                                         │
│   问题 2: 多实例无法共享                                                │
│   解决: 所有后端实例都连接同一个 MinIO                                  │
│         backend-1 上传 → MinIO → backend-2 可以读取                    │
│                                                                         │
│   问题 3: 备份和迁移困难                                                │
│   解决: MinIO 提供标准 API，可以用 mc (MinIO Client) 工具同步          │
│         mc mirror minio/tcgs-attachments backup/                       │
│                                                                         │
│   问题 4: 后端成为文件下载瓶颈                                          │
│   解决: MinIO 支持预签名 URL，用户直接从 MinIO 下载                     │
│         # 生成临时下载链接 (有效期 1 小时)                              │
│         url = minio_client.presigned_get_object(                        │
│             bucket="tcgs-attachments",                                  │
│             object_key="topics/1/report.pdf",                           │
│             expires=timedelta(hours=1)                                  │
│         )                                                               │
│         # 返回: http://minio:9000/tcgs-attachments/topics/1/report.pdf?签名
│         # 用户直接访问这个 URL 下载，不经过后端                         │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   生产环境迁移:                                                         │
│   ──────────────                                                        │
│   开发环境: MinIO (本地 Docker)                                         │
│   生产环境: AWS S3 / 阿里云 OSS / 腾讯云 COS                            │
│                                                                         │
│   因为 API 兼容，只需要改配置:                                          │
│   # 开发环境                                                            │
│   MINIO_ENDPOINT=minio:9000                                             │
│   MINIO_ACCESS_KEY=minioadmin                                           │
│                                                                         │
│   # 生产环境 (切换到 AWS S3)                                            │
│   S3_ENDPOINT=s3.amazonaws.com                                          │
│   S3_ACCESS_KEY=AKIA...                                                 │
│   # 代码不用改！                                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.6 MinIO 管理界面

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MinIO Console (Web 管理界面)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   访问: http://localhost:9001                                           │
│   账号: minioadmin                                                      │
│   密码: minioadmin                                                      │
│                                                                         │
│   功能:                                                                 │
│   - 查看所有 Bucket                                                     │
│   - 浏览和下载文件                                                      │
│   - 上传文件 (用于测试)                                                 │
│   - 设置访问策略                                                        │
│   - 查看存储统计                                                        │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  MinIO Console                                      [minioadmin]│  │
│   ├─────────────────────────────────────────────────────────────────┤  │
│   │  Buckets                                                        │  │
│   │  ┌───────────────────────────────────────────────────────────┐ │  │
│   │  │ 📁 tcgs-attachments                                       │ │  │
│   │  │    Objects: 156                                           │ │  │
│   │  │    Size: 234 MB                                           │ │  │
│   │  │    Created: 2026-04-01                                    │ │  │
│   │  └───────────────────────────────────────────────────────────┘ │  │
│   │                                                                 │  │
│   │  Recent Objects                                                 │  │
│   │  ├─ topics/1/report.pdf           2.3 MB    10 min ago        │  │
│   │  ├─ topics/1/data.xlsx            456 KB    1 hour ago        │  │
│   │  └─ wiki/pages/3/diagram.png      89 KB     2 hours ago       │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. 系统架构图与请求流转

前面我们分别介绍了各个技术组件，这一章我们把它们串联起来，看看整个系统是如何协同工作的。

### 10.1 部署架构全景图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           TCGS 部署架构                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                              用户浏览器                                 │
│                                  │                                      │
│                                  │ HTTP (Port 80)                       │
│                                  ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    Docker Network: tcgs_default                 │  │
│   │                                                                 │  │
│   │  ┌───────────────────────────────────────────────────────────┐ │  │
│   │  │              tcgs-frontend (Nginx)                        │ │  │
│   │  │                                                           │ │  │
│   │  │   /              → Vue 静态文件 (index.html, JS, CSS)     │ │  │
│   │  │   /api/*         → proxy_pass http://backend:8000         │ │  │
│   │  │   /docs          → proxy_pass http://backend:8000/docs    │ │  │
│   │  └───────────────────────────────────────────────────────────┘ │  │
│   │                              │                                  │  │
│   │                              ▼                                  │  │
│   │  ┌───────────────────────────────────────────────────────────┐ │  │
│   │  │              tcgs-backend (FastAPI + Uvicorn)             │ │  │
│   │  │                                                           │ │  │
│   │  │   /api/auth/*      → JWT 认证                             │ │  │
│   │  │   /api/topics/*    → 课题 CRUD                            │ │  │
│   │  │   /api/capacity/*  → 产能管理                             │ │  │
│   │  │   /api/wiki/*      → 知识库                               │ │  │
│   │  │   /api/upload/*    → 文件上传 (→ MinIO)                   │ │  │
│   │  └───────────────────────────────────────────────────────────┘ │  │
│   │              │                              │                   │  │
│   │              ▼                              ▼                   │  │
│   │  ┌─────────────────────┐      ┌─────────────────────┐          │  │
│   │  │   tcgs-postgres     │      │    tcgs-minio       │          │  │
│   │  │   PostgreSQL 15     │      │    MinIO (S3)       │          │  │
│   │  │                     │      │                     │          │  │
│   │  │   - users           │      │   Bucket:           │          │  │
│   │  │   - topics          │      │   tcgs-attachments  │          │  │
│   │  │   - wiki_pages      │      │                     │          │  │
│   │  │   - capacity_slots  │      │   Port: 9000 (API)  │          │  │
│   │  │   - ...             │      │   Port: 9001 (Web)  │          │  │
│   │  └─────────────────────┘      └─────────────────────┘          │  │
│   │              │                              │                   │  │
│   │              ▼                              ▼                   │  │
│   │  ┌─────────────────────┐      ┌─────────────────────┐          │  │
│   │  │   postgres_data     │      │    minio_data       │          │  │
│   │  │   (Docker Volume)   │      │   (Docker Volume)   │          │  │
│   │  └─────────────────────┘      └─────────────────────┘          │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 完整请求流转示例

**场景：用户登录后创建一个课题**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    完整请求流转 (12 个步骤)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ══════════════════════════════════════════════════════════════════   │
│   阶段 1: 用户登录                                                      │
│   ══════════════════════════════════════════════════════════════════   │
│                                                                         │
│   1️⃣ 用户在 LoginView.vue 输入账号密码，点击登录                        │
│      │                                                                  │
│      ▼                                                                  │
│   2️⃣ authStore.login({ email, password })                              │
│      │                                                                  │
│      ▼                                                                  │
│   3️⃣ Axios: POST /api/auth/login                                       │
│      │   { "email": "user@example.com", "password": "xxx" }             │
│      │                                                                  │
│      ▼                                                                  │
│   4️⃣ Nginx: proxy_pass → http://backend:8000/api/auth/login            │
│      │                                                                  │
│      ▼                                                                  │
│   5️⃣ FastAPI: 验证密码 → 生成 JWT Token                                 │
│      │   response: { "access_token": "eyJhbG...", "user": {...} }      │
│      │                                                                  │
│      ▼                                                                  │
│   6️⃣ authStore: 保存 token 到 localStorage，更新 user 状态             │
│      │                                                                  │
│      ▼                                                                  │
│   7️⃣ Vue Router: 跳转到 /dashboard                                     │
│                                                                         │
│   ══════════════════════════════════════════════════════════════════   │
│   阶段 2: 创建课题                                                      │
│   ══════════════════════════════════════════════════════════════════   │
│                                                                         │
│   8️⃣ 用户在 TopicsListView.vue 点击"创建课题"                          │
│      │   填写表单：标题、类型、紧急度等                                 │
│      │                                                                  │
│      ▼                                                                  │
│   9️⃣ topicsStore.createTopic(formData)                                 │
│      │   loading.value = true                                           │
│      │                                                                  │
│      ▼                                                                  │
│   🔟 Axios: POST /api/topics                                            │
│      │   Headers: { Authorization: "Bearer eyJhbG..." }                │
│      │   Body: { "title": "新课题", "type": "RESEARCH", ... }          │
│      │                                                                  │
│      ▼                                                                  │
│   1️⃣1️⃣ FastAPI:                                                         │
│      │   - 依赖注入: get_current_user() 验证 JWT                        │
│      │   - Pydantic: TopicCreate 验证数据格式                           │
│      │   - SQLAlchemy: topic = Topic(**data); db.add(topic)            │
│      │   - PostgreSQL: INSERT INTO topics ... RETURNING id             │
│      │   - 如果有模板: 自动创建 stage_instances                         │
│      │                                                                  │
│      ▼                                                                  │
│   1️⃣2️⃣ 响应返回:                                                        │
│       - FastAPI → Nginx → Axios → topicsStore                          │
│       - topics.value.push(newTopic)                                    │
│       - loading.value = false                                          │
│       - Vue 响应式: 课题列表自动更新，显示新课题                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.3 项目目录结构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TCGS 项目完整目录结构                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   tcgs/                                                                 │
│   │                                                                     │
│   │   ═══════════════════ 前端 (Vue 3) ═══════════════════             │
│   ├── src/                                                              │
│   │   ├── main.ts              # 应用入口，挂载 Vue/Pinia/Router       │
│   │   ├── App.vue              # 根组件                                │
│   │   ├── router/index.ts      # 路由配置 + 路由守卫                   │
│   │   ├── stores/              # Pinia 状态管理                        │
│   │   │   ├── auth.ts          #   认证状态 (token, user)              │
│   │   │   ├── topics.ts        #   课题状态                            │
│   │   │   ├── capacity.ts      #   产能状态                            │
│   │   │   └── wiki.ts          #   Wiki 状态                           │
│   │   ├── api/                 # API 服务层                            │
│   │   │   ├── client.ts        #   Axios 配置 (拦截器、Token)          │
│   │   │   ├── topics.ts        #   课题 API 封装                       │
│   │   │   └── ...                                                      │
│   │   ├── views/               # 页面组件                              │
│   │   │   ├── LoginView.vue                                            │
│   │   │   ├── topics/TopicsListView.vue                                │
│   │   │   └── ...                                                      │
│   │   ├── components/          # 通用组件                              │
│   │   └── types/index.ts       # TypeScript 类型定义                   │
│   │                                                                     │
│   │   ═══════════════════ 后端 (FastAPI) ═══════════════════           │
│   ├── backend/                                                          │
│   │   ├── app/                                                          │
│   │   │   ├── main.py          # FastAPI 应用入口                      │
│   │   │   ├── config.py        # 配置管理 (环境变量)                   │
│   │   │   ├── database.py      # 数据库连接 (SQLAlchemy)               │
│   │   │   ├── api/             # API 路由                              │
│   │   │   │   ├── __init__.py  #   路由聚合                            │
│   │   │   │   ├── auth.py      #   /api/auth/*                         │
│   │   │   │   ├── topics.py    #   /api/topics/*                       │
│   │   │   │   └── ...                                                  │
│   │   │   ├── models/          # SQLAlchemy ORM 模型                   │
│   │   │   │   ├── user.py                                              │
│   │   │   │   ├── topic.py                                             │
│   │   │   │   └── ...                                                  │
│   │   │   ├── schemas/         # Pydantic 数据验证                     │
│   │   │   └── services/        # 业务逻辑层                            │
│   │   ├── alembic/             # 数据库迁移                            │
│   │   │   └── versions/        #   迁移脚本                            │
│   │   ├── requirements.txt     # Python 依赖                           │
│   │   └── Dockerfile           # 后端镜像构建                          │
│   │                                                                     │
│   │   ═══════════════════ 部署配置 ═══════════════════                 │
│   ├── docker-compose.yml       # 多容器编排                            │
│   ├── Dockerfile.frontend      # 前端镜像 (多阶段构建)                 │
│   ├── nginx.conf               # Nginx 配置                            │
│   └── .env                     # 环境变量                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.4 技术栈协同关系

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    技术栈协同关系图                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   前端 (浏览器)                    后端 (服务器)                        │
│   ─────────────                    ─────────────                        │
│                                                                         │
│   ┌─────────────┐                 ┌─────────────┐                      │
│   │ TypeScript  │ ═══类型对应═══▶ │  Pydantic   │                      │
│   │ interface   │                 │  BaseModel  │                      │
│   │             │                 │             │                      │
│   │ Topic {     │                 │ TopicCreate │                      │
│   │   id: number│                 │   title: str│                      │
│   │   title: str│                 │   type: Enum│                      │
│   │ }           │                 │ }           │                      │
│   └─────────────┘                 └─────────────┘                      │
│         │                               │                               │
│         │                               │                               │
│         ▼                               ▼                               │
│   ┌─────────────┐                 ┌─────────────┐                      │
│   │   Axios     │ ══HTTP 请求══▶  │   FastAPI   │                      │
│   │             │                 │   Router    │                      │
│   │ camelCase   │ ══自动转换══▶   │ snake_case  │                      │
│   │ userId      │                 │ user_id     │                      │
│   └─────────────┘                 └─────────────┘                      │
│         │                               │                               │
│         │                               │                               │
│         ▼                               ▼                               │
│   ┌─────────────┐                 ┌─────────────┐                      │
│   │   Pinia     │ ◀══JSON 响应══  │ SQLAlchemy  │                      │
│   │   Store     │                 │   ORM       │                      │
│   │             │                 │             │                      │
│   │ topics: []  │                 │ Topic model │                      │
│   │ loading: T/F│                 │   ↓         │                      │
│   └─────────────┘                 │ PostgreSQL  │                      │
│         │                         └─────────────┘                      │
│         │                                                               │
│         ▼                                                               │
│   ┌─────────────┐                                                      │
│   │    Vue 3    │                                                      │
│   │  响应式渲染  │                                                      │
│   │             │                                                      │
│   │ 数据变化    │                                                      │
│   │   ↓         │                                                      │
│   │ 自动更新DOM │                                                      │
│   └─────────────┘                                                      │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   关键转换点:                                                           │
│   1. TypeScript interface ↔ Pydantic BaseModel (类型一致性)            │
│   2. camelCase ↔ snake_case (Axios 拦截器自动转换)                     │
│   3. Pinia 响应式 → Vue 自动更新 (无需手动操作 DOM)                    │
│   4. SQLAlchemy ORM → SQL (无需手写 SQL)                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Vue 响应式原理

Vue 3 的响应式系统是其核心特性，理解它有助于写出更高效的代码。

### 11.1 什么是响应式？

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      响应式的本质                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   传统方式 (命令式):                                                    │
│   ─────────────────────                                                 │
│   let count = 0                                                         │
│   document.getElementById('counter').innerHTML = count                  │
│                                                                         │
│   function increment() {                                                │
│       count++                                                           │
│       document.getElementById('counter').innerHTML = count  // 手动更新 │
│   }                                                                     │
│   问题: 每次数据变化都要手动更新 DOM                                    │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   Vue 响应式 (声明式):                                                  │
│   ─────────────────────                                                 │
│   const count = ref(0)                                                  │
│                                                                         │
│   <template>                                                            │
│     <span>{{ count }}</span>   <!-- 自动绑定 -->                        │
│     <button @click="count++">+1</button>                                │
│   </template>                                                           │
│                                                                         │
│   优势: 数据变化自动更新 DOM, 开发者只需关注数据                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Vue 3 Proxy 实现原理

```
┌─────────────────────────────────────────────────────────────────────────┐
│                Vue 3 Proxy 响应式原理                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   简化版实现:                                                           │
│   ─────────────                                                         │
│   function reactive(target) {                                           │
│       return new Proxy(target, {                                        │
│           get(obj, key) {                                               │
│               track(obj, key)    // 收集依赖: 谁在用这个数据？          │
│               return obj[key]                                           │
│           },                                                            │
│           set(obj, key, value) {                                        │
│               obj[key] = value                                          │
│               trigger(obj, key)  // 触发更新: 通知使用者数据变了        │
│               return true                                               │
│           }                                                             │
│       })                                                                │
│   }                                                                     │
│                                                                         │
│   工作流程:                                                             │
│   ─────────                                                             │
│   1. 组件渲染时读取 state.count → Proxy get 拦截 → track()             │
│      记录: "这个组件依赖 state.count"                                   │
│                                                                         │
│   2. 用户点击按钮 state.count++ → Proxy set 拦截 → trigger()           │
│      通知: "所有依赖 state.count 的组件，重新渲染！"                    │
│                                                                         │
│   3. Vue 调度器批量更新 DOM (微任务队列，高效)                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.3 为什么需要 key？

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Virtual DOM Diff 与 key                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   没有 key 的情况 (低效):                                               │
│   ───────────────────────                                               │
│   旧列表:                      新列表:                                  │
│   <li>课题A</li>               <li>课题C</li>  ← 内容替换               │
│   <li>课题B</li>       →       <li>课题A</li>  ← 内容替换               │
│                                <li>课题B</li>  ← 新增                   │
│                                                                         │
│   执行了 3 次 DOM 操作                                                  │
│                                                                         │
│   有 key 的情况 (高效):                                                 │
│   ─────────────────────                                                 │
│   旧列表:                      新列表:                                  │
│   <li key="1">课题A</li>       <li key="3">课题C</li>  ← 只新增         │
│   <li key="2">课题B</li>  →    <li key="1">课题A</li>  ← 复用+移动      │
│                                <li key="2">课题B</li>  ← 复用           │
│                                                                         │
│   Vue 通过 key 识别"这是同一个元素"，只做必要的 DOM 操作               │
│                                                                         │
│   最佳实践:                                                             │
│   ──────────                                                            │
│   <li v-for="topic in topics" :key="topic.id">  ← 使用唯一 ID          │
│       {{ topic.title }}                                                 │
│   </li>                                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 12. 4+1 视图模型

### 12.1 逻辑视图 (Logical View)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    逻辑视图 - 功能分解                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                        ┌─────────────────┐                              │
│                        │   TCGS System   │                              │
│                        └────────┬────────┘                              │
│                                 │                                       │
│       ┌─────────────┬───────────┼───────────┬─────────────┐            │
│       ▼             ▼           ▼           ▼             ▼            │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ │
│ │   Auth    │ │  Topics   │ │ Capacity  │ │   Wiki    │ │ Insights  │ │
│ │   Module  │ │  Module   │ │  Module   │ │  Module   │ │  Module   │ │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘ │
│      │             │             │             │             │         │
│      ▼             ▼             ▼             ▼             ▼         │
│ ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   │
│ │  User   │   │  Topic  │   │  Slot   │   │  Page   │   │  Stats  │   │
│ │ Session │   │ Stage   │   │ Binding │   │Revision │   │  KPIs   │   │
│ │  JWT    │   │TechPoint│   │Workload │   │ Comment │   │ Charts  │   │
│ └─────────┘   │CoreIdea │   └─────────┘   └─────────┘   └─────────┘   │
│               └─────────┘                                              │
│                                                                         │
│   职责分配:                                                             │
│   ──────────                                                            │
│   Auth:     用户认证、授权、会话管理                                    │
│   Topics:   课题 CRUD、阶段流转、评审、交付物                           │
│   Capacity: 槽位管理、人员绑定、工作量统计                              │
│   Wiki:     文档管理、版本控制、评论互动                                │
│   Insights: 数据聚合、KPI 计算、可视化                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.2 开发视图 (Development View)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    开发视图 - 代码组织                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                        前端包 (Frontend)                        │  │
│   ├─────────────────────────────────────────────────────────────────┤  │
│   │                                                                 │  │
│   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │  │
│   │   │    Views      │  │    Stores     │  │     API       │      │  │
│   │   │   (Pages)     │  │   (Pinia)     │  │   (Axios)     │      │  │
│   │   ├───────────────┤  ├───────────────┤  ├───────────────┤      │  │
│   │   │ Dashboard     │  │ authStore     │  │ auth.ts       │      │  │
│   │   │ Topics        │  │ topicsStore   │  │ topics.ts     │      │  │
│   │   │ Capacity      │  │ capacityStore │  │ capacity.ts   │      │  │
│   │   │ Wiki          │  │ wikiStore     │  │ wiki.ts       │      │  │
│   │   │ Insights      │  │ usersStore    │  │ insights.ts   │      │  │
│   │   └───────────────┘  └───────────────┘  └───────────────┘      │  │
│   │           │                  │                  │               │  │
│   │           └──────────────────┼──────────────────┘               │  │
│   │                              ▼                                  │  │
│   │   ┌─────────────────────────────────────────────────────────┐  │  │
│   │   │                    Components                           │  │  │
│   │   │  common/  │  topic/  │  wiki/  │  capacity/            │  │  │
│   │   └─────────────────────────────────────────────────────────┘  │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                        后端包 (Backend)                         │  │
│   ├─────────────────────────────────────────────────────────────────┤  │
│   │                                                                 │  │
│   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │  │
│   │   │     API       │  │    Models     │  │   Services    │      │  │
│   │   │   (Routes)    │  │ (SQLAlchemy)  │  │   (Logic)     │      │  │
│   │   ├───────────────┤  ├───────────────┤  ├───────────────┤      │  │
│   │   │ auth.py       │  │ user.py       │  │ auth.py       │      │  │
│   │   │ topics.py     │  │ topic.py      │  │ audit.py      │      │  │
│   │   │ capacity.py   │  │ capacity.py   │  │ storage.py    │      │  │
│   │   │ wiki.py       │  │ wiki.py       │  │               │      │  │
│   │   │ insights.py   │  │ stage.py      │  │               │      │  │
│   │   └───────────────┘  └───────────────┘  └───────────────┘      │  │
│   │           │                  │                  │               │  │
│   │           └──────────────────┼──────────────────┘               │  │
│   │                              ▼                                  │  │
│   │   ┌─────────────────────────────────────────────────────────┐  │  │
│   │   │                     Schemas                             │  │  │
│   │   │              (Pydantic Validation)                      │  │  │
│   │   └─────────────────────────────────────────────────────────┘  │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   依赖关系:                                                             │
│   ──────────                                                            │
│   Views → Stores → API → Backend Routes → Models → Database            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.3 进程视图 (Process View)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    进程视图 - 运行时架构                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                     Docker Host                                 │  │
│   ├─────────────────────────────────────────────────────────────────┤  │
│   │                                                                 │  │
│   │   Process: tcgs-frontend (Nginx)                                │  │
│   │   ┌───────────────────────────────────────────────────────────┐│  │
│   │   │  Master Process (PID 1)                                   ││  │
│   │   │      │                                                    ││  │
│   │   │      ├── Worker Process 1 (静态文件 + 代理)               ││  │
│   │   │      └── Worker Process 2 (静态文件 + 代理)               ││  │
│   │   │                                                           ││  │
│   │   │  监听: 0.0.0.0:80                                         ││  │
│   │   │  角色: 反向代理, 静态文件服务                              ││  │
│   │   └───────────────────────────────────────────────────────────┘│  │
│   │                                                                 │  │
│   │   Process: tcgs-backend (Uvicorn + FastAPI)                     │  │
│   │   ┌───────────────────────────────────────────────────────────┐│  │
│   │   │  Uvicorn Server (PID 1)                                   ││  │
│   │   │      │                                                    ││  │
│   │   │      ├── Event Loop (asyncio)                             ││  │
│   │   │      │      ├── HTTP Handler                              ││  │
│   │   │      │      ├── Database Connection Pool                  ││  │
│   │   │      │      └── MinIO Client                              ││  │
│   │   │      │                                                    ││  │
│   │   │      └── File Watcher (--reload 模式)                     ││  │
│   │   │                                                           ││  │
│   │   │  监听: 0.0.0.0:8000                                       ││  │
│   │   │  角色: API 服务, 业务逻辑                                  ││  │
│   │   └───────────────────────────────────────────────────────────┘│  │
│   │                                                                 │  │
│   │   Process: tcgs-postgres (PostgreSQL)                           │  │
│   │   ┌───────────────────────────────────────────────────────────┐│  │
│   │   │  Postmaster (PID 1)                                       ││  │
│   │   │      │                                                    ││  │
│   │   │      ├── Background Writer                                ││  │
│   │   │      ├── WAL Writer                                       ││  │
│   │   │      ├── Checkpointer                                     ││  │
│   │   │      └── Client Connections (per connection)              ││  │
│   │   │                                                           ││  │
│   │   │  监听: 0.0.0.0:5432                                       ││  │
│   │   │  角色: 数据持久化                                          ││  │
│   │   └───────────────────────────────────────────────────────────┘│  │
│   │                                                                 │  │
│   │   Process: tcgs-minio (MinIO)                                   │  │
│   │   ┌───────────────────────────────────────────────────────────┐│  │
│   │   │  MinIO Server (PID 1)                                     ││  │
│   │   │      │                                                    ││  │
│   │   │      ├── S3 API Handler (Port 9000)                       ││  │
│   │   │      └── Console Handler (Port 9001)                      ││  │
│   │   │                                                           ││  │
│   │   │  角色: 文件对象存储                                        ││  │
│   │   └───────────────────────────────────────────────────────────┘│  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.4 物理视图 (Physical View)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    物理视图 - 部署拓扑                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   开发环境 (本地):                                                      │
│   ─────────────────                                                     │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    Developer Laptop                             │  │
│   │                                                                 │  │
│   │   ┌─────────────────────────────────────────────────────────┐  │  │
│   │   │                   Docker Desktop                        │  │  │
│   │   │                                                         │  │  │
│   │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │  │  │
│   │   │  │frontend │ │backend  │ │postgres │ │ minio   │       │  │  │
│   │   │  │  :80    │ │  :8000  │ │  :5432  │ │:9000/01 │       │  │  │
│   │   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │  │  │
│   │   │                                                         │  │  │
│   │   └─────────────────────────────────────────────────────────┘  │  │
│   │                                                                 │  │
│   │   访问: http://localhost:80                                     │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   生产环境 (推荐):                                                      │
│   ─────────────────                                                     │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                        Cloud Provider                           │  │
│   │                                                                 │  │
│   │   ┌───────────────┐      ┌───────────────────────────────────┐ │  │
│   │   │    CDN        │      │       Kubernetes Cluster          │ │  │
│   │   │  (静态资源)   │      │                                   │ │  │
│   │   └───────────────┘      │  ┌─────────┐    ┌─────────┐      │ │  │
│   │          │               │  │ Pod:    │    │ Pod:    │      │ │  │
│   │          │               │  │ backend │    │ backend │      │ │  │
│   │          ▼               │  │ replica1│    │ replica2│      │ │  │
│   │   ┌───────────────┐      │  └─────────┘    └─────────┘      │ │  │
│   │   │ Load Balancer │      │         │              │          │ │  │
│   │   │  (Nginx/ALB)  │──────│─────────┴──────────────┘          │ │  │
│   │   └───────────────┘      │                                   │ │  │
│   │                          └───────────────────────────────────┘ │  │
│   │                                       │                         │  │
│   │                          ┌────────────┴────────────┐           │  │
│   │                          ▼                         ▼           │  │
│   │                   ┌─────────────┐          ┌─────────────┐     │  │
│   │                   │ RDS         │          │ S3 / OSS    │     │  │
│   │                   │ PostgreSQL  │          │ (替代MinIO) │     │  │
│   │                   │ (托管)      │          │             │     │  │
│   │                   └─────────────┘          └─────────────┘     │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.5 场景视图 (Scenarios)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    场景视图 - 用例驱动                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   用例 1: 用户登录                                                      │
│   ──────────────────                                                    │
│                                                                         │
│   Actor: 用户                                                           │
│   前置条件: 用户已注册                                                  │
│                                                                         │
│   ┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐             │
│   │  用户  │     │ 前端   │     │ 后端   │     │ 数据库 │             │
│   └────┬───┘     └────┬───┘     └────┬───┘     └────┬───┘             │
│        │              │              │              │                  │
│        │ 1.输入账密   │              │              │                  │
│        │─────────────▶│              │              │                  │
│        │              │              │              │                  │
│        │              │ 2.POST /auth │              │                  │
│        │              │─────────────▶│              │                  │
│        │              │              │              │                  │
│        │              │              │ 3.查询用户   │                  │
│        │              │              │─────────────▶│                  │
│        │              │              │              │                  │
│        │              │              │ 4.返回用户   │                  │
│        │              │              │◀─────────────│                  │
│        │              │              │              │                  │
│        │              │              │ 5.验证密码   │                  │
│        │              │              │──┐           │                  │
│        │              │              │  │ bcrypt    │                  │
│        │              │              │◀─┘           │                  │
│        │              │              │              │                  │
│        │              │ 6.JWT Token  │              │                  │
│        │              │◀─────────────│              │                  │
│        │              │              │              │                  │
│        │              │ 7.存储Token  │              │                  │
│        │              │──┐           │              │                  │
│        │              │  │localStorage              │                  │
│        │              │◀─┘           │              │                  │
│        │              │              │              │                  │
│        │ 8.跳转首页   │              │              │                  │
│        │◀─────────────│              │              │                  │
│        │              │              │              │                  │
│                                                                         │
│   ─────────────────────────────────────────────────────────────────────│
│                                                                         │
│   用例 2: 创建课题                                                      │
│   ──────────────────                                                    │
│                                                                         │
│   Actor: 成员 (MEMBER)                                                  │
│   前置条件: 用户已登录                                                  │
│                                                                         │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│   │  用户  │ │  组件  │ │ Store  │ │  API   │ │ 后端   │ │ 数据库 │   │
│   └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘   │
│       │          │          │          │          │          │         │
│       │ 1.点击创建│          │          │          │          │         │
│       │─────────▶│          │          │          │          │         │
│       │          │          │          │          │          │         │
│       │          │ 2.显示表单│          │          │          │         │
│       │◀─────────│          │          │          │          │         │
│       │          │          │          │          │          │         │
│       │ 3.填写提交│          │          │          │          │         │
│       │─────────▶│          │          │          │          │         │
│       │          │          │          │          │          │         │
│       │          │4.createTopic()      │          │          │         │
│       │          │─────────▶│          │          │          │         │
│       │          │          │          │          │          │         │
│       │          │          │5.POST    │          │          │         │
│       │          │          │─────────▶│          │          │         │
│       │          │          │          │          │          │         │
│       │          │          │          │6.验证JWT │          │         │
│       │          │          │          │─────────▶│          │         │
│       │          │          │          │          │          │         │
│       │          │          │          │          │7.INSERT  │         │
│       │          │          │          │          │─────────▶│         │
│       │          │          │          │          │          │         │
│       │          │          │          │          │8.新记录  │         │
│       │          │          │          │          │◀─────────│         │
│       │          │          │          │          │          │         │
│       │          │          │          │9.课题数据│          │         │
│       │          │          │◀─────────│          │          │         │
│       │          │          │          │          │          │         │
│       │          │10.更新状态          │          │          │         │
│       │          │◀─────────│          │          │          │         │
│       │          │          │          │          │          │         │
│       │          │11.响应式更新 DOM    │          │          │         │
│       │◀─────────│          │          │          │          │         │
│       │          │          │          │          │          │         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 附录: 常用命令速查

```bash
# ─────────────────────────────────────────────────────────
# Docker 操作
# ─────────────────────────────────────────────────────────
docker compose up -d --build    # 构建并启动所有服务
docker compose down             # 停止所有服务
docker compose down -v          # 停止并删除数据卷 (⚠️ 数据丢失)
docker compose logs -f backend  # 查看后端日志
docker compose ps               # 查看服务状态
docker exec -it tcgs-backend sh # 进入后端容器

# ─────────────────────────────────────────────────────────
# 数据库操作
# ─────────────────────────────────────────────────────────
docker exec -it tcgs-postgres psql -U postgres -d tcgs
# 在 psql 中:
\dt                             # 列出所有表
\d topics                       # 查看表结构
SELECT * FROM users;            # 查询数据

# ─────────────────────────────────────────────────────────
# Alembic 迁移
# ─────────────────────────────────────────────────────────
alembic revision --autogenerate -m "add new column"  # 生成迁移
alembic upgrade head            # 应用所有迁移
alembic downgrade -1            # 回滚一个版本
alembic history                 # 查看迁移历史

# ─────────────────────────────────────────────────────────
# 前端开发
# ─────────────────────────────────────────────────────────
npm run dev                     # 启动开发服务器
npm run build                   # 生产构建
npm run lint                    # 代码检查
```

---

**报告完成于**: 2026-04-02

**作者**: Claude Code

**版本**: 1.0
