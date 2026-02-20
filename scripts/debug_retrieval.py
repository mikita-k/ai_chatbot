import sys
import os

# Add parent directory to path so we can import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.stage1.rag_chatbot import DocumentStore

store = DocumentStore.from_file('data/static_docs.txt')
query = "how much should I pay for 2 hours?"
hits = store.retrieve(query, k=5)

print("Query:", query)
print("\nFound documents:")
for idx, similarity in hits:
    print(f"\nDocument {idx} (similarity={similarity:.4f}):")
    print(store.docs[idx][:200])
