import sqlite3
from typing import Tuple, Optional

class CommandCache:
    def __init__(self, db_file="ai_shell.db"):
        self.conn = sqlite3.connect(db_file)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            query TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            explanation TEXT,
            usage_count INTEGER DEFAULT 1,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()

    def get(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        cursor = self.conn.execute(
            "SELECT command, explanation FROM commands WHERE query = ?",
            (query,)
        )
        result = cursor.fetchone()
        if result:
            self.conn.execute(
                "UPDATE commands SET usage_count = usage_count + 1 WHERE query = ?",
                (query,)
            )
            self.conn.commit()
        return result or (None, None)

    def save(self, query: str, command: str, explanation: str = None):
        self.conn.execute(
            """
            INSERT INTO commands (query, command, explanation) 
            VALUES (?, ?, ?)
            ON CONFLICT(query) DO UPDATE SET
                command = excluded.command,
                explanation = excluded.explanation,
                usage_count = usage_count + 1
            """,
            (query, command, explanation)
        )
        self.conn.commit()