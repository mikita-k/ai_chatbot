from src.stage1.rag_chatbot import DocumentStore

store = DocumentStore.from_file('data/static_docs.txt')
query = "how much should I pay for 2 hours?"
hits = store.retrieve(query, k=5)

print("Query:", query)
print("\nFound documents:")
for idx, score in hits:
    print(f"\nDocument {idx} (score={score:.4f}):")
    print(store.docs[idx][:200])
