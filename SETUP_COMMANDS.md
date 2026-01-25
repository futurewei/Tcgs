# TCGS 项目本地部署命令记录

## 环境要求
- macOS (Apple Silicon)
- Homebrew 已安装

---

## 1. 安装系统依赖

```bash
# 安装 Python 3.11、Node.js 20、PostgreSQL 15
brew install python@3.11 node@20 postgresql@15
```

---

## 2. 配置环境变量（临时）

```bash
export PATH="/opt/homebrew/opt/python@3.11/bin:/opt/homebrew/opt/node@20/bin:/opt/homebrew/opt/postgresql@15/bin:$PATH"
```

---

## 3. 启动并配置 PostgreSQL

```bash
# 启动 PostgreSQL 服务
brew services start postgresql@15

# 创建用户和数据库
createuser -s postgres
psql postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';"
createdb -U postgres tcgs
```

---

## 4. 后端环境配置

```bash
# 进入后端目录
cd /Users/laiwei/Desktop/algo_gov/tcgs_prod_v2/Tcgs/backend

# 创建 Python 虚拟环境
/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip 并安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. 创建后端环境配置文件

```bash
# 创建 .env 文件
cat > /Users/laiwei/Desktop/algo_gov/tcgs_prod_v2/Tcgs/backend/.env << 'EOF'
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tcgs
SECRET_KEY=tcgs-dev-secret-key-2026
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=tcgs-attachments
MINIO_SECURE=false
DEBUG=true
EOF
```

---

## 6. 初始化数据库（运行 seed 脚本）

```bash
cd /Users/laiwei/Desktop/algo_gov/tcgs_prod_v2/Tcgs/backend
source venv/bin/activate
python seed.py
```

---

## 7. 安装前端依赖

```bash
export PATH="/opt/homebrew/opt/node@20/bin:$PATH"
cd /Users/laiwei/Desktop/algo_gov/tcgs_prod_v2/Tcgs
npm install --legacy-peer-deps
```

---

## 8. 修改 vite.config.ts（添加 API 代理）

将 `vite.config.ts` 修改为：

```typescript
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

---

## 9. 启动服务

### 方式一：使用 Docker Compose（推荐）

```bash
cd /Users/laiwei/Desktop/algo_gov/tcgs_prod_v2/Tcgs
docker compose up -d --build
```

### 方式二：本地直接运行

**终端 1 - 启动后端：**
```bash
cd /Users/laiwei/Desktop/algo_gov/tcgs_prod_v2/Tcgs/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**终端 2 - 启动前端：**
```bash
export PATH="/opt/homebrew/opt/node@20/bin:$PATH"
cd /Users/laiwei/Desktop/algo_gov/tcgs_prod_v2/Tcgs
npm run dev
```

### 方式三：使用启动脚本

```bash
cd /Users/laiwei/Desktop/algo_gov/tcgs_prod_v2/Tcgs
./start-dev.sh
```

---

## 访问地址

| 服务 | Docker 方式 | 本地方式 |
|------|-------------|----------|
| 前端 | http://localhost:80 | http://localhost:5173 |
| 后端 API | http://localhost:8000 | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs | http://localhost:8000/docs |
| MinIO 控制台 | http://localhost:9001 | 需单独启动 |

---

## 测试账号

| 角色 | 邮箱 | 密码 |
|------|------|------|
| Admin | admin@tcgs.com | admin123 |
| Member | member@tcgs.com | member123 |
| Reviewer | reviewer@tcgs.com | reviewer123 |
| External | external@tcgs.com | external123 |
| Customer | pdt@tcgs.com | pdt123 |

---

## 常用 Docker 命令

```bash
# 查看容器状态
docker ps

# 查看后端日志
docker logs tcgs-backend

# 查看前端日志
docker logs tcgs-frontend

# 停止所有服务
docker compose down

# 重新构建并启动
docker compose up -d --build

# 清理所有数据（包括数据库）
docker compose down -v
```
