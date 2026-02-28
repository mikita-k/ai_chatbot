#!/usr/bin/env python
"""
Stage 1: Clean FAISS Database

Use this script when static_docs.txt has changed and you want to rebuild the FAISS index.

Usage:
    python scripts/stage1/clean_faiss_db.py

This will:
1. Remove faiss_db/index.faiss
2. Remove faiss_db/docs.pkl
3. Next run of any chatbot will rebuild them automatically
"""

import os
import shutil
from pathlib import Path

def main():
    print("🧹 Cleaning FAISS Database...")

    faiss_db_path = Path(__file__).parent.parent.parent / "faiss_db"

    if not faiss_db_path.exists():
        print(f"ℹ️  FAISS DB directory does not exist: {faiss_db_path}")
        return

    files_to_remove = [
        faiss_db_path / "index.faiss",
        faiss_db_path / "docs.pkl"
    ]

    for file_path in files_to_remove:
        if file_path.exists():
            file_path.unlink()
            print(f"✅ Removed: {file_path.name}")
        else:
            print(f"ℹ️  File not found: {file_path.name}")

    print("\n✅ FAISS DB cleaned!")
    print("📝 Next run of chatbot will rebuild the index from static_docs.txt")

if __name__ == "__main__":
    main()

