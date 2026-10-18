"""
memory_engine.py
Core long-term memory engine using SQLite.
Stores everything ULTRON learns about Sparsh Sir.
"""
import sqlite3, os, json, datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "ultron_memory.db")
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_conn(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS user_profile (
        key TEXT PRIMARY KEY, value TEXT NOT NULL,
        category TEXT DEFAULT 'general', confidence REAL DEFAULT 1.0,
        updated_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        description TEXT, status TEXT DEFAULT 'active', tech_stack TEXT,
        last_worked TEXT DEFAULT (datetime('now')), created_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT, goal TEXT NOT NULL,
        category TEXT DEFAULT 'general', priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'active', deadline TEXT,
        created_at TEXT DEFAULT (datetime('now')), completed_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS learning_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL,
        subject TEXT, source TEXT, notes TEXT, mastery REAL DEFAULT 0.0,
        studied_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS preferences (
        key TEXT PRIMARY KEY, value TEXT NOT NULL,
        category TEXT DEFAULT 'general', updated_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, activity TEXT NOT NULL,
        category TEXT DEFAULT 'general', duration INTEGER DEFAULT 0,
        logged_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS conversation_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT, summary TEXT NOT NULL,
        topics TEXT, mood TEXT DEFAULT 'neutral',
        date TEXT DEFAULT (date('now')), created_at TEXT DEFAULT (datetime('now')))""")
    conn.commit(); conn.close()
    print("[MEMORY] Database initialized.")

def set_profile(key, value, category="general"):
    conn = _get_conn()
    conn.execute("INSERT OR REPLACE INTO user_profile (key,value,category,updated_at) VALUES (?,?,?,datetime('now'))",
                (key.lower(), value, category))
    conn.commit(); conn.close()

def get_profile(key):
    conn = _get_conn()
    row  = conn.execute("SELECT value FROM user_profile WHERE key=?", (key.lower(),)).fetchone()
    conn.close()
    return row["value"] if row else None

def get_all_profile():
    conn  = _get_conn()
    rows  = conn.execute("SELECT key,value,category FROM user_profile").fetchall()
    conn.close()
    return {r["key"]: {"value": r["value"], "category": r["category"]} for r in rows}

def add_project(name, description="", tech_stack=""):
    conn = _get_conn()
    cur  = conn.execute("INSERT INTO projects (name,description,tech_stack) VALUES (?,?,?)",
                       (name, description, tech_stack))
    pid  = cur.lastrowid; conn.commit(); conn.close(); return pid

def get_projects(status="active"):
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM projects WHERE status=? ORDER BY last_worked DESC",
                       (status,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_recent_project():
    conn = _get_conn()
    row  = conn.execute("SELECT * FROM projects ORDER BY last_worked DESC LIMIT 1").fetchone()
    conn.close(); return dict(row) if row else {}

def add_goal(goal, category="general", priority="medium", deadline=None):
    conn = _get_conn()
    cur  = conn.execute("INSERT INTO goals (goal,category,priority,deadline) VALUES (?,?,?,?)",
                       (goal, category, priority, deadline))
    gid  = cur.lastrowid; conn.commit(); conn.close(); return gid

def get_goals(status="active"):
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM goals WHERE status=? ORDER BY priority DESC", (status,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def log_learning(topic, subject="", source="", notes="", mastery=0.5):
    conn = _get_conn()
    conn.execute("INSERT INTO learning_history (topic,subject,source,notes,mastery) VALUES (?,?,?,?,?)",
                (topic, subject, source, notes, mastery))
    conn.commit(); conn.close()

def get_learning_history(subject=None):
    conn = _get_conn()
    if subject:
        rows = conn.execute("SELECT * FROM learning_history WHERE subject LIKE ? ORDER BY studied_at DESC",
                           (f"%{subject}%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM learning_history ORDER BY studied_at DESC LIMIT 20").fetchall()
    conn.close(); return [dict(r) for r in rows]

def set_preference(key, value, category="general"):
    conn = _get_conn()
    conn.execute("INSERT OR REPLACE INTO preferences (key,value,category,updated_at) VALUES (?,?,?,datetime('now'))",
                (key.lower(), value, category))
    conn.commit(); conn.close()

def log_activity(activity, category="general", duration=0):
    conn = _get_conn()
    conn.execute("INSERT INTO activity_log (activity,category,duration) VALUES (?,?,?)",
                (activity, category, duration))
    conn.commit(); conn.close()

def get_today_activities():
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM activity_log WHERE date(logged_at)=date('now') ORDER BY logged_at DESC").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_weekly_summary():
    conn = _get_conn()
    rows = conn.execute("""SELECT category, COUNT(*) as count, SUM(duration) as total_time
        FROM activity_log WHERE logged_at >= datetime('now','-7 days') GROUP BY category""").fetchall()
    conn.close()
    return {r["category"]: {"count": r["count"], "total_time": r["total_time"]} for r in rows}

def get_full_context():
    profile  = get_all_profile()
    projects = get_projects()
    goals    = get_goals()
    learning = get_learning_history()
    context  = "=== ULTRON MEMORY CONTEXT ===\n\n"
    if profile:
        context += "USER PROFILE:\n"
        for key, data in profile.items():
            context += f"  {key}: {data['value']}\n"
        context += "\n"
    if projects:
        context += "ACTIVE PROJECTS:\n"
        for p in projects[:5]: context += f"  - {p['name']}: {p.get('description','')}\n"
        context += "\n"
    if goals:
        context += "CURRENT GOALS:\n"
        for g in goals[:5]: context += f"  - [{g['priority'].upper()}] {g['goal']}\n"
        context += "\n"
    if learning:
        context += "RECENT LEARNING:\n"
        for l in learning[:5]: context += f"  - {l['topic']} ({l.get('subject','')})\n"
    return context

init_db()