import os
import uuid
import mysql.connector
from mysql.connector import Error
from datetime import datetime

DB_NAME = "Optiwell"

def _base_config():
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", 3306)),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", "trinhquocviet2005"),
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
    }

def get_connection(include_db: bool = True):
    cfg = _base_config()
    if include_db:
        cfg["database"] = DB_NAME
    return mysql.connector.connect(**cfg)

def ensure_database():
    try:
        conn = get_connection(include_db=False)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.close()
        conn.close()
    except Error as e:
        raise RuntimeError(f"Failed creating database {DB_NAME}: {e}")

def init_db():
    ensure_database()
    try:
        conn = get_connection(include_db=True)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_uuid CHAR(36) NOT NULL UNIQUE,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_uuid CHAR(36) NOT NULL,
                role ENUM('patient','doctor') NOT NULL,
                content TEXT NOT NULL,
                image_path VARCHAR(255),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX (session_uuid),
                CONSTRAINT fk_session FOREIGN KEY (session_uuid) REFERENCES sessions(session_uuid)
                    ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        conn.commit()
        cur.close()
        conn.close()
    except Error as e:
        raise RuntimeError(f"Failed initializing tables: {e}")

def create_session(session_uuid: str | None = None) -> str:
    sid = session_uuid or str(uuid.uuid4())
    try:
        conn = get_connection(include_db=True)
        cur = conn.cursor()
        cur.execute("INSERT IGNORE INTO sessions (session_uuid, created_at) VALUES (%s, %s)", (sid, datetime.utcnow()))
        conn.commit()
        cur.close()
        conn.close()
        return sid
    except Error as e:
        raise RuntimeError(f"Failed creating session: {e}")

def save_message(session_uuid: str, role: str, content: str, image_path: str | None = None):
    if role not in {"patient", "doctor"}:
        raise ValueError("role must be 'patient' or 'doctor'")
    try:
        conn = get_connection(include_db=True)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (session_uuid, role, content, image_path, created_at) VALUES (%s, %s, %s, %s, %s)",
            (session_uuid, role, content, image_path, datetime.utcnow())
        )
        conn.commit()
        cur.close()
        conn.close()
    except Error as e:
        raise RuntimeError(f"Failed saving message: {e}")

def fetch_messages(session_uuid: str) -> list[tuple[str, str]]:
    """Return list of (role, content) for a session."""
    try:
        conn = get_connection(include_db=True)
        cur = conn.cursor()
        cur.execute("SELECT role, content FROM messages WHERE session_uuid=%s ORDER BY id", (session_uuid,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Error as e:
        raise RuntimeError(f"Failed fetching messages: {e}")

__all__ = [
    "init_db",
    "create_session",
    "save_message",
    "fetch_messages",
]