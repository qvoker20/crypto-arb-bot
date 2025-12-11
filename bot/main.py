import asyncio
from datetime import datetime
from bot.db import init_db, insert_spread, log_arb_trade, get_all_signal_users
from bot.config import SYMBOLS, THRESHOLD, FETCH_INTERVAL
from bot.price_fetcher import get_binance_price, get_bybit_price, get_okx_price
from bot.spread_detector import SpreadMonitor


# ============================
#   Форматування часу
# ============================
def fmt(dt):
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime("%d.%m.%Y %H:%M:%S")


# ============================
#   ЛОГУВАННЯ
# ============================
def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


# ============================
#   Моніторинг
# ============================
async def monitor() -> None:
    from bot.telegram_bot import send_signal  # lazy import to avoid circular import

    init_db()
    log("База даних ініціалізована")

    monitors = {symbol: SpreadMonitor() for symbol in SYMBOLS}
    log(f"Створено SpreadMonitor для монет: {SYMBOLS}")

    while True:
        try:
            signal_users = get_all_signal_users()
            log(f"Користувачів з сигналами: {len(signal_users)} → {signal_users}")

            for symbol in SYMBOLS:
                try:
                    log(f"--- Перевірка монети: {symbol} ---")

                    # ціни
                    b = await get_binance_price(symbol)
                    bb = await get_bybit_price(symbol)
                    ok = await get_okx_price(symbol)

                    log(f"Ціни: Binance={b}, Bybit={bb}, OKX={ok}")

                    if b is None or bb is None or ok is None:
                        log(f"[SKIP] Немає ціни для {symbol}")
                        continue

                    prices = {"binance": b, "bybit": bb, "okx": ok}

                    ev = monitors[symbol].check(symbol, prices, THRESHOLD)
                    log(f"Результат SpreadMonitor: {ev}")

                    # =====================================
                    #              START
                    # =====================================
                    if ev and ev[0] == "start":
                        (
                            _,
                            spread_start,
                            low_ex, high_ex,
                            low_price, high_price,
                            start_time
                        ) = ev

                        log(
                            f"[START] {symbol}: спред={spread_start:.4f}% "
                            f"{low_ex}({low_price}) → {high_ex}({high_price})"
                        )

                        msg = (
                            f"🚨 *АРБІТРАЖ ВІДКРИТО*\n"
                            f"Монета: *{symbol}*\n"
                            f"Спред: *{spread_start:.2f}%*\n\n"
                            f"Біржі: *{low_ex.upper()} → {high_ex.upper()}*\n\n"
                            f"Ціни:\n"
                            f"• Купівля: `{low_price}`\n"
                            f"• Продаж: `{high_price}`\n\n"
                            f"Старт: `{fmt(start_time)}`"
                        )

                        for uid in signal_users:
                            log(f"Надсилаю START сигнал {uid}")
                            await send_signal(uid, msg)

                    # =====================================
                    #              END
                    # =====================================
                    elif ev and ev[0] == "end":
                        (
                            _,
                            spread_end,
                            duration,
                            max_spread,
                            exs,
                            start_prices,
                            end_prices,
                            start_t,
                            end_t
                        ) = ev

                        log(
                            f"[END] {symbol}: тривалість={duration:.2f} сек "
                            f"макс={max_spread:.4f}%"
                        )

                        msg = (
                            f"✅ *АРБІТРАЖ ЗАКРИТО*\n"
                            f"Монета: *{symbol}*\n\n"
                            f"⏱ Тривалість: *{duration:.2f} сек*\n"
                            f"📈 Макс. спред: *{max_spread:.2f}%*\n\n"
                            f"Період:\n"
                            f"• Старт: `{fmt(start_t)}`\n"
                            f"• Кінець: `{fmt(end_t)}`"
                        )

                        for uid in signal_users:
                            log(f"Надсилаю END сигнал {uid}")
                            await send_signal(uid, msg)

                        # запис у spreads
                        insert_spread((
                            symbol,
                            exs[0], exs[1],
                            start_prices[0], start_prices[1],
                            end_prices[0], end_prices[1],
                            THRESHOLD, spread_end, max_spread,
                            start_t.isoformat(), end_t.isoformat(),
                            duration
                        ))
                        log("Запис у spreads OK")

                        # запис у arb_trades
                        log_arb_trade(
                            exs[0],
                            exs[1],
                            symbol,
                            0,
                            start_prices[0],
                            end_prices[1],
                            0,
                            max_spread,
                            max_spread,
                            start_t.isoformat(),
                            end_t.isoformat()
                        )
                        log("Запис у arb_trades OK")

                except Exception as e:
                    log(f"[ERROR] помилка монети {symbol}: {e}")

        except Exception as e:
            log(f"[CRITICAL] помилка в циклі моніторингу: {e}")

        await asyncio.sleep(FETCH_INTERVAL)
        log("Цикл моніторингу → пауза...")


# ============================
#   MAIN
# ============================
async def main():
    from bot.telegram_bot import run_telegram  # lazy import

    task1 = asyncio.create_task(run_telegram())
    task2 = asyncio.create_task(monitor())

    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    asyncio.run(main())
