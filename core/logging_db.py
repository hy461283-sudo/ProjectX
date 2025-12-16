import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from .models import Event, Action, AuditEntry

DB_PATH = 'system_monitor.db'
SCHEMA_PATH = 'schema.sql'

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        try:
            # Basic migration: try adding columns if they don't exist
            # This is a naive migration for MVP
            try:
                conn.execute("ALTER TABLE actions ADD COLUMN target_process TEXT")
                conn.execute("ALTER TABLE actions ADD COLUMN target_service TEXT")
                conn.execute("ALTER TABLE actions ADD COLUMN files_deleted TEXT")
            except sqlite3.OperationalError:
                pass # Columns probably exist
        except Exception:
            pass
            
        with open(SCHEMA_PATH, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

    def log_event(self, event: Event) -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO events (timestamp, type, severity, description, metric_value, threshold)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (event.timestamp, event.type, event.severity, event.description, event.metric_value, event.threshold)
        )
        conn.commit()
        event_id = cur.lastrowid
        conn.close()
        return event_id

    def log_action(self, action: Action, extra: dict = None) -> int:
        if extra is None:
            extra = {}
        
        conn = self.get_connection()
        cur = conn.cursor()
        
        target_process = extra.get('target_process')
        target_service = extra.get('target_service')
        files_deleted = extra.get('files_deleted')

        cur.execute(
            '''INSERT INTO actions (
                event_id, timestamp, type, status, output, duration_ms,
                target_process, target_service, files_deleted
            )
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                action.event_id, action.timestamp, action.type, action.status, 
                action.output, action.duration_ms,
                target_process, target_service, files_deleted
            )
        )
        conn.commit()
        action_id = cur.lastrowid
        conn.close()
        return action_id

    def log_audit(self, entry: AuditEntry):
        conn = self.get_connection()
        conn.execute(
            '''INSERT INTO audit_log (timestamp, action_id, affected_resources, status)
               VALUES (?, ?, ?, ?)''',
            (entry.timestamp, entry.action_id, entry.affected_resources, entry.status)
        )
        conn.commit()
        conn.close()

    def get_settings(self) -> Dict[str, str]:
        conn = self.get_connection()
        cur = conn.execute("SELECT key, value FROM settings")
        rows = cur.fetchall()
        conn.close()
        return {row['key']: row['value'] for row in rows}

    def update_setting(self, key: str, value: str):
        conn = self.get_connection()
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()

    def get_recent_events(self, limit=100) -> List[dict]:
        conn = self.get_connection()
        cur = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_recent_actions(self, limit=50) -> List[dict]:
        conn = self.get_connection()
        cur = conn.execute("SELECT * FROM actions ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def create_recommendation(self, event_id: int, category: str, recommendation_text: str, 
                            action_type: str = None, priority: str = 'medium') -> int:
        """Create a new recommendation for user action."""
        conn = self.get_connection()
        cur = conn.cursor()
        timestamp = datetime.now().isoformat()
        cur.execute(
            '''INSERT INTO recommendations (timestamp, event_id, category, recommendation_text, action_type, priority)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (timestamp, event_id, category, recommendation_text, action_type, priority)
        )
        conn.commit()
        rec_id = cur.lastrowid
        conn.close()
        return rec_id

    def get_pending_recommendations(self, limit=20) -> List[dict]:
        """Get all pending recommendations."""
        conn = self.get_connection()
        cur = conn.execute(
            "SELECT * FROM recommendations WHERE status = 'pending' ORDER BY id DESC LIMIT ?", 
            (limit,)
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_recommendations(self, limit=50) -> List[dict]:
        """Get all recommendations regardless of status."""
        conn = self.get_connection()
        cur = conn.execute("SELECT * FROM recommendations ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_recommendation_status(self, rec_id: int, status: str):
        """Update recommendation status (pending, applied, dismissed)."""
        conn = self.get_connection()
        timestamp = datetime.now().isoformat() if status == 'applied' else None
        conn.execute(
            "UPDATE recommendations SET status = ?, applied_at = ? WHERE id = ?",
            (status, timestamp, rec_id)
        )
        conn.commit()
        conn.close()
