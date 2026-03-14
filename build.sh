#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Build the RAG index from data/ files at deploy time
python -c "from rag.dataprep import build_index; count = build_index(); print(f'[Build] RAG index ready — {count} chunks')"
