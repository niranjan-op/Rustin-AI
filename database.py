import os
import shutil
import sqlite3


def init_sqlite_db(db_path="test.db"):
    """
    Initialize SQLite database with Chainlit-compatible schema
    and apply required compatibility patches automatically.
    """

    print(f"Initializing database at {db_path}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # =========================================================
    # USERS
    # =========================================================
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            identifier TEXT NOT NULL,
            createdAt TEXT,
            metadata TEXT DEFAULT '{}'
        )
        """
    )

    # =========================================================
    # THREADS
    # =========================================================
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS threads (
            id TEXT PRIMARY KEY,
            name TEXT,
            createdAt TEXT,
            userId TEXT,
            userIdentifier TEXT,
            tags TEXT,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (userId) REFERENCES users(id)
        )
        """
    )

    # =========================================================
    # FEEDBACKS
    # =========================================================
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS feedbacks (
            id TEXT PRIMARY KEY,
            forId TEXT,
            value TEXT,
            comment TEXT
        )
        """
    )

    # =========================================================
    # ELEMENTS
    # =========================================================
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS elements (
            id TEXT PRIMARY KEY,
            threadId TEXT,
            type TEXT,
            chainlitKey TEXT,
            url TEXT,
            objectKey TEXT,
            name TEXT,
            display TEXT,
            size TEXT,
            language TEXT,
            page TEXT,
            forId TEXT,
            mime TEXT,
            props TEXT DEFAULT '{}',
            FOREIGN KEY (threadId)
                REFERENCES threads(id)
                ON DELETE CASCADE
        )
        """
    )

    # =========================================================
    # STEPS
    # =========================================================
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS steps (
            id TEXT PRIMARY KEY,
            threadId TEXT,
            parentId TEXT,
            name TEXT,
            type TEXT,
            input TEXT,
            output TEXT,
            isError INTEGER,
            streaming INTEGER,
            waitForAnswer INTEGER,
            showInput TEXT,
            defaultOpen INTEGER,

            -- Added patch columns directly into schema
            autoCollapse INTEGER DEFAULT 0,
            language TEXT,
            indent INTEGER,

            createdAt TEXT NOT NULL,
            start TEXT,
            end TEXT,
            metadata TEXT DEFAULT '{}',
            generation TEXT,
            tags TEXT,

            FOREIGN KEY (threadId)
                REFERENCES threads(id)
                ON DELETE CASCADE
        )
        """
    )

    conn.commit()

    # =========================================================
    # PATCH EXISTING DATABASES
    # =========================================================

    patch_steps_table(cursor)
    patch_elements_for_images(cursor)

    conn.commit()
    conn.close()

    print(f"✅ SQLite database '{db_path}' is ready.")


def patch_steps_table(cursor):
    """
    Patch older DB versions by adding missing columns.
    """

    columns_to_add = [
        ("autoCollapse", "INTEGER DEFAULT 0"),
        ("language", "TEXT"),
        ("indent", "INTEGER"),
    ]

    for col_name, col_type in columns_to_add:

        try:
            cursor.execute(
                f"""
                ALTER TABLE steps
                ADD COLUMN {col_name} {col_type}
                """
            )

            print(f"[+] Added column: {col_name}")

        except sqlite3.OperationalError:
            print(f"[*] Column '{col_name}' already exists.")


def patch_elements_for_images(cursor):
    """
    Convert element URLs to /public/ paths and copy files.
    """

    blob_dir = os.path.join(os.getcwd(), "blob")
    public_dir = os.path.join(os.getcwd(), "public")

    os.makedirs(public_dir, exist_ok=True)

    print("Patching element URLs to /public/ paths...")

    try:
        cursor.execute(
            """
            SELECT id, url, objectKey
            FROM elements
            """
        )

        rows = cursor.fetchall()

    except sqlite3.OperationalError:
        print("[!] Elements table missing.")
        return

    updates = 0

    for row_id, url, object_key in rows:

        if not object_key:
            continue

        clean_key = object_key.replace("\\", "/")

        new_url = f"/public/{clean_key}"

        # -----------------------------------------------------
        # Copy file from blob/ -> public/
        # -----------------------------------------------------

        src = os.path.join(
            blob_dir,
            *object_key.replace("/", os.sep).split(os.sep),
        )

        dst = os.path.join(
            public_dir,
            *clean_key.split("/"),
        )

        if os.path.exists(src) and not os.path.exists(dst):

            os.makedirs(os.path.dirname(dst), exist_ok=True)

            shutil.copy2(src, dst)

            print(f"  Copied: {src} -> {dst}")

        # -----------------------------------------------------
        # Update DB URL
        # -----------------------------------------------------

        if url != new_url:

            cursor.execute(
                """
                UPDATE elements
                SET url = ?
                WHERE id = ?
                """,
                (new_url, row_id),
            )

            updates += 1

    print(
        f"[SUCCESS] Patched {updates} element URLs "
        f"to /public/ paths."
    )


if __name__ == "__main__":
    init_sqlite_db()