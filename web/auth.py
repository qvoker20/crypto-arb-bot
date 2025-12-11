# web/auth.py
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
import sqlite3
from bot.db import get_db

SESSION_COOKIE = "arb_session"

def require_login(request: Request):
    """Перевіряє, чи користувач авторизований та повертає словник користувача."""
    session = request.cookies.get(SESSION_COOKIE)
    if not session:
        raise HTTPException(status_code=302, detail="Redirect", headers={"Location": "/login"})

    conn = get_db()
    try:
        conn.row_factory = sqlite3.Row  # дає доступ до колонок за назвами
        cur = conn.cursor()
        cur.execute("SELECT id, username, full_name, is_admin FROM users WHERE username = ?", (session,))
        row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=302, detail="Redirect", headers={"Location": "/login"})

    return dict(row)

def login_user(response, username: str):
    """Створюємо cookie для сесії."""
    response.set_cookie(
        key=SESSION_COOKIE,
        value=username,
        httponly=True,
        max_age=60 * 60 * 24 * 7  # 7 днів
    )

def logout_user(response):
    """Видаляємо cookie."""
    response.delete_cookie(SESSION_COOKIE)