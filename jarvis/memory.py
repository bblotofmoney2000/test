import sqlite3
import os
from datetime import datetime

DB = os.path.expanduser('~/.jarvis_memory.db')


def _conn():
    return sqlite3.connect(DB)


def init():
    with _conn() as c:
        c.executescript('''
            CREATE TABLE IF NOT EXISTS messages (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                role      TEXT NOT NULL,
                content   TEXT NOT NULL,
                ts        DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS notes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT NOT NULL,
                content   TEXT NOT NULL,
                category  TEXT DEFAULT 'general',
                ts        DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT,
                status      TEXT DEFAULT 'pending',
                due_date    TEXT,
                ts          DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS facts (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                ts    DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')


# ── Messages ──────────────────────────────────────────────────────────────────

def add_message(role: str, content: str):
    with _conn() as c:
        c.execute('INSERT INTO messages (role, content) VALUES (?,?)', (role, content))


def get_history(limit: int = 40) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            'SELECT role, content, ts FROM messages ORDER BY id DESC LIMIT ?', (limit,)
        ).fetchall()
    return [{'role': r[0], 'content': r[1], 'ts': r[2]} for r in reversed(rows)]


# ── Notes ─────────────────────────────────────────────────────────────────────

def save_note(title: str, content: str, category: str = 'general') -> int:
    with _conn() as c:
        cur = c.execute(
            'INSERT INTO notes (title, content, category) VALUES (?,?,?)', (title, content, category)
        )
        return cur.lastrowid


def get_notes(category: str | None = None) -> list[dict]:
    with _conn() as c:
        if category:
            rows = c.execute(
                'SELECT id, title, content, category, ts FROM notes WHERE category=? ORDER BY id DESC', (category,)
            ).fetchall()
        else:
            rows = c.execute(
                'SELECT id, title, content, category, ts FROM notes ORDER BY id DESC'
            ).fetchall()
    return [{'id': r[0], 'title': r[1], 'content': r[2], 'category': r[3], 'ts': r[4]} for r in rows]


# ── Tasks ─────────────────────────────────────────────────────────────────────

def create_task(title: str, description: str = '', due_date: str = '') -> int:
    with _conn() as c:
        cur = c.execute(
            'INSERT INTO tasks (title, description, due_date) VALUES (?,?,?)', (title, description, due_date)
        )
        return cur.lastrowid


def get_tasks(status: str | None = None) -> list[dict]:
    with _conn() as c:
        if status:
            rows = c.execute(
                'SELECT id, title, description, status, due_date, ts FROM tasks WHERE status=? ORDER BY id DESC', (status,)
            ).fetchall()
        else:
            rows = c.execute(
                'SELECT id, title, description, status, due_date, ts FROM tasks ORDER BY id DESC'
            ).fetchall()
    return [{'id': r[0], 'title': r[1], 'description': r[2], 'status': r[3], 'due': r[4], 'ts': r[5]} for r in rows]


def complete_task(task_id: int):
    with _conn() as c:
        c.execute('UPDATE tasks SET status="completed" WHERE id=?', (task_id,))


# ── Facts (long-term memory) ───────────────────────────────────────────────────

def remember_fact(key: str, value: str):
    with _conn() as c:
        c.execute(
            'INSERT OR REPLACE INTO facts (key, value, ts) VALUES (?,?,?)',
            (key, value, datetime.now().isoformat())
        )


def get_facts() -> dict:
    with _conn() as c:
        rows = c.execute('SELECT key, value FROM facts').fetchall()
    return {r[0]: r[1] for r in rows}


# ── Stats ─────────────────────────────────────────────────────────────────────

def stats() -> dict:
    with _conn() as c:
        msgs   = c.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
        notes  = c.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
        tasks  = c.execute('SELECT COUNT(*) FROM tasks WHERE status="pending"').fetchone()[0]
    return {'messages': msgs, 'notes': notes, 'pending_tasks': tasks}
