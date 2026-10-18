"""
builder.py
Main Autonomous Project Builder.
ULTRON's Stage 6 — one sentence → complete working project.
"""
import os, sys, time
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from modules.speaker import speak

def build_project(description: str) -> dict:
    """
    Main function — takes a description and builds a complete project.
    Steps:
    1. Plan project structure
    2. Generate all files
    3. Run syntax checks
    4. Launch/run project
    5. Auto-fix errors if any
    6. Report results
    """
    print(f"\n{'='*60}")
    print(f"[BUILDER] Starting project: {description}")
    print(f"{'='*60}")

    start_time = time.time()

    # STEP 1 — Plan
    speak("Planning your project Sir. One moment.")
    from project_builder.project_planner  import plan_project, get_project_folder
    from project_builder.code_generator   import generate_file_code, generate_readme
    from project_builder.code_runner      import run_project, test_syntax, open_project_folder
    from project_builder.debugger         import auto_fix_project, format_code

    plan = plan_project(description)
    if not plan:
        speak("Sorry Sir. Could not plan the project. Please try again.")
        return {"success":False,"error":"Planning failed"}

    project_name = plan.get("name","my_project")
    project_title= plan.get("title","My Project")
    files        = plan.get("files",[])

    speak(f"Building {project_title} Sir. Generating {len(files)} files.")
    print(f"[BUILDER] Plan: {project_title} — {len(files)} files")

    # STEP 2 — Create project folder
    folder = get_project_folder(project_name)
    print(f"[BUILDER] Project folder: {folder}")

    # STEP 3 — Generate all files
    generated_files = {}
    for i, file_info in enumerate(files):
        filename = file_info.get("filename","main.py")
        speak(f"Writing {filename} Sir.")
        print(f"[BUILDER] Generating file {i+1}/{len(files)}: {filename}")

        code = generate_file_code(plan, file_info, generated_files)
        generated_files[filename] = code

        # Save file
        file_path = os.path.join(folder, filename)
        with open(file_path,'w',encoding='utf-8') as f:
            f.write(code)
        print(f"[BUILDER] Saved: {file_path}")

        # Format Python files
        if filename.endswith(".py"):
            format_code(file_path)

    # Generate README
    readme_path = os.path.join(folder, "README.md")
    with open(readme_path,'w',encoding='utf-8') as f:
        f.write(generate_readme(plan))

    # STEP 4 — Syntax check all Python files
    speak("Checking code quality Sir.")
    syntax_errors = []
    for file_info in files:
        filename = file_info.get("filename","")
        if filename.endswith(".py"):
            file_path = os.path.join(folder, filename)
            result    = test_syntax(file_path)
            if not result["valid"]:
                syntax_errors.append({"file":filename,"error":result["error"]})
                print(f"[BUILDER] Syntax error in {filename}: {result['error']}")

    # Auto-fix syntax errors
    if syntax_errors:
        speak("Found some issues Sir. Auto-fixing now.")
        for err in syntax_errors:
            file_path = os.path.join(folder, err["file"])
            with open(file_path,'r',encoding='utf-8') as f:
                code = f.read()
            from project_builder.debugger import fix_code
            fixed = fix_code(code, err["error"], err["file"])
            with open(file_path,'w',encoding='utf-8') as f:
                f.write(fixed)

    # STEP 5 — Run project
    speak(f"Launching {project_title} Sir.")
    run_result = run_project(folder, plan, timeout=20)

    # STEP 6 — Auto-fix runtime errors
    if not run_result.get("success") and run_result.get("error"):
        speak("Detected an error Sir. Auto-fixing.")
        run_result = auto_fix_project(folder, plan, run_result)

    # STEP 7 — Open project folder
    open_project_folder(folder)

    # STEP 8 — Report
    elapsed = round(time.time() - start_time, 1)
    print(f"\n[BUILDER] Completed in {elapsed}s")
    print(f"[BUILDER] Folder: {folder}")
    print(f"[BUILDER] Files: {list(generated_files.keys())}")
    print(f"[BUILDER] Success: {run_result.get('success',False)}")

    if run_result.get("success"):
        if run_result.get("launched"):
            speak(f"Done Sir! {project_title} is now running. Project folder opened on your Desktop.")
        else:
            output = run_result.get("output","")
            if output:
                speak(f"Done Sir! {project_title} completed. Output: {output[:100]}")
            else:
                speak(f"Done Sir! {project_title} built successfully. Check your Desktop.")
    else:
        speak(f"Sir, {project_title} was built but had some issues. Check the project folder on your Desktop.")

    # Save to memory
    try:
        from memory.memory_engine import add_project, log_activity
        add_project(project_title, description, plan.get("type",""))
        log_activity(f"Built project: {project_title}", category="project")
    except: pass

    return {
        "success":     run_result.get("success",False),
        "title":       project_title,
        "folder":      folder,
        "files":       list(generated_files.keys()),
        "run_result":  run_result,
        "elapsed":     elapsed
    }

def is_build_request(text: str) -> bool:
    """Check if user wants to build a project."""
    import re
    t = text.lower()
    triggers = [
        r'build (me )?(a |an )?',
        r'create (me )?(a |an )?(app|website|tool|script|program|project|game)',
        r'make (me )?(a |an )?(app|website|tool|script|program|project|game)',
        r'develop (a |an )?',
        r'code (me )?(a |an )?',
        r'write (me )?(a |an )?(app|program|tool|script|game)',
        r'generate (a |an )?(app|project|website)',
        r'build a project',
        r'autonomous(ly)? build',
    ]
    return any(re.search(p, t) for p in triggers)