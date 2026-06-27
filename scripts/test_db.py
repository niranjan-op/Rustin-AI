"""
Developer utility: List all projects in the database.
Run from the project root: python scripts/test_db.py
"""
import sqlite3

def check_projects():
    conn = sqlite3.connect(".files/test.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, user_identifier FROM projects")
    rows = cursor.fetchall()
    print("Projects in DB:")
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    check_projects()
