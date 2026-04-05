#!/bin/bash
# 激活虚拟环境并安装依赖

echo "📦 创建 Python 虚拟环境..."
python3 -m venv .venv

echo "🔧 激活虚拟环境..."
source .venv/bin/activate

echo "📥 安装依赖包..."
pip install -r requirements.txt

echo ""
echo "✅ 虚拟环境配置完成！"
echo ""
echo "使用方法："
echo "  source .venv/bin/activate"
echo "  python3 generate_song.py \"鬼灭之刃 OP\""
echo ""
