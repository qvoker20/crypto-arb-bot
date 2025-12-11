# web/main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from web.auth import require_login, login_user, logout_user
from bot.db import verify_user, get_db
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="web/templates")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_submit(request: Request,
                       username: str = Form(...),
                       password: str = Form(...)):
    user = verify_user(username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Невірний логін або пароль"}
        )
    response = RedirectResponse("/dashboard", status_code=302)
    login_user(response, username)
    return response

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = require_login(request)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            symbol,
            exchange_low,
            exchange_high,
            price_low_start,
            price_high_start,
            price_low_end,
            price_high_end,
            max_spread,          -- ЗБЕРІГАЄТЬСЯ ЯК ВІДСОТОК (напр. 0.0228 => 0.02%)
            duration_seconds,
            start_time,
            end_time
        FROM spreads
        ORDER BY id DESC
        LIMIT 500
    """)
    rows_raw = cur.fetchall()
    conn.close()

    def fmt_ts(s):
        try:
            return datetime.fromisoformat(s).strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            return s

    def fmt_price(v):
        try:
            x = float(v)
            s = f"{x:,.4f}".replace(",", " ")
            s = s.rstrip("0").rstrip(".")
            return s
        except Exception:
            return str(v)

    def fmt_pct(v):
        # ВАЖЛИВО: НЕ множимо на 100. 0.0228 -> 0.02%
        try:
            f = float(str(v).replace("%", "").strip())
            return f"{f:.2f}%"
        except Exception:
            return str(v)

    def raw_pct(v):
        # для сорту: повертаємо числове значення у відсотках (без %), без множення
        try:
            return float(str(v).replace("%", "").strip())
        except Exception:
            return 0.0

    def fmt_duration(s):
        try:
            f = float(s)
            if f < 60:
                return f"{f:.2f} сек"
            m, sec = divmod(f, 60)
            return f"{int(m)} хв {sec:.1f} сек"
        except Exception:
            return str(s)

    rows = []
    symbols_set = set()
    for r in rows_raw:
        symbol = r[0]
        symbols_set.add(symbol)
        rows.append({
            "symbol": symbol,
            "ex_low": r[1],
            "ex_high": r[2],
            "price_low_start": fmt_price(r[3]),
            "price_high_start": fmt_price(r[4]),
            "price_low_end": fmt_price(r[5]),
            "price_high_end": fmt_price(r[6]),
            "max_spread": fmt_pct(r[7]),
            "max_spread_value": raw_pct(r[7]),  # для сортування на фронті
            "duration": fmt_duration(r[8]),
            "start_time_fmt": fmt_ts(r[9]),
            "end_time_fmt": fmt_ts(r[10]),
        })

    symbols = sorted(symbols_set)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "rows": rows,
        "symbols": symbols,
        "username": user["username"]
    })

@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    logout_user(response)
    return response