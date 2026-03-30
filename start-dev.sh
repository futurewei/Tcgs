#!/bin/bash

# AlgoHub 本地开发启动脚本
# 用于同时启动前端和后端服务

export PATH="/opt/homebrew/opt/node@20/bin:/opt/homebrew/opt/python@3.11/bin:/opt/homebrew/opt/postgresql@15/bin:$PATH"

PROJECT_DIR="/Users/laiwei/Desktop/algo_gov/tcgs_prod_v2/Tcgs"

echo "=========================================="
echo "  AlgoHub 本地开发环境启动"
echo "=========================================="

# 检查 PostgreSQL 是否运行
if ! pg_isready -q; then
    echo "⚠️  PostgreSQL 未运行，正在启动..."
    brew services start postgresql@15
    sleep 2
fi
echo "✅ PostgreSQL 运行中"

# 启动后端
echo ""
echo "🚀 启动后端服务 (端口 8000)..."
cd "$PROJECT_DIR/backend"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 启动前端
echo ""
echo "🚀 启动前端服务 (端口 5173)..."
cd "$PROJECT_DIR"
npm run dev &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"

echo ""
echo "=========================================="
echo "  服务启动完成！"
echo "=========================================="
echo ""
echo "📍 访问地址："
echo "   前端: http://localhost:5173"
echo "   后端 API: http://localhost:8000"
echo "   API 文档: http://localhost:8000/docs"
echo ""
echo "👤 测试账号："
echo "   Admin:              admin@algohub.com / admin123"
echo "   Member:             member@algohub.com / member123"
echo "   Reviewer:           reviewer@algohub.com / reviewer123"
echo "   Customer (PDU内):   pdt@algohub.com / pdt123"
echo "   Customer (PDU外):   partner@algohub.com / partner123"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 捕获 Ctrl+C 并清理进程
trap "echo ''; echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# 等待子进程
wait
