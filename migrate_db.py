import os, shutil, sqlite3

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./domus.db").replace("sqlite:///","")
if not os.path.exists(DB_PATH):
    print(f"No DB at {DB_PATH}; nothing to migrate.")
    raise SystemExit(0)

bak = DB_PATH + ".bak"
shutil.copyfile(DB_PATH, bak)
print(f"Backup written → {bak}")

target_cols = [
    ("job_id", "TEXT PRIMARY KEY"),
    ("matter_ref", "TEXT"),
    ("council", "TEXT"),
    ("filename", "TEXT"),
    ("extracted", "TEXT"),
    ("risks", "TEXT"),
    ("received_at", "TEXT"),
]

def cols_dict(cur, table):
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1]: row for row in cur.fetchall()}

with sqlite3.connect(DB_PATH) as conn:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='convey_searches'")
    row = cur.fetchone()

    if not row:
        print("Table convey_searches does not exist — creating fresh table.")
        cols_sql = ", ".join([f"{n} {t}" for n, t in target_cols])
        cur.execute(f"CREATE TABLE convey_searches ({cols_sql})")
        conn.commit()
        print("Created convey_searches with correct schema.")
    else:
        existing = cols_dict(cur, "convey_searches")
        target_names = [n for n, _ in target_cols]
        missing = [n for n in target_names if n not in existing]
        has_job = "job_id" in existing
        job_is_pk = has_job and (existing["job_id"][5] == 1)  # PRAGMA table_info: pk flag at index 5
        needs_rebuild = (not has_job) or (not job_is_pk)

        if not needs_rebuild and not missing:
            print("Schema already compatible. No migration needed.")
        elif not needs_rebuild and missing:
            for m in missing:
                # SQLite can't add constraints via ALTER; add as plain TEXT if missing
                coltype = dict(target_cols)[m].split()[0]
                cur.execute(f"ALTER TABLE convey_searches ADD COLUMN {m} {coltype}")
                print(f"Added column: {m}")
            conn.commit()
            print("Added missing columns. Migration complete.")
        else:
            print("Rebuilding table with correct schema.")

source .venv/bin/activate
python3 -V
python3 migrate_db.py

pkill -f "uvicorn main:app" || true
python3 -m uvicorn main:app --reload --port 8000

