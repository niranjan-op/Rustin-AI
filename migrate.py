import sqlite3

def migrate_projects():
    conn = sqlite3.connect(".files/test.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE projects SET user_identifier = '1' WHERE user_identifier IS NULL")
    conn.commit()
    print(f"Updated {cursor.rowcount} projects to belong to user '1'.")
    conn.close()

if __name__ == "__main__":
    migrate_projects()
