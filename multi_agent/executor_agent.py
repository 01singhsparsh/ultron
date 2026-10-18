import os, sys, subprocess
from multi_agent.base_agent import BaseAgent

class ExecutorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="EXECUTOR", role="System command execution and automation", max_tokens=300)

    def run_powershell(self, cmd):
        try:
            result = subprocess.run(["powershell","-Command",cmd],
                                   capture_output=True, text=True, timeout=60)
            return {"success":result.returncode==0,"output":result.stdout.strip()[:500],"error":result.stderr.strip()[:200]}
        except Exception as e:
            return {"success":False,"output":"","error":str(e)}

    def open_application(self, app):
        try:
            from agents.app_controller import open_app
            return open_app(app)
        except:
            subprocess.Popen(["start","",app], shell=True); return True

    def create_folder(self, path):
        try: os.makedirs(path, exist_ok=True); return True
        except: return False

    def run(self, task, context=None):
        self.log(f"Executing: {task}")
        system = """You are ULTRON's Executor Agent.
Convert the task to a specific command. Return JSON:
{"command_type":"powershell|open_app|create_folder|file_op","command":"exact command","description":"what this does"}"""
        plan     = self.think_json(f"What command executes: {task}", system)
        if not plan:
            return {"agent":"executor_agent","task":task,"success":False,"output":"Could not determine execution plan"}
        cmd_type = plan.get("command_type","powershell")
        command  = plan.get("command","")
        result   = {"agent":"executor_agent","task":task}
        if cmd_type == "open_app":
            success = self.open_application(command)
            result.update({"success":success,"output":f"Opened: {command}"})
        elif cmd_type == "create_folder":
            success = self.create_folder(command)
            result.update({"success":success,"output":f"Created: {command}"})
        elif cmd_type == "powershell" and command:
            exec_result = self.run_powershell(command)
            result.update(exec_result)
        else:
            result.update({"success":False,"output":"Unknown execution type"})
        self.log(f"Execution {'✓' if result.get('success') else '✗'}: {result.get('output','')[:100]}")
        return result