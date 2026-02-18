import sqlite3
import numpy as np
import os


class State:
    def __init__(self, db_path=None):
        if db_path is None:
            state_dir = os.environ.get("STATE_DIR", "")
            if state_dir:
                os.makedirs(state_dir, exist_ok=True)
                db_path = os.path.join(state_dir, "state.db")
            else:
                db_path = "state.db"
        self.db_path = db_path
        self._setup_database()

    def _get_connection(self):
        # sqlite3.connect creates the file if it doesn't exist
        return sqlite3.connect(self.db_path)

    def _setup_database(self):
        """Initializes tables in the local SQLite file."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table for patient admission status and sex
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    mrn TEXT PRIMARY KEY,
                    sex INTEGER,
                    is_admitted INTEGER DEFAULT 1,
                    paged INTEGER DEFAULT 0
                )
            """)
            # Table for lab results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lab_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mrn TEXT,
                    value REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (mrn) REFERENCES patients(mrn)
                )
            """)
            # Table for message tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_id TEXT PRIMARY KEY
                )
            """)
            conn.commit()

    def is_processed(self, message_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM processed_messages WHERE message_id = ?", (message_id,))
            return cursor.fetchone() is not None

    def mark_processed(self, message_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO processed_messages (message_id) VALUES (?)", (message_id,))
            conn.commit()

    def admit(self, mrn, sex_str):
        sex = 0 if sex_str == "F" else 1
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # SQLite 'REPLACE' or 'INSERT OR REPLACE' handles the update logic
            cursor.execute("""
                INSERT INTO patients (mrn, sex, is_admitted, paged) 
                VALUES (?, ?, 1, 0)
                ON CONFLICT(mrn) DO UPDATE SET is_admitted=1, paged=0
            """, (mrn, sex))
            conn.commit()

    def discharge(self, mrn):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE patients SET is_admitted = 0 WHERE mrn = ?", (mrn,))
            conn.commit()

    def has_patient(self, mrn):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_admitted FROM patients WHERE mrn = ?", (mrn,))
            result = cursor.fetchone()
            return result is not None and result[0] == 1

    def add_creatinine(self, mrn, value):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO lab_results (mrn, value) VALUES (?, ?)", (mrn, value))
            conn.commit()

    def get_lab_history(self, mrn):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row  # Allows accessing columns by name
            cursor = conn.cursor()

            cursor.execute("SELECT sex FROM patients WHERE mrn = ?", (mrn,))
            patient = cursor.fetchone()

            cursor.execute("SELECT value FROM lab_results WHERE mrn = ?", (mrn,))
            rows = cursor.fetchall()

        if not rows or not patient:
            return None

        results = [r['value'] for r in rows]
        return {
            "sex": patient['sex'],
            "min": min(results),
            "max": max(results),
            "mean": np.mean(results),
            "median": np.median(results),
            "std": np.std(results),
            "results": results
        }

    def paged_patient(self, mrn):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE patients SET paged = 1 WHERE mrn = ?", (mrn,))
            conn.commit()

    def has_paged_patient(self, mrn):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT paged FROM patients WHERE mrn = ?", (mrn,))
            result = cursor.fetchone()
            return result is not None and result[0] == 1