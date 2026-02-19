import re
import time
import os
import pickle
from typing import List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    print("dotenv not found, skipping .env loading. Make sure environment variables are set.")
    # dotenv is optional; if not installed, environment variables must be set externally
    pass


class DocumentStore:
    """Vector database store using FAISS with sentence-transformers embeddings."""

    def __init__(self, docs: List[str], db_path: str = "./faiss_db"):
        self.docs = docs
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)

        # Initialize embedding model
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        # Check if index already exists
        index_path = os.path.join(db_path, "index.faiss")
        docs_path = os.path.join(db_path, "docs.pkl")

        if os.path.exists(index_path) and os.path.exists(docs_path):
            # Load existing index and docs
            self.index = faiss.read_index(index_path)
            with open(docs_path, "rb") as f:
                self.docs = pickle.load(f)
        else:
            # Create new index
            self._index_documents()

    def _index_documents(self):
        """Embed and index documents in FAISS."""
        embeddings = self.model.encode(self.docs, convert_to_numpy=True)
        embeddings = embeddings.astype(np.float32)

        # Create FAISS index (flat L2 index for exact search)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        # Save index and docs
        os.makedirs(self.db_path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(self.db_path, "index.faiss"))
        with open(os.path.join(self.db_path, "docs.pkl"), "wb") as f:
            pickle.dump(self.docs, f)

    @classmethod
    def from_file(cls, path: str, db_path: str = "./faiss_db"):
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        # split by blank line into documents
        parts = [p.strip() for p in raw.split("\n\n") if p.strip()]
        return cls(parts, db_path=db_path)

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[int, float]]:
        """Retrieve top-k most similar documents using vector similarity."""
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True).astype(np.float32)

        # Search in FAISS (returns distances)
        distances, indices = self.index.search(query_embedding, k)

        # Convert L2 distances to similarity scores (0-1 range)
        # Lower L2 distance = higher similarity
        # Use exponential decay to get scores in [0, 1]
        scores = [np.exp(-d) for d in distances[0]]

        return list(zip(indices[0].tolist(), scores))


def guard_rails(text: str) -> str:
    # redact emails
    text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", text)
    # redact long digit sequences (simulate sensitive numbers)
    text = re.sub(r"\b\d{6,}\b", "[REDACTED_NUMBER]", text)
    return text


class SimpleRAGChatbot:
    def __init__(self, store: DocumentStore, use_llm: bool = False, model: str | None = None, include_dynamic: bool = True):
        self.store = store
        self.use_llm = use_llm
        self.include_dynamic = include_dynamic
        # allow override via parameter or env var
        self.model = model or os.getenv("OPENAI_MODEL")

    def _get_dynamic_context(self) -> str:
        """Get dynamic context from parking availability database."""
        try:
            from data.dynamic import (
                get_availability_summary,
                get_current_pricing,
                get_opening_hours,
            )
        except ImportError:
            return ""

        try:
            availability = get_availability_summary()
            pricing = get_current_pricing()
            hours = get_opening_hours()

            return f"""
=== REAL-TIME PARKING INFORMATION ===
{availability}

Current Pricing:
- Hourly rate: ${pricing.get('hourly_rate', 2.0)}
- Daily maximum: ${pricing.get('daily_max', 20.0)}

Today's Hours:
- Opening: {hours.get('opening', '07:00')}
- Closing: {hours.get('closing', '22:00')}
"""
        except Exception as e:
            return f"(Dynamic data unavailable: {e})"

    def _call_openai(self, query: str, contexts: List[str]) -> str:
        # lazy import to avoid hard dependency during tests
        try:
            import openai
        except Exception as e:
            raise RuntimeError("openai package is not installed. Install it or disable use_llm.") from e

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")

        # Prefer new OpenAI client interface (openai>=1.0.0)
        try:
            # New client: openai.OpenAI
            if hasattr(openai, "OpenAI"):
                client = openai.OpenAI(api_key=api_key)
                ctx_text = "\n\n".join(f"== Document {i} ==\n{c}" for i, c in enumerate(contexts))
                user_msg = f"User question: {query}\n\nDocuments:\n{ctx_text}\n\nProvide a concise answer based on the documents."
                resp = client.chat.completions.create(
                    model=self.model or "gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": (
                            "You are a helpful assistant that answers user queries based solely on provided documents. "
                            "When the answer is not present in the documents, say 'I don't know' and offer to escalate."
                        )},
                        {"role": "user", "content": user_msg}
                    ],
                    max_tokens=300,
                    temperature=0.0,
                )
                # new resp shape: resp.choices[0].message.content
                try:
                    return resp.choices[0].message.content.strip()
                except Exception:
                    # fallback to dict-like access
                    return str(resp)
            else:
                # old interface
                openai.api_key = api_key
                model = self.model or "gpt-3.5-turbo"

                system = (
                    "You are a helpful assistant that answers user queries based solely on provided documents. "
                    "When the answer is not present in the documents, say 'I don't know' and offer to escalate."
                )
                # assemble context
                ctx_text = "\n\n".join(f"== Document {i} ==\n{c}" for i, c in enumerate(contexts))
                user_prompt = f"User question: {query}\n\nDocuments:\n{ctx_text}\n\nProvide a concise answer and cite document indices when relevant."

                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ]

                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    max_tokens=300,
                    temperature=0.0,
                )
                return resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            # bubble up exceptions so caller can fallback
            raise

    def answer(self, query: str, k: int = 3, use_llm: bool | None = None) -> str:
        # allow per-call override; default to bot setting
        if use_llm is None:
            use_llm = self.use_llm

        start = time.time()
        hits = self.store.retrieve(query, k=k)
        elapsed = time.time() - start
        contexts = [self.store.docs[i] for i, _ in hits]

        # Add dynamic context if relevant
        if self.include_dynamic:
            dynamic_context = self._get_dynamic_context()
            if dynamic_context:
                contexts.append(dynamic_context)

        if use_llm:
            try:
                generated = self._call_openai(query, contexts)
                return guard_rails(generated + f"\n\n(Retrieval latency: {elapsed:.3f}s, top={k})")
            except Exception as e:
                # fallback to simple concatenation with a warning
                fallback = "\n---\n".join(c for c in contexts)
                return guard_rails(f"[LLM_ERROR: {e}]\n{fallback}\n\n(Retrieval latency: {elapsed:.3f}s, top={k})")

        pieces = [self.store.docs[i] + f"\n[similarity={score:.3f}]" for i, score in hits]
        # simple "generation": concatenate retrieved passages as the answer base
        answer = "\n---\n".join(pieces)

        # Add dynamic context to the answer
        if self.include_dynamic:
            dynamic_context = self._get_dynamic_context()
            if dynamic_context:
                answer += f"\n---\n{dynamic_context}"

        meta = f"\n\n(Retrieval latency: {elapsed:.3f}s, top={k})"
        return guard_rails(answer + meta)


