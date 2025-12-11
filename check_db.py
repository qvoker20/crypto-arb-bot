import sqlite3

conn = sqlite3.connect("spreads.db")
cur = conn.cursor()

cur.execute("SELECT * FROM spreads LIMIT 20")
rows = cur.fetchall()

for r in rows:
    print(r)

conn.close()
