import os, re

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "data", "second_brain_db")
os.makedirs(CHROMA_PATH, exist_ok=True)

CHUNK_SIZE    = 800
CHUNK_OVERLAP = 150

_client = None; _collection = None

def _get_collection():
    global _client, _collection
    if _collection is not None: return _collection
    try:
        import chromadb
        _client     = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            name="second_brain", metadata={"hnsw:space":"cosine"})
        print(f"[VECTORSTORE] Ready — {_collection.count()} chunks stored.")
        return _collection
    except Exception as e:
        print(f"[VECTORSTORE] Error: {e}"); return None

def _chunk_text(text):
    text   = re.sub(r'\n{3,}', '\n\n', text)
    chunks = []; start = 0
    while start < len(text):
        end   = start + CHUNK_SIZE
        chunk = text[start:end].strip()
        if len(chunk) > 50: chunks.append(chunk)
        start = end - CHUNK_OVERLAP
        if start >= len(text): break
    return chunks

def add_document(text, metadata=None):
    collection = _get_collection()
    if not collection: return 0
    chunks = _chunk_text(text)
    source = (metadata or {}).get("source","unknown")
    ids=[]; docs=[]; metas=[]
    for i, chunk in enumerate(chunks):
        chunk_id = f"{source}_{i}_{hash(chunk)%100000}"
        ids.append(chunk_id); docs.append(chunk)
        meta = {k: str(v) for k,v in (metadata or {}).items()}
        meta["chunk_index"] = str(i); meta["total_chunks"] = str(len(chunks))
        metas.append(meta)
    try:
        added = 0
        for i in range(0, len(ids), 50):
            collection.add(ids=ids[i:i+50], documents=docs[i:i+50], metadatas=metas[i:i+50])
            added += len(ids[i:i+50])
        print(f"[VECTORSTORE] Added {added} chunks from {source}"); return added
    except Exception as e:
        print(f"[VECTORSTORE] Add error: {e}"); return 0

def search(query, n_results=5, filter_source=None):
    collection = _get_collection()
    if not collection or collection.count() == 0: return []
    try:
        where  = {"source": filter_source} if filter_source else None
        kwargs = {"query_texts":[query], "n_results":min(n_results, collection.count())}
        if where: kwargs["where"] = where
        results = collection.query(**kwargs)
        chunks  = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                chunks.append({
                    "text":     doc,
                    "source":   results["metadatas"][0][i].get("source",""),
                    "category": results["metadatas"][0][i].get("category",""),
                    "score":    1 - results["distances"][0][i],
                    "metadata": results["metadatas"][0][i],
                })
        return sorted(chunks, key=lambda x: x["score"], reverse=True)
    except Exception as e:
        print(f"[VECTORSTORE] Search error: {e}"); return []

def get_all_sources():
    collection = _get_collection()
    if not collection or collection.count() == 0: return []
    try:
        results = collection.get(limit=1000)
        sources = list(set(m.get("source","") for m in results.get("metadatas",[])))
        return [s for s in sources if s]
    except: return []

def delete_source(source):
    collection = _get_collection()
    if not collection: return
    try: collection.delete(where={"source":source}); print(f"[VECTORSTORE] Deleted: {source}")
    except Exception as e: print(f"[VECTORSTORE] Delete error: {e}")

def count():
    try: return _get_collection().count()
    except: return 0