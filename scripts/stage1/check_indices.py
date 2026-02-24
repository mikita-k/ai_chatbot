import sys
import os

# Add parent directory to path so we can import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.stage1.rag_chatbot import DocumentStore
store = DocumentStore.from_file('data/static_docs.txt')
for i, doc in enumerate(store.docs):
    print(f'{i}: {doc[:50]}...')

