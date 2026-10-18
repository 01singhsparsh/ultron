import os, json, datetime

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "data", "chroma_db")
os.makedirs(CHROMA_PATH, exist_ok=True)

_client = None; _collection = None

def _get_collection():
    global _client, _collection
    if _collection is not None: return _collection
    try:
        import chromadb
        _client     = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            name="ultron_memories", metadata={"hnsw:space": "cosine"})
        print(f"[SEMANTIC] ChromaDB ready. {_collection.count()} memories stored.")
        return _collection
    except Exception as e:
        print(f"[SEMANTIC] ChromaDB error: {e}"); return None

def store_memory(text, metadata=None):
    try:
        collection = _get_collection()
        if not collection: return False
        doc_id = f"mem_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        meta   = {"timestamp": str(datetime.datetime.now()), "date": str(datetime.date.today()), **(metadata or {})}
        meta   = {k: str(v) for k,v in meta.items()}
        collection.add(documents=[text], metadatas=[meta], ids=[doc_id])
        return True
    except Exception as e:
        print(f"[SEMANTIC] Store error: {e}"); return False

def search_memory(query, n_results=5):
    try:
        collection = _get_collection()
        if not collection or collection.count() == 0: return []
        results = collection.query(query_texts=[query], n_results=min(n_results, collection.count()))
        memories = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                memories.append({
                    "text":     doc,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0,
                })
        return memories
    except Exception as e:
        print(f"[SEMANTIC] Search error: {e}"); return []

def store_conversation(user_text, ultron_reply, topics=None):
    text = f"User said: {user_text}\nULTRON replied: {ultron_reply}"
    return store_memory(text, {"type": "conversation", "topics": json.dumps(topics or []), "user": user_text[:100]})

def store_fact(fact, category="general"):
    return store_memory(fact, {"type": "fact", "category": category})

def get_relevant_context(query):
    memories = search_memory(query, n_results=3)
    if not memories: return ""
    context = "RELEVANT PAST MEMORIES:\n"
    for m in memories:
        date = m["metadata"].get("date","unknown date")
        context += f"  [{date}] {m['text'][:200]}\n"
    return context

def memory_count():
    try:
        collection = _get_collection()
        return collection.count() if collection else 0
    except: return 0