import os, sys, subprocess, tempfile
from multi_agent.base_agent import BaseAgent

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESKTOP  = os.path.join(os.path.expanduser("~"), "Desktop")

class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="CODING", role="Python code generation debugging and execution", max_tokens=1000)

    def write_code(self, task, context=""):
        system = """You are ULTRON's Coding Agent — expert Python developer.
Write clean working production-ready Python code with comments.
Return ONLY the Python code. Start with: # ULTRON Generated Code"""
        prompt = f"Write Python code to: {task}"
        if context: prompt += f"\nContext: {context}"
        code = self.think(prompt, system)
        if "```python" in code: code = code.split("```python")[1].split("```")[0].strip()
        elif "```"     in code: code = code.split("```")[1].split("```")[0].strip()
        return code

    def review_code(self, code):
        system = """You are a senior code reviewer. Review code and return JSON:
{"has_issues":true/false,"issues":["issue1"],"improved_code":"fixed code","score":0-10}"""
        result = self.think_json(f"Review this code:\n```python\n{code}\n```", system)
        if not result: return {"has_issues":False,"issues":[],"improved_code":code,"score":8}
        return result

    def execute_code(self, code, timeout=30):
        tmp_file = tempfile.mktemp(suffix=".py")
        try:
            with open(tmp_file,'w',encoding='utf-8') as f: f.write(code)
            result = subprocess.run(
                ["py","-3.11",tmp_file], capture_output=True, text=True,
                timeout=timeout, cwd=os.path.expanduser("~\\Desktop"))
            return {"success":result.returncode==0,"output":result.stdout.strip()[:1000],
                    "error":result.stderr.strip()[:500],"code":code}
        except subprocess.TimeoutExpired:
            return {"success":False,"output":"","error":"Timeout","code":code}
        except Exception as e:
            return {"success":False,"output":"","error":str(e),"code":code}
        finally:
            try: os.remove(tmp_file)
            except: pass

    def debug_code(self, code, error):
        system = "You are a Python debugger. Fix the code based on the error. Return ONLY corrected Python code."
        fixed = self.think(f"Fix this code:\n```python\n{code}\n```\nError: {error}", system)
        if "```python" in fixed: fixed = fixed.split("```python")[1].split("```")[0].strip()
        elif "```"     in fixed: fixed = fixed.split("```")[1].split("```")[0].strip()
        return fixed

    def save_code(self, code, filename=None):
        import time
        if not filename: filename = f"ultron_code_{int(time.time())}.py"
        path = os.path.join(DESKTOP, filename)
        with open(path,'w',encoding='utf-8') as f: f.write(code)
        self.log(f"Code saved: {path}"); return path

    def run(self, task, context=None):
        self.log(f"Coding task: {task}")
        code = self.write_code(task, str(context or ""))
        if not code:
            return {"agent":"coding_agent","task":task,"success":False,"error":"Could not generate code"}
        review = self.review_code(code)
        if review.get("has_issues") and review.get("improved_code"):
            code = review["improved_code"]
            self.log(f"Code improved. Score: {review.get('score','?')}/10")
        path   = self.save_code(code)
        result = {"agent":"coding_agent","task":task,"code":code,"path":path,"success":True,"executed":False,"output":""}
        if any(w in task.lower() for w in ["run","execute","calculate","compute","print","output"]):
            self.log("Executing code...")
            exec_result = self.execute_code(code)
            result["executed"] = True; result["output"] = exec_result.get("output","")
            result["success"]  = exec_result.get("success",False)
            if not exec_result["success"] and exec_result.get("error"):
                fixed       = self.debug_code(code, exec_result["error"])
                exec_result2 = self.execute_code(fixed)
                if exec_result2["success"]:
                    result["code"] = fixed; result["output"] = exec_result2["output"]
                    result["success"] = True; self.save_code(fixed, "ultron_fixed_code.py")
        return result