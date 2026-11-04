#!/bin/bash
# AGI 智能体部署脚本
set -e

echo "================================================"
echo "AGI 智能体部署助手"
echo "================================================"

cd "$(dirname "$0")"

# 创建必要目录
echo "📁 创建目录结构..."
mkdir -p data/journal data/knowledge data/archive logs

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
pip3 install -r requirements.txt -q

# 检查配置
if [ ! -f "config.yaml" ]; then
    echo "❌ 配置文件 config.yaml 不存在"
    echo "请创建 config.yaml 并填写 API 密钥"
    exit 1
fi

echo ""
echo "✅ 部署完成！"
echo ""
echo "启动方式："
echo "  1. 测试模式（Mock LLM）: python3 test_agent.py"
echo "  2. 生产模式:            python3 run.py --mode agent"
echo "  3. 飞书 Bot:             python3 run.py --mode feishu"
echo "  4. 全部运行:             python3 run.py --mode both"
echo ""
echo "日志位置: data/ 和 logs/"
echo "================================================"
