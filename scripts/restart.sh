#!/bin/bash
# ===================================
# 重启服务脚本
# ===================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
cd "$SCRIPT_DIR" || exit 1

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
source venv/bin/activate
nohup python3 main.py $MODE > app.log 2>&1 &

# 等待3秒确保服务启动
sleep 3

echo "✅ 重启完成！"
echo "📄 日志: tail -f app.log"
echo "🔍 进程: ps aux | grep main.py"
echo "🌐 访问: https://stock.diplo.top"
