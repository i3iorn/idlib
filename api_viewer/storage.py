import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List

class RequestResponseStorage:
    def __init__(self, db_path: str = "requests.db"):
        db_path = Path(db_path)
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(db_path.as_posix(), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        schema_path = Path(__file__).parent.joinpath('config', 'requests.sql')
        with self.lock, self.conn, open(schema_path) as script:
            self.conn.executescript(script.read().strip())

    def insert_request(self, method: str, url: str, headers: str = '', body: str = '', token_request_id: int = None, http_version: str = "") -> int:
        with self.lock:
            cursor = self.conn.execute(
                "INSERT INTO requests (token_request_id, method, url, headers, body, http_version) VALUES (?, ?, ?, ?, ?, ?)",
                (token_request_id, method, url, headers, body, http_version)
            )
            self.conn.commit()
            return cursor.lastrowid

    def insert_response(self, request_id: int, status_code: int, headers: str, response_time: float, body: str = '', http_version: str = "", reason_phrase: str = "") -> int:
        with self.lock:
            cursor = self.conn.execute(
                "INSERT INTO responses (request_id, response_time, status_code, headers, body, http_version, reason_phrase) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (request_id, response_time, status_code, headers, body, http_version, reason_phrase)
            )
            self.conn.commit()
            return cursor.lastrowid

    def insert_value(self, request_id: int, jsonpath: str, value: str) -> int:
        with self.lock:
            cursor = self.conn.execute(
                "INSERT INTO jsonpath_values (request_id, jsonpath, value) VALUES (?, ?, ?)",
                (request_id, jsonpath, value)
            )
            self.conn.commit()
            return cursor.lastrowid

    def fetch_all(self) -> List[Dict[str, Any]]:
        with self.lock:
            cursor = self.conn.execute("SELECT * FROM request_response ORDER BY request_timestamp DESC")
            return [dict(row) for row in cursor.fetchall()]

    def fetch_request(self, request_id: int) -> Dict[str, Any]:
        with self.lock:
            cursor = self.conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetch_response(self, request_id: int = None, response_id: int = None) -> Dict[str, Any]:
        if request_id is not None:
            column_name = "request_id"
            column_value = request_id
        elif response_id is not None:
            column_name = "id"
            column_value = response_id
        else:
            raise ValueError("Either request_id or response_id must be provided")

        with self.lock:
            cursor = self.conn.execute(f"SELECT * FROM responses WHERE {column_name} = ?", (column_value,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def close(self):
        with self.lock:
            self.conn.close()
