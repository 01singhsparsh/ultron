import os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return resultimport os, sys

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROQ_API_KEY = ""

def _load_key():
    global GROQ_API_KEY
    try:
        with open(os.path.join(BASE_DIR, "config.py")) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    GROQ_API_KEY = line.split("=")[1].strip().strip('"').strip("'")
    except: pass

_load_key()

def answer_from_knowledge(question, n_chunks=4):
    from second_brain.vectorstore import search, count
    if count() == 0:
        return {"answer":"Sir, no documents have been ingested yet. Please add files to the knowledge folder.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    chunks   = search(question, n_results=n_chunks)
    if not chunks:
        return {"answer":"Sir, I could not find relevant information in your knowledge base.",
                "sources":[], "confidence":0.0, "chunks_used":0}
    relevant = [c for c in chunks if c["score"] > 0.3]
    if not relevant: relevant = chunks[:2]
    context  = ""
    sources  = list(set(c["source"] for c in relevant))
    for chunk in relevant[:n_chunks]:
        context += f"\n[Source: {chunk['source']}]\n{chunk['text']}\n"
    prompt = f"""You are ULTRON, answering questions from personal knowledge documents.
RETRIEVED KNOWLEDGE:\n{context}\nQUESTION: {question}
INSTRUCTIONS:
- Answer ONLY based on the provided knowledge above
- If knowledge doesn't contain enough info, say so
- Be concise but complete. Cite source document name. Address as Sparsh Sir. Max 3 sentences."""
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=250, temperature=0.3)
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer: {e}"
    avg_score = sum(c["score"] for c in relevant) / len(relevant)
    return {"answer":answer, "sources":sources, "confidence":round(avg_score,2), "chunks_used":len(relevant)}

def summarize_document(source_name):
    from second_brain.vectorstore import search
    chunks = search(f"summary overview introduction {source_name}", n_results=6, filter_source=source_name)
    if not chunks: chunks = search("main content", n_results=6, filter_source=source_name)
    if not chunks: return f"Sir, could not find {source_name} in the knowledge base."
    context = "\n\n".join([c["text"] for c in chunks[:4]])
    prompt  = f"Summarize document '{source_name}' in 3-4 sentences.\nContent: {context[:2000]}\nAddress as Sparsh Sir. Be concise."
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200, temperature=0.3)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization error Sir: {e}"

def is_knowledge_question(text):
    import re; t = text.lower()
    triggers = [
        r'what does my (?:note|pdf|document|lecture|slide)',
        r'according to my', r'from my (?:notes?|document|lecture|pdf|slides?)',
        r'what did (?:my professor|i write|i note)',
        r'summarize (?:my|the) (?:pdf|document|notes?|lecture|ppt)',
        r'explain (?:from|using) my', r'what is in my (?:notes?|pdf|document)',
        r'read my (?:notes?|pdf|document)', r'search my knowledge',
        r'from (?:the )?knowledge base', r'in my (?:notes?|pdf|lecture)',
    ]
    return any(re.search(p, t) for p in triggers)

def list_knowledge():
    from second_brain.vectorstore   import get_all_sources, count
    from second_brain.ingestion     import get_ingested_files
    total = count(); files = get_ingested_files()
    if not files:
        return f"Sir, no documents in knowledge base yet. Add files to: {os.path.join(BASE_DIR,'data','knowledge')}"
    result = f"Sir, knowledge base has {total} chunks from {len(files)} documents:\n"
    for f in files: result += f"  â€¢ {f['name']} ({f['chunks']} chunks, {f['date']})\n"
    return result
