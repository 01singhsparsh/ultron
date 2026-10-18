import os, sys, time
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from multi_agent.planner_agent   import PlannerAgent
from multi_agent.research_agent  import ResearchAgent
from multi_agent.coding_agent    import CodingAgent
from multi_agent.memory_agent    import MemoryAgent
from multi_agent.critic_agent    import CriticAgent
from multi_agent.executor_agent  import ExecutorAgent
from modules.speaker             import speak

class Orchestrator:
    def __init__(self):
        self.planner  = PlannerAgent()
        self.research = ResearchAgent()
        self.coding   = CodingAgent()
        self.memory   = MemoryAgent()
        self.critic   = CriticAgent()
        self.executor = ExecutorAgent()
        self.agent_map = {
            "planner_agent":  self.planner,
            "research_agent": self.research,
            "coding_agent":   self.coding,
            "memory_agent":   self.memory,
            "critic_agent":   self.critic,
            "executor_agent": self.executor,
        }
        self.is_running = False
        print("[ORCHESTRATOR] Multi-Agent System initialized — 6 agents ready")

    def _quick_classify(self, task):
        t = task.lower()
        if any(w in t for w in ["write code","python script","code to","program to"]): return "coding"
        if any(w in t for w in ["search","find","what is","who is","weather","news"]): return "research"
        if any(w in t for w in ["open","install","create folder","run command"]):      return "execution"
        if any(w in t for w in ["remember","my goal","my project","from memory"]):     return "memory"
        return "research"

    def run(self, task):
        if self.is_running: return "Sir, I am already working on a task. Please wait."
        self.is_running = True
        start_time      = time.time()
        print(f"\n{'='*50}\n[ORCHESTRATOR] New task: {task}\n{'='*50}")
        try:
            speak("Activating multi-agent system Sir.")
            memory_result = self.memory.run(task)
            context       = {"task":task,"memory":memory_result.get("relevant",""),"profile":memory_result.get("profile",{})}
            plan          = self.planner.run(task, context)
            steps         = plan.get("steps",[])
            speak(f"Plan ready. {len(steps)} steps. Executing now Sir.")
            results = {}; final_answer = ""
            for step_info in steps:
                step_num   = step_info.get("step",1)
                agent_name = step_info.get("agent","research_agent")
                step_task  = step_info.get("task",task)
                print(f"\n[ORCHESTRATOR] Step {step_num}: {agent_name} — {step_task[:60]}")
                agent = self.agent_map.get(agent_name)
                if not agent: print(f"[ORCHESTRATOR] Unknown agent: {agent_name}"); continue
                result = agent.run(step_task, {**context,"previous_results":results})
                results[f"step_{step_num}"] = result
                if result.get("answer"):                             final_answer = result["answer"]
                elif result.get("output") and result.get("success"): final_answer = result["output"]
                elif result.get("code"):                             final_answer = f"Code generated and saved to Desktop Sir."
            if final_answer:
                critic_result = self.critic.run(task, {"question":task,"answer":final_answer})
                final_answer  = critic_result.get("final_answer", final_answer)
                print(f"[ORCHESTRATOR] Quality score: {critic_result.get('quality_score',7)}/10")
            if not final_answer:
                final_answer = "Sir, I completed the analysis. Please check Desktop for generated files."
            elapsed = round(time.time()-start_time,1)
            print(f"\n[ORCHESTRATOR] Task complete in {elapsed}s")
            try:
                from memory.memory_engine import log_activity
                log_activity(f"Multi-agent task: {task[:80]}", category="agent")
            except: pass
            return final_answer
        except Exception as e:
            print(f"[ORCHESTRATOR] Error: {e}")
            return f"Sir, the multi-agent system encountered an error: {str(e)[:100]}"
        finally:
            self.is_running = False

    def quick_run(self, task):
        category = self._quick_classify(task)
        print(f"[ORCHESTRATOR] Quick run — category: {category}")
        if category == "coding":
            result = self.coding.run(task)
            return f"Code executed Sir. Output: {result['output']}" if result.get("output") else "Code written and saved to Desktop Sir."
        elif category == "research":
            result = self.research.run(task)
            return result.get("answer","Could not find information Sir.")
        elif category == "execution":
            result = self.executor.run(task)
            return result.get("output","Execution attempted Sir.")
        elif category == "memory":
            result = self.memory.run(task)
            return result.get("relevant","No relevant memory found Sir.")
        else:
            result = self.research.run(task)
            return result.get("answer","Could not process Sir.")

_orchestrator = None

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None: _orchestrator = Orchestrator()
    return _orchestrator

def run_multi_agent(task, quick=False):
    orch = get_orchestrator()
    return orch.quick_run(task) if quick else orch.run(task)

def needs_multi_agent(text):
    import re; t = text.lower()
    triggers = [
        r'research .+ and (summarize|explain|write)',
        r'write (a |an )?(python |code |script )',
        r'build (a |an )?', r'create (a |an )?(app|script|program|tool)',
        r'fix (the |this |my )?error', r'debug',
        r'what should i (study|learn|work on)', r'plan (my|a)',
        r'help me (understand|learn|build|create)',
    ]
    return any(re.search(p, t) for p in triggers)