#!/bin/bash
# 创建 RAG 语料库目录结构
mkdir -p work/scripts/rag_corpus
# 初始化 README 文件
cat <<EOF > work/scripts/rag_corpus/README.md
# RAG Corpus
此目录用于存放 M2 里程碑要求的真实文档集。

## 目录结构
- \`upwork_projects/\`: 存放从 Upwork 采集的项目描述。
- \`faq/\`: 存放技术文档及常见问题集。

## 采集目标
1. Upwork 实时项目需求文本。
2. 开发者技能匹配相关的 FAQ。
EOF
echo "SUCCESS: scripts/rag_corpus directory and README.md initialized."