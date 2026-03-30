# AlgoHub - 算法能力中台

AlgoHub 是一个面向算法团队的课题治理与能力管理系统，将"课题/项目"与"人、阶段、产出、容量"统一管理，让技术工作从「隐性经验」变成「可管理结构」。

## 技术栈

**前端**
- Vue 3 + TypeScript
- Element Plus
- Pinia (状态管理)
- Vite
- TailwindCSS

**后端**
- Python + FastAPI
- SQLAlchemy ORM
- PostgreSQL
- Alembic (数据库迁移)
- JWT 鉴权
- MinIO (文件存储)

**部署**
- Docker + Docker Compose
- Nginx (前端反向代理)

---

## 核心功能

### 1. 课题 (Topic) 管理
- 课题类型：Uncertainty（探索型）/ Evolution（演进型）
- 紧急程度：P0 / P1 / P2
- DRI (直接责任人) 机制
- 委托人/来源人管理

### 2. 阶段化流程 (Stage Workflow)
- 可自定义阶段模板
- 阶段状态可视化 (pending / active / done)
- 阶段推进/回退
- 阶段交付物要求
- 阶段评审意见

### 3. 产出与评审 (Artifact & Review)
- 每阶段可上传交付物
- 支持多种交付物类型 (文档/链接/文件)
- 评审意见记录

### 4. 能力槽位 (Capacity Slot)
- Algo / External 不同类型槽位
- 课题绑定容量占比
- 负载可视化

### 5. 数据洞察 (Insights)
- KPI 统计
- 人员负载分析
- 课题吞吐量

### 6. 用户角色
| 角色 | 说明 |
|------|------|
| Admin | 系统管理员，全权限 |
| Member | 技术成员，可创建和推进课题 |
| Reviewer | 评审角色 |
| External | 外部协作者 |
| Customer | 委托人/需求方，只读 |

---

## 快速启动

### Docker 模式（推荐）

```bash
# 首次启动（构建镜像）
docker-compose up -d --build

# 重新构建（无缓存）
docker-compose build --no-cache
docker-compose up -d

# 仅重建前端（无缓存）
docker-compose build --no-cache frontend
docker-compose up -d frontend

# 仅重建后端（无缓存）
docker-compose build --no-cache backend
docker-compose up -d backend

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f           # 所有服务
docker-compose logs -f backend   # 仅后端
docker-compose logs -f frontend  # 仅前端

# 停止所有服务
docker-compose down

# 停止并删除数据卷（慎用，会删除数据库数据）
docker-compose down -v
```

**服务端口**
- 前端: http://localhost:80
- 后端 API: http://localhost:8001
- MinIO Console: http://localhost:9001
- PostgreSQL: localhost:5432

### 非 Docker 模式（开发环境）

**1. 启动 PostgreSQL**
```bash
# macOS (Homebrew)
brew services start postgresql@15

# 或使用 Docker 单独运行 PostgreSQL
docker run -d --name tcgs-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=tcgs \
  -p 5432:5432 \
  postgres:15-alpine
```

**2. 启动后端**
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tcgs
export SECRET_KEY=dev-secret-key

# 运行数据库迁移
alembic upgrade head

# 初始化种子数据
python seed.py

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**3. 启动前端**
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

**4. 停止服务**
```bash
# 停止前端: Ctrl+C

# 停止后端: Ctrl+C

# 停止 PostgreSQL
brew services stop postgresql@15
# 或
docker stop tcgs-postgres
```

---

## 数据库管理

### Alembic 迁移命令

```bash
cd backend

# 查看当前迁移版本
alembic current

# 查看迁移历史
alembic history

# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade <revision_id>

# 回退一个版本
alembic downgrade -1

# 回退到指定版本
alembic downgrade <revision_id>

# 回退到初始状态
alembic downgrade base

# 生成新的迁移文件（自动检测模型变化）
alembic revision --autogenerate -m "描述信息"

# 生成空的迁移文件（手动编写）
alembic revision -m "描述信息"
```

### 手动数据库操作

```bash
# 进入 Docker PostgreSQL
docker exec -it tcgs-postgres psql -U postgres -d tcgs

# 或本地 PostgreSQL
psql -U postgres -d tcgs
```

**常用 SQL 命令**
```sql
-- 查看所有表
\dt

-- 查看表结构
\d table_name

-- 查看表数据
SELECT * FROM users LIMIT 10;

-- 添加字段（当 Alembic 不可用时）
ALTER TABLE stage_template_stages ADD COLUMN require_review BOOLEAN DEFAULT FALSE;
ALTER TABLE topic_stage_instances ADD COLUMN require_review BOOLEAN DEFAULT FALSE;

-- 修改字段类型
ALTER TABLE table_name ALTER COLUMN column_name TYPE new_type;

-- 删除字段
ALTER TABLE table_name DROP COLUMN column_name;

-- 查看枚举类型
SELECT enum_range(NULL::topic_type);
SELECT enum_range(NULL::user_role);

-- 退出
\q
```

### 数据库备份与恢复

```bash
# 备份（Docker 环境）
docker exec tcgs-postgres pg_dump -U postgres tcgs > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份（本地环境）
pg_dump -U postgres tcgs > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复（Docker 环境）
cat backup.sql | docker exec -i tcgs-postgres psql -U postgres -d tcgs

# 恢复（本地环境）
psql -U postgres -d tcgs < backup.sql

# 创建数据库
docker exec tcgs-postgres createdb -U postgres tcgs

# 删除数据库（慎用）
docker exec tcgs-postgres dropdb -U postgres tcgs
```

---

## 目录结构

```
tcgs/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic 模式
│   │   ├── services/       # 业务逻辑
│   │   └── main.py         # 应用入口
│   ├── alembic/            # 数据库迁移
│   │   └── versions/       # 迁移版本文件
│   ├── requirements.txt    # Python 依赖
│   └── seed.py             # 种子数据
├── src/                    # 前端代码
│   ├── api/                # API 调用
│   ├── components/         # 组件
│   ├── stores/             # Pinia 状态
│   ├── views/              # 页面视图
│   └── types/              # TypeScript 类型
├── docker-compose.yml      # Docker 编排
├── nginx.conf              # Nginx 配置
└── package.json            # 前端依赖
```

---

## 常见问题

### 端口被占用
```bash
# 查看端口占用
lsof -i :8000
lsof -i :80

# 杀死占用进程
kill -9 <PID>
```

### 数据库连接失败
```bash
# 检查 PostgreSQL 是否运行
docker-compose ps
# 或
pg_isready -h localhost -p 5432
```

### 前端页面空白
```bash
# 检查 nginx 配置
docker exec tcgs-frontend cat /etc/nginx/conf.d/default.conf

# 检查前端构建
docker-compose logs frontend
```

### 清理 Docker 缓存
```bash
# 清理未使用的镜像
docker image prune

# 清理所有未使用资源
docker system prune -a
```

---

## License

MIT License
