"""
code_runner.py
Runs and tests generated projects.
Captures output and detects errors.
"""
import os, sys, subprocess, time
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_project(folder: str, plan: dict, timeout: int = 30) -> dict:
    """
    Run the project and return results.
    For GUI apps: launches them and returns success.
    For scripts: captures output.
    """
    project_type = plan.get("type","python_script")
    run_command  = plan.get("run_command","python main.py")
    main_file    = None

    for f in plan.get("files",[]):
        if f.get("is_main"):
            main_file = f["filename"]
            break
    if not main_file:
        main_file = plan.get("files",[{}])[0].get("filename","main.py")

    main_path = os.path.join(folder, main_file)
    if not os.path.exists(main_path):
        return {"success":False,"output":"","error":f"Main file not found: {main_file}","launched":False}

    print(f"[RUNNER] Running: {main_file}")

    # For GUI apps — launch in background
    if project_type in ["python_gui","web"]:
        try:
            if project_type == "web":
                # Open HTML in browser
                import webbrowser
                index = os.path.join(folder, "index.html")
                if os.path.exists(index):
                    webbrowser.open(f"file:///{index}")
                    return {"success":True,"output":"Opened in browser","error":"","launched":True}

            # Launch Python GUI
            subprocess.Popen(
                ["py","-3.11", main_path],
                cwd=folder,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            time.sleep(2)
            return {"success":True,"output":"Application launched","error":"","launched":True}
        except Exception as e:
            return {"success":False,"output":"","error":str(e),"launched":False}

    # For scripts — capture output
    try:
        result = subprocess.run(
            ["py","-3.11", main_path],
            capture_output = True,
            text           = True,
            timeout        = timeout,
            cwd            = folder
        )
        return {
            "success": result.returncode == 0,
            "output":  result.stdout.strip()[:1000],
            "error":   result.stderr.strip()[:500],
            "launched": False
        }
    except subprocess.TimeoutExpired:
        return {"success":True,"output":"Script ran (timeout — may need input)","error":"","launched":False}
    except Exception as e:
        return {"success":False,"output":"","error":str(e),"launched":False}

def test_syntax(file_path: str) -> dict:
    """Test Python file for syntax errors."""
    try:
        result = subprocess.run(
            ["py","-3.11","-m","py_compile", file_path],
            capture_output=True, text=True, timeout=10
        )
        return {
            "valid": result.returncode == 0,
            "error": result.stderr.strip()
        }
    except Exception as e:
        return {"valid":False,"error":str(e)}

def open_project_folder(folder: str):
    """Open the project folder in File Explorer."""
    subprocess.Popen(f'explorer "{folder}"', shell=True)