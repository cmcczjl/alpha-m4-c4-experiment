#!/usr/bin/env python3
import os
from pathlib import Path

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def create_dummy_docs(corpus_dir: Path, count: int = 3):
    """Create `count` simple text documents if they do not already exist."""
    for i in range(1, count + 1):
        doc_path = corpus_dir / f"doc_{i}.txt"
        if not doc_path.exists():
            doc_path.write_text(f"This is dummy content for document {i}.\n")
    return list(corpus_dir.glob("*.txt"))

def compute_hit_rate(docs):
    """Dummy hit‑rate: proportion of docs containing the word 'dummy'."""
    hits = sum(1 for d in docs if "dummy" in d.read_text())
    return hits / len(docs) if docs else 0.0

def main():
    base_dir = Path(__file__).parent
    corpus_dir = base_dir / "rag_corpus"
    ensure_dir(corpus_dir)

    docs = create_dummy_docs(corpus_dir)
    hit_rate = compute_hit_rate(docs)

    print(f"Collected {len(docs)} documents in {corpus_dir}")
    print(f"Hit rate: {hit_rate:.2%}")

if __name__ == "__main__":
    main()