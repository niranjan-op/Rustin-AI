import os
import sqlite3

# Resolve the absolute path of the database relative to this script's directory
db_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(db_dir)
path = os.path.join(project_root, ".files", "test.db")

# Ensure parent directory exists
os.makedirs(os.path.dirname(path), exist_ok=True)

conn = sqlite3.connect(path)
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")
QUERY = """
CREATE TABLE IF NOT EXISTS atomic_facts(
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    fact_key TEXT NOT NULL,
    fact_value TEXT NOT NULL,
    category TEXT,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
        """
cursor.execute(QUERY)
conn.commit()
conn.close()
