"""
debugger.py
Auto-debugger for generated projects.
Detects errors and generates fixes automatically.
"""
import os, sys, re
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

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

def fix_code(original_code: str, error: str, filename: str) -> str:
    """Fix code given an error message."""
    if not GROQ_API_KEY:
        return original_code
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        system = """You are ULTRON's Auto-Debugger.
Fix the Python code based on the error message.
Return ONLY the corrected complete code â€” nothing else.
The code must be fully functional after your fix."""
        response = client.chat.completions.create(
            model       = "qwen/qwen3.8-27b",
            messages    = [
                {"role":"system","content":system},
                {"role":"user","content":f"File: {filename}\n\nError:\n{error}\n\nOriginal code:\n```python\n{original_code}\n```\n\nFixed code:"}
            ],
            max_tokens  = 1500,
            temperature = 0.1
        )
        fixed = response.choices[0].message.content.strip()
        if "```python" in fixed: fixed = fixed.split("```python")[1].split("```")[0].strip()
        elif "```"     in fixed: fixed = fixed.split("```")[1].split("```")[0].strip()
        print(f"[DEBUGGER] Fixed {filename}")
        return fixed
    except Exception as e:
        print(f"[DEBUGGER] Fix error: {e}")
        return original_code

def auto_fix_project(folder: str, plan: dict, run_result: dict) -> dict:
    """
    Automatically fix errors in a project.
    Returns updated run_result after fixes.
    """
    error = run_result.get("error","")
    if not error:
        return run_result

    print(f"[DEBUGGER] Auto-fixing errors...")

    # Find which file caused the error
    file_match = re.search(r'File "(.+?)", line (\d+)', error)
    if file_match:
        error_file = os.path.basename(file_match.group(1))
        error_line = file_match.group(2)
        print(f"[DEBUGGER] Error in {error_file} at line {error_line}")
    else:
        # Fix main file by default
        for f in plan.get("files",[]):
            if f.get("is_main"):
                error_file = f["filename"]
                break
        else:
            error_file = plan.get("files",[{}])[0].get("filename","main.py")

    file_path = os.path.join(folder, error_file)
    if not os.path.exists(file_path):
        return run_result

    # Read original code
    with open(file_path,'r',encoding='utf-8') as f:
        original_code = f.read()

    # Generate fix
    fixed_code = fix_code(original_code, error, error_file)

    if fixed_code != original_code:
        with open(file_path,'w',encoding='utf-8') as f:
            f.write(fixed_code)
        print(f"[DEBUGGER] Applied fix to {error_file}")

        # Re-run to verify fix
        from project_builder.code_runner import run_project
        new_result = run_project(folder, plan, timeout=15)
        if new_result.get("success"):
            print(f"[DEBUGGER] Fix successful!")
            return new_result
        else:
            print(f"[DEBUGGER] Fix did not resolve all issues")
            return new_result

    return run_result

def format_code(file_path: str) -> bool:
    """Auto-format Python code using autopep8."""
    try:
        import autopep8
        with open(file_path,'r',encoding='utf-8') as f:
            code = f.read()
        formatted = autopep8.fix_code(code, options={'aggressive':1})
        with open(file_path,'w',encoding='utf-8') as f:
            f.write(formatted)
        return True
    except Exception as e:
        print(f"[DEBUGGER] Format error: {e}")
        return False
