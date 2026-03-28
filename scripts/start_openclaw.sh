#!/bin/bash
# ===================================
# 启动 OpenClaw 脚本
# ===================================

# 端口（默认 18789）
PORT="${1:-18789}"

echo "========================"
echo "启动 OpenClaw 端口: $PORT"
echo "========================"

# 杀掉旧进程
echo "正在停止旧进程..."
pkill -f "openclaw"
sleep 1

# 后台启动
nohup openclaw --port $PORT > openclaw.log 2>&1 &

echo "✅ OpenClaw 启动完成！"
echo "📄 日志: tail -f openclaw.log"
echo "🔍 进程: ps aux | grep openclaw"
echo "🔗 健康检查: curl http://127.0.0.1:$PORT/health"
