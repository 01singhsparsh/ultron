from multi_agent.base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="PLANNER", role="Strategic task decomposition", max_tokens=600)

    def run(self, task, context=None):
        self.log(f"Planning: {task}")
        system = """You are ULTRON's Planner Agent.
Break down the user's goal into a structured execution plan.
AVAILABLE AGENTS: research_agent, coding_agent, memory_agent, vision_agent, executor_agent, critic_agent
Return JSON:
{
  "goal": "original goal",
  "complexity": "simple|medium|complex",
  "steps": [
    {"step":1,"agent":"agent_name","task":"specific task","depends_on":[],"expected_output":"what this produces"}
  ],
  "final_output": "what the user will receive"
}"""
        result = self.think_json(f"Create execution plan for: {task}", system)
        if not result:
            result = {"goal":task,"complexity":"simple",
                     "steps":[{"step":1,"agent":"research_agent","task":task,"depends_on":[],"expected_output":"answer"}],
                     "final_output":"Direct answer"}
        self.log(f"Plan: {len(result.get('steps',[]))} steps, complexity: {result.get('complexity','?')}")
        return result