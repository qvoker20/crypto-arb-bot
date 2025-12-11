import sqlite3
import bcrypt

def get_db():
    conn = sqlite3.connect("spreads.db", check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # таблиця spreads (вже існує)
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
        duration_seconds REAL
    )
    """)

    # 🔥 таблиця users — нова
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        telegram_id TEXT,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

        # таблиця portfolio_state — поточний баланс користувача
    cur.execute("""
    CREATE TABLE IF NOT EXISTS portfolio_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        exchange TEXT NOT NULL,      -- Bybit, OKX, Binance
        asset TEXT NOT NULL,         -- USDT або монета (APT, SOL, TON...)
        amount REAL NOT NULL,        -- кількість активу
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # таблиця arb_trades — всі арбітражні цикли
    cur.execute("""
    CREATE TABLE IF NOT EXISTS arb_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        start_exchange TEXT NOT NULL,
        end_exchange TEXT NOT NULL,

        buy_asset TEXT NOT NULL,
        sell_asset TEXT NOT NULL,

        amount REAL NOT NULL,
        buy_price REAL NOT NULL,
        sell_price REAL NOT NULL,

        fees REAL NOT NULL,
        profit_usdt REAL NOT NULL,
        profit_percent REAL NOT NULL,

        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

def insert_spread(data):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO spreads (
        symbol,
        exchange_low,
        exchange_high,
        price_low_start,
        price_high_start,
        price_low_end,
        price_high_end,
        spread_start,
        spread_end,
        max_spread,
        start_time,
        end_time,
        duration_seconds
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_user(full_name: str, username: str, password: str, telegram_id=None, is_admin=0):
    conn = get_db()
    cur = conn.cursor()

    password_hash = hash_password(password)

    cur.execute("""
    INSERT INTO users (full_name, username, password_hash, telegram_id, is_admin)
    VALUES (?, ?, ?, ?, ?)
    """, (full_name, username, password_hash, telegram_id, is_admin))

    conn.commit()
    conn.close()

def get_user_by_username(username: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()

    conn.close()
    return row

def verify_user(username: str, password: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, full_name, username, password_hash, telegram_id, is_admin FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    stored_hash = row[3]

    if bcrypt.checkpw(password.encode(), stored_hash.encode()):
        return {
            "id": row[0],
            "full_name": row[1],
            "username": row[2],
            "telegram_id": row[4],
            "is_admin": row[5]
        }

    return None

def get_user_by_telegram_id(tg_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, full_name, username, is_admin FROM users WHERE telegram_id = ?", (str(tg_id),))
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "full_name": row[1],
            "username": row[2],
            "is_admin": row[3]
        }

    return None

# ============================
#     PORTFOLIO STATE
# ============================

def set_portfolio_state(exchange: str, asset: str, amount: float):
    conn = get_db()
    cur = conn.cursor()

    # запис завжди один — id = 1
    cur.execute("""
    INSERT INTO portfolio_state (id, exchange, asset, amount)
    VALUES (1, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        exchange = excluded.exchange,
        asset = excluded.asset,
        amount = excluded.amount,
        updated_at = CURRENT_TIMESTAMP;
    """, (exchange, asset, amount))

    conn.commit()
    conn.close()


def get_portfolio_state():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT exchange, asset, amount, updated_at FROM portfolio_state WHERE id = 1;")
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "exchange": row[0],
        "asset": row[1],
        "amount": row[2],
        "updated_at": row[3]
    }

# ============================
#     ARBITRAGE TRADES LOG
# ============================

def log_arb_trade(start_exchange, end_exchange, symbol, amount, buy_price, sell_price,
                  fees, profit_usdt, profit_percent, start_time, end_time):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO arb_trades (
        start_exchange, end_exchange, 
        buy_asset, sell_asset,
        amount, buy_price, sell_price,
        fees, profit_usdt, profit_percent,
        start_time, end_time
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        start_exchange,
        end_exchange,
        symbol, symbol,
        amount,
        buy_price,
        sell_price,
        fees,
        profit_usdt,
        profit_percent,
        start_time,
        end_time,
    ))

    conn.commit()
    conn.close()


def get_all_signal_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL")
    rows = cur.fetchall()
    conn.close()
    return [int(r[0]) for r in rows]
