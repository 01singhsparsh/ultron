from multi_agent.base_agent import BaseAgent

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MEMORY", role="Personal context and memory retrieval", max_tokens=400)

    def get_full_context(self):
        context = ""
        try:
            from memory.memory_engine   import get_full_context
            context += get_full_context()
        except: pass
        try:
            from memory.episodic_memory import get_context_string
            context += "\n" + get_context_string(5)
        except: pass
        try:
            from memory.semantic_memory import get_relevant_context
            context += "\n" + get_relevant_context("recent activities goals projects")
        except: pass
        return context

    def search_memory(self, query):
        try:
            from memory.semantic_memory import search_memory
            results = search_memory(query, n_results=3)
            if results:
                return "\n".join([f"[{r['metadata'].get('date','?')}] {r['text'][:200]}" for r in results])
        except: pass
        return ""

    def get_user_profile(self):
        try:
            from memory.memory_engine import get_all_profile, get_goals, get_projects
            return {"profile":get_all_profile(),"goals":get_goals()[:5],"projects":get_projects()[:5]}
        except: return {}

    def run(self, task, context=None):
        self.log(f"Retrieving context for: {task}")
        full_context = self.get_full_context()
        memory_hits  = self.search_memory(task)
        profile      = self.get_user_profile()
        system       = "You are ULTRON's Memory Agent. Provide relevant personal context. Be concise. Only include truly relevant information."
        summary      = self.think(
            f"Task: {task}\nContext:\n{full_context[:1000]}\nMemory search:\n{memory_hits}\nSummarize what's relevant.", system)
        return {"agent":"memory_agent","task":task,"context":full_context[:2000],
                "relevant":summary,"profile":profile,"memory_hits":memory_hits[:500]}