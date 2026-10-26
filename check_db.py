
import sqlite3
from pathlib import Path

db_path = Path("instance") / "careerpilot.db"

if not db_path.exists():
    print("ERROR: Database file not found:", db_path)
else:
    connection = sqlite3.connect(str(db_path))

    try:
        print("Database integrity:",
              connection.execute("PRAGMA integrity_check").fetchone()[0])

        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        print("\nDatabase tables and record counts:")

        for (table_name,) in tables:
            count = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]

            print(f"{table_name}: {count} records")

    finally:
        connection.close()
