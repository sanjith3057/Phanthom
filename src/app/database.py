import sqlite3
import os
from utils import get_project_root

# Always resolve DB path relative to the project root — never relative to CWD
DB_PATH = os.path.join(get_project_root(), "database", "phantom.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT DEFAULT 'default',
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def save_message(role: str, content: str, session_id: str = "default"):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)',
        (session_id, role, content)
    )
    conn.commit()
    conn.close()


def get_history(session_id: str = "default", limit: int = 50) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        'SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC LIMIT ?',
        (session_id, limit)
    )
    rows = cur.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]
