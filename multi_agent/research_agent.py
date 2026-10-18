import urllib.request, urllib.parse, json
from multi_agent.base_agent import BaseAgent

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="RESEARCH", role="Web search and knowledge retrieval", max_tokens=500)

    def web_search(self, query):
        try:
            q   = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())
            results = []
            if data.get("AbstractText"): results.append(data["AbstractText"])
            if data.get("Answer"):       results.append(str(data["Answer"]))
            for t in data.get("RelatedTopics",[])[:4]:
                if isinstance(t,dict) and t.get("Text"): results.append(t["Text"])
            return " | ".join(results[:3]) if results else ""
        except Exception as e:
            self.log(f"Web search error: {e}"); return ""

    def knowledge_search(self, query):
        try:
            from second_brain.vectorstore import search
            chunks = search(query, n_results=3)
            if chunks:
                return "\n".join([f"[{c['source']}]: {c['text'][:300]}" for c in chunks])
        except Exception as e:
            self.log(f"Knowledge search error: {e}")
        return ""

    def weather_search(self, city="Delhi"):
        try:
            url = f"https://wttr.in/{city.replace(' ','+')}?format=3"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r: return r.read().decode().strip()
        except: return ""

    def run(self, task, context=None):
        self.log(f"Researching: {task}")
        task_lower = task.lower()
        web_data = ""; know_data = ""
        if any(w in task_lower for w in ["weather","temperature","forecast"]):
            import re
            city_match = re.search(r'in\s+([a-zA-Z\s]+?)(?:\s*$|\s*\?)', task_lower)
            city       = city_match.group(1).strip() if city_match else "Delhi"
            web_data   = self.weather_search(city)
        else:
            web_data  = self.web_search(task)
            know_data = self.knowledge_search(task)
        system   = "You are ULTRON's Research Agent. Synthesize search results into a clear accurate answer. Address as Sparsh Sir. Max 3 sentences. Only use provided data."
        combined = ""
        if web_data:  combined += f"Web results: {web_data}\n"
        if know_data: combined += f"Personal knowledge: {know_data}\n"
        if combined:
            answer = self.think(f"Task: {task}\nData found:\n{combined}\nProvide clear answer.", system)
        else:
            answer = self.think(f"Answer from your knowledge: {task}", system)
        return {"agent":"research_agent","task":task,"answer":answer,
                "sources":["web","knowledge_base"] if combined else ["ai_knowledge"],"raw_data":combined[:500]}