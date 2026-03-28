#!/bin/sh
# ===================================
# 重启服务脚本
# ===================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && cd .. && pwd)"
cd "$SCRIPT_DIR" || exit 1

MODE="--serve-only"
PORT="8080"

while [ $# -gt 0 ]; do
    case "$1" in
        --port)
            PORT="$2"
            shift 2
            ;;
        --serve-only|--webui)
            MODE="$1"
            shift
            ;;
        *)
            MODE="$1"
            shift
            ;;
    esac
done

echo "========================"
echo "重启服务: python3 main.py $MODE --port $PORT"
echo "========================"

# 1. 停止旧服务
echo "正在停止旧服务..."
pkill -f "python3 main.py"
sleep 1

# 2. 启动新服务
echo "正在启动新服务..."
. venv/bin/activate
nohup python3 main.py $MODE --port $PORT > app.log 2>&1 &

# 等待5秒确保服务启动
sleep 5

# 检查服务是否启动成功
if curl -s --connect-timeout 3 http://localhost:$PORT/ > /dev/null 2>&1; then
    echo "✅ 服务启动成功！端口: $PORT"
else
    echo "⚠️ 服务可能未启动，请检查日志: tail -f app.log"
    echo "尝试访问: curl http://localhost:$PORT/"
fi

echo "📄 日志: tail -f app.log"
echo "🔍 进程: ps aux | grep main.py"
echo "🌐 访问: https://stock.diplo.top"
