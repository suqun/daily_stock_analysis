#!/bin/bash
# ===================================
# 启动 OpenClaw 脚本
# ===================================

echo "========================"
echo "启动 OpenClaw"
echo "========================"

# 杀掉旧进程
echo "正在停止旧进程..."
pkill -f "openclaw-gateway" || true
sleep 2

# 后台启动
nohup openclaw > openclaw.log 2>&1 &

echo "等待服务启动..."
sleep 5

if curl -s http://127.0.0.1:18789/health > /dev/null 2>&1; then
    echo "✅ OpenClaw 启动成功！"
else
    echo "❌ OpenClaw 启动失败，请检查日志: tail -f openclaw.log"
fi
echo "📄 日志: tail -f openclaw.log"
echo "🔍 进程: ps aux | grep openclaw"
echo "🔗 健康检查: curl http://127.0.0.1:18789/health"
