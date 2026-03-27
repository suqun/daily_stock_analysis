#!/bin/bash
# ===================================
# 重启服务脚本
# ===================================

# 如果没有传入参数，使用默认
MODE="${1:---serve-only}"

echo "========================"
echo "重启服务: python3 main.py $MODE"
echo "========================"

# 1. 停止旧服务
echo "正在停止旧服务..."
pkill -f "python3 main.py"
sleep 1

# 2. 启动新服务
echo "正在启动新服务..."
nohup python3 main.py $MODE > app.log 2>&1 &

# 等待2秒确保服务启动
sleep 2

echo "✅ 重启完成！"
echo "📄 日志: tail -f app.log"
echo "🔍 进程: ps aux | grep main.py"
