#!/usr/bin/env python3
import os

def main():
    # 输出目录：scripts/rag_corpus/
    out_dir = os.path.join(os.path.dirname(__file__), "rag_corpus")
    os.makedirs(out_dir, exist_ok=True)

    # 创建 3 份示例文档
    docs = {
        "doc1.txt": "This is the content of document one. It contains sample text for testing.",
        "doc2.txt": "Document two includes different information. It serves as another example.",
        "doc3.txt": "The third document provides additional data for the RAG corpus."
    }

    for name, content in docs.items():
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"Collected {len(docs)} documents saved to {out_dir}/")

if __name__ == "__main__":
    main()