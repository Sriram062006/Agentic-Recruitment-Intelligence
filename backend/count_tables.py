import sqlite3

conn = sqlite3.connect("data/recruitment.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
for t in tables:
    c.execute(f"SELECT count(*) FROM {t}")
    print(f"{t}: {c.fetchone()[0]}")
