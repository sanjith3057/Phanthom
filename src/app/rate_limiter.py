import os
import time
import sqlite3
from utils import get_project_root

DB_PATH = os.path.join(get_project_root(), "database", "phantom.db")


class RateLimiter:
    """
    Enforces a 15-second Resting Protocol between user interactions.
    """
    def __init__(self, cooldown_seconds: int = 15):
        self.db_path = DB_PATH
        self.cooldown_seconds = cooldown_seconds
        self._ensure_table()

    def _ensure_table(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT DEFAULT 'default',
                timestamp REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def check_cooldown(self, session_id: str = "default") -> tuple:
        """Returns (is_allowed: bool, remaining_seconds: float)."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            'SELECT timestamp FROM interaction_logs WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1',
            (session_id,)
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            return True, 0.0

        elapsed = time.time() - row[0]
        if elapsed >= self.cooldown_seconds:
            return True, 0.0
        return False, round(self.cooldown_seconds - elapsed, 1)

    def record_interaction(self, session_id: str = "default"):
        """Logs this interaction to start the cooldown timer."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO interaction_logs (session_id, timestamp) VALUES (?, ?)',
            (session_id, time.time())
        )
        conn.commit()
        conn.close()
