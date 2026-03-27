#!/bin/bash
# ===================================
# 启动服务脚本
# ===================================

# 默认参数
MODE="${1:---serve-only}"

echo "========================"
echo "启动服务: python3 main.py $MODE"
echo "========================"

# 后台启动
nohup python3 main.py $MODE > app.log 2>&1 &

echo "✅ 启动完成！"
echo "📄 日志: tail -f app.log"
echo "🔍 进程: ps aux | grep main.py"