def collect_reservation_interactive() -> dict:
    print("Please provide reservation details.")
    name = input("Name: ").strip()
    surname = input("Surname: ").strip()
    car_number = input("Car number: ").strip()
    period = input("Reservation period (e.g. 2026-02-20 10:00 - 2026-02-20 12:00): ").strip()
    # apply light validation
    if not name or not surname:
        raise ValueError("Name and surname are required")
    return {
        "name": name,
        "surname": surname,
        "car_number": car_number,
        "period": period,
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="RAG chatbot with FAISS vector DB (Stage 1)")
    parser.add_argument("command", choices=["chat", "qa", "eval"], help="mode")
    parser.add_argument("-q", "--query", help="single query for qa mode")
    parser.add_argument("--use-llm", action="store_true", help="Use OpenAI LLM for answer generation (requires OPENAI_API_KEY)")
    parser.add_argument("--db-path", default="./faiss_db", help="Path to FAISS database (default: ./faiss_db)")
    parser.add_argument("--no-dynamic", action="store_true", help="Disable dynamic data (availability, pricing)")
    args = parser.parse_args()

    # Initialize dynamic database on startup
    try:
        from data.dynamic import init_db
        init_db()
    except Exception as e:
        print(f"Warning: Could not initialize dynamic database: {e}")

    store = DocumentStore.from_file("data/static_docs.txt", db_path=args.db_path)
    bot = SimpleRAGChatbot(store, use_llm=args.use_llm, include_dynamic=not args.no_dynamic)

    # show LLM/key status for clarity (do not print the key value)
    if args.use_llm:
        if os.getenv("OPENAI_API_KEY"):
            print("LLM enabled — OPENAI_API_KEY found in environment (will be used)")
        else:
            print("LLM enabled but OPENAI_API_KEY NOT found. Set it in .env or export it in your shell.")

    if args.command == "chat":
        print("RAG Chat with FAISS (type 'exit' to quit)")
        while True:
            q = input("You: ")
            if q.strip().lower() in ("exit", "quit"):
                break
            print(bot.answer(q))
    elif args.command == "qa":
        if not args.query:
            raise SystemExit("--query required for qa mode")
        print(bot.answer(args.query, use_llm=args.use_llm))
    elif args.command == "eval":
        # evaluation example: test retrieval quality on known queries
        tests = [
            ("working hours", 0),
            ("price", 1),
            ("where is the parking", 2),
        ]
        results = []
        for q, expected_idx in tests:
            hits = store.retrieve(q, k=5)
            found = any(i == expected_idx for i, _ in hits)
            results.append({"query": q, "expected_doc_idx": expected_idx, "found": found})
        print(json.dumps(results, indent=2))
