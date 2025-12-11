import sqlite3

def get_db():
    conn = sqlite3.connect("spreads.db", check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS spreads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        exchange_low TEXT,
        exchange_high TEXT,
        price_low_start REAL,
        price_high_start REAL,
        price_low_end REAL,
        price_high_end REAL,
        spread_start REAL,
        spread_end REAL,
        max_spread REAL,
        start_time TEXT,
        end_time TEXT,
        duration_seconds INTEGER
    )
    """)
    conn.commit()
    conn.close()

def insert_spread(data):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO spreads (
        symbol, exchange_low, exchange_high,
        price_low_start, price_high_start,
        price_low_end, price_high_end,
        spread_start, spread_end, max_spread,
        start_time, end_time, duration_seconds
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

    conn.commit()
    conn.close()
