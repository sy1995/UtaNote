#!/bin/bash
# 快速运行脚本 - 自动激活虚拟环境

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "⚠️  虚拟环境不存在，正在创建..."
    bash setup.sh
fi

# 激活虚拟环境
source .venv/bin/activate

# 运行脚本
python3 generate_song.py "$@"
