"""
Developer utility: List all registered users in the database.
Run from the project root: python scripts/test_users.py
"""
import sqlite3

def check_users():
    conn = sqlite3.connect(".files/test.db")
    cursor = conn.cursor()
    cursor.execute("SELECT identifier FROM users")
    rows = cursor.fetchall()
    print("Users in DB:")
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    check_users()
