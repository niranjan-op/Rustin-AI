import sqlite3
conn = sqlite3.connect('.files/test.db')
cursor = conn.cursor()
cursor.execute("SELECT id, project_id, createdAt FROM threads ORDER BY createdAt DESC LIMIT 10")
print("Latest Threads:")
for row in cursor.fetchall():
    print(row)
