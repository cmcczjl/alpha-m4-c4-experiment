#!/usr/bin/env python3
"""
A lightweight local RAG (Retrieval‑Augmented Generation) demo.

It loads a few hard‑coded documents, performs a simple keyword‑based
retrieval for the user query, and then synthesises an answer by
concatenating the retrieved snippet with a static template.

The script is deliberately self‑contained and uses only the Python
standard library so it can run in the sandbox without additional
installations.
"""

import sys
import re
from textwrap import dedent

# ----------------------------------------------------------------------
# Sample knowledge base – in a real RAG system this would be replaced by
# vector store / Elasticsearch / etc.
# ----------------------------------------------------------------------
DOCUMENTS = [
    {
        "id": "doc1",
        "title": "Introduction to RAG",
        "content": dedent(
            """
            Retrieval‑Augmented Generation (RAG) combines a large language
            model with an external knowledge source. The retriever fetches
            relevant documents, and the generator produces a response
            conditioned on both the query and the retrieved texts.
            """
        ).strip(),
    },
    {
        "id": "doc2",
        "title": "Python subprocess module",
        "content": dedent(
            """
            The subprocess module allows you to spawn new processes, connect
            to their input/output/error pipes, and obtain their return codes.
            Common functions are subprocess.run, subprocess.Popen, and
            subprocess.check_output.
            """
        ).strip(),
    },
    {
        "id": "doc3",
        "title": "FastAPI quick start",
        "content": dedent(
            """
            FastAPI is a modern, fast (high‑performance) web framework for
            building APIs with Python 3.7+ based on standard Python type hints.
            It uses Pydantic for data validation and Starlette for the ASGI
            toolkit.
            """
        ).strip(),
    },
]

# ----------------------------------------------------------------------
# Simple keyword retriever
# ----------------------------------------------------------------------
def retrieve(query: str, top_k: int = 2):
    """Return up to `top_k` documents whose content contains any query word."""
    query_terms = set(re.findall(r"\w+", query.lower()))
    scores = []
    for doc in DOCUMENTS:
        doc_terms = set(re.findall(r"\w+", doc["content"].lower()))
        common = query_terms & doc_terms
        if common:
            scores.append((len(common), doc))
    # Sort by number of matching terms (descending) and keep top_k
    scores.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scores[:top_k]]

# ----------------------------------------------------------------------
# Very naive "generator" – just formats the retrieved snippets.
# ----------------------------------------------------------------------
def generate_answer(query: str, retrieved_docs):
    if not retrieved_docs:
        return "I couldn't find any relevant information."
    snippets = "\n---\n".join(f"[{doc['title']}]\n{doc['content']}" for doc in retrieved_docs)
    answer = (
        f"**Question:** {query}\n\n"
        f"**Relevant documents:**\n{snippets}\n\n"
        "**Answer:** Based on the above excerpts, the answer to your query is ..."
    )
    return answer

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        # Default demo query when no arguments are supplied
        query = "What is Retrieval‑Augmented Generation?"
    print(f"🔎 Query: {query}\n")
    retrieved = retrieve(query)
    print("📄 Retrieved document snippets:")
    for doc in retrieved:
        print(f"- {doc['title']} (id: {doc['id']})")
    print("\n📝 Generated answer:\n")
    print(generate_answer(query, retrieved))

if __name__ == "__main__":
    main()