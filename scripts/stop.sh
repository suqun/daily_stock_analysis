#!/bin/bash
# ===================================
# 停止服务脚本
# ===================================

echo "正在停止服务..."

# 精准匹配杀死进程
pkill -f "python3 main.py"

# 等待1秒确保进程退出
sleep 1

# 检查是否还有残留进程
REMAINING=$(ps aux | grep "python3 main.py" | grep -v grep | wc -l)
if [ "$REMAINING" -eq 0 ]; then
    echo "✅ 服务已停止"
else
    echo "⚠️ 仍有 $REMAINING 个进程在运行"
    ps aux | grep "python3 main.py" | grep -v grep
fi
