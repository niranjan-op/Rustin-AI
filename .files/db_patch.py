import sqlite3

db_path = "test.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 1. Disable constraints and start transaction
    cursor.execute("PRAGMA foreign_keys=OFF;")
    cursor.execute("BEGIN TRANSACTION;")

    # 2. Create the new threads table including the new project_id column
    cursor.execute("""
    CREATE TABLE threads_new (
        id TEXT PRIMARY KEY,
        name TEXT,
        createdAt TEXT,
        userId TEXT,
        userIdentifier TEXT,
        tags TEXT,
        metadata TEXT DEFAULT '{}',
        project_id TEXT, -- Added new column
        FOREIGN KEY (userId) REFERENCES users(id),
        FOREIGN KEY (project_id) REFERENCES PROJECTS(id) -- Added new foreign key
    );
    """)

    # 3. Copy existing data from old table to new table
    cursor.execute("""
    INSERT INTO threads_new (id, name, createdAt, userId, userIdentifier, tags, metadata)
    SELECT id, name, createdAt, userId, userIdentifier, tags, metadata
    FROM threads;
    """)

    # 4. Swap the tables
    cursor.execute("DROP TABLE threads;")
    cursor.execute("ALTER TABLE threads_new RENAME TO threads;")

    # 5. Commit changes safely
    conn.commit()
    print("Successfully added project_id foreign key to the threads table!")

except sqlite3.Error as e:
    print(f"Migration failed: {e}")
    conn.rollback()

finally:
    # 6. Re-enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys=ON;")
    conn.close()
