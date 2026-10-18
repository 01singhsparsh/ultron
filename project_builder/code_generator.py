"""
code_generator.py
Generates complete, working code for each project file.
Uses Groq AI with project context for coherent multi-file projects.
"""
import os, sys
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

def generate_file_code(
    project_plan:  dict,
    file_info:     dict,
    existing_files: dict = None
) -> str:
    """
    Generate complete code for a single file.
    existing_files: dict of {filename: code} already generated
    """
    if not GROQ_API_KEY:
        return "# ULTRON: No API key configured"

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        project_title = project_plan.get("title","Project")
        project_type  = project_plan.get("type","python_script")
        features      = project_plan.get("features",[])
        all_files     = [f["filename"] for f in project_plan.get("files",[])]
        filename      = file_info.get("filename","main.py")
        file_desc     = file_info.get("description","")
        is_main       = file_info.get("is_main", False)

        # Build context from already generated files
        context = ""
        if existing_files:
            for fname, fcode in existing_files.items():
                context += f"\n--- Already generated: {fname} ---\n{fcode[:500]}\n"

        # Determine file type for specific instructions
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".py":
            lang_hint = "Python"
            if project_type == "python_gui":
                lang_hint = "Python with tkinter GUI"
        elif ext == ".html":
            lang_hint = "HTML5"
        elif ext == ".css":
            lang_hint = "CSS3"
        elif ext == ".js":
            lang_hint = "JavaScript"
        else:
            lang_hint = "code"

        system = f"""You are ULTRON's Code Generator â€” an expert {lang_hint} developer.
Generate complete, working, production-ready code.

PROJECT: {project_title}
TYPE: {project_type}
FEATURES: {', '.join(features)}
ALL PROJECT FILES: {', '.join(all_files)}
THIS FILE: {filename} â€” {file_desc}

RULES:
1. Write COMPLETE working code â€” no placeholders, no TODOs
2. Every function must be fully implemented
3. Include proper error handling
4. Add helpful comments
5. For Python GUI: use tkinter, make it look nice with colors and fonts
6. For web: make it responsive and modern looking
7. Code must work immediately when run
8. Return ONLY the code, no explanations
9. Start with: # ULTRON Generated â€” {filename}
"""

        prompt = f"Generate complete {lang_hint} code for: {filename}\nDescription: {file_desc}"
        if is_main:
            prompt += f"\nThis is the MAIN file â€” make it the entry point that ties everything together."
        if context:
            prompt += f"\nContext from other files:{context}"

        response = client.chat.completions.create(
            model       = "qwen/qwen3.8-27b",
            messages    = [
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt}
            ],
            max_tokens  = 1500,
            temperature = 0.2
        )

        code = response.choices[0].message.content.strip()

        # Clean up markdown code blocks
        if f"```{lang_hint.lower()}" in code.lower():
            for marker in ["```python","```html","```css","```javascript","```js","```"]:
                if marker in code:
                    code = code.split(marker)[1].split("```")[0].strip()
                    break
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        print(f"[GENERATOR] Generated {filename} ({len(code)} chars)")
        return code

    except Exception as e:
        print(f"[GENERATOR] Error generating {file_info.get('filename','?')}: {e}")
        return f"# ULTRON: Error generating code â€” {e}\nprint('Error in generation')"

def generate_readme(project_plan: dict) -> str:
    """Generate a README.md for the project."""
    title    = project_plan.get("title","My Project")
    desc     = project_plan.get("description","")
    features = project_plan.get("features",[])
    files    = [f["filename"] for f in project_plan.get("files",[])]
    run_cmd  = project_plan.get("run_command","python main.py")

    readme = f"""# {title}

> Built by ULTRON â€” Advanced AI Assistant

## Description
{desc}

## Features
"""
    for feature in features:
        readme += f"- {feature}\n"

    readme += f"""
## Files
"""
    for f in project_plan.get("files",[]):
        readme += f"- `{f['filename']}` â€” {f['description']}\n"

    readme += f"""
## How to Run
