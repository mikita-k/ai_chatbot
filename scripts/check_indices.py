from src.stage1.rag_chatbot import DocumentStore
store = DocumentStore.from_file('data/static_docs.txt')
for i, doc in enumerate(store.docs):
    print(f'{i}: {doc[:50]}...')

