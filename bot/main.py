import asyncio
from config import SYMBOLS, THRESHOLD, FETCH_INTERVAL
from price_fetcher import get_binance_price, get_bybit_price, get_okx_price
from spread_detector import SpreadMonitor
from db import init_db, insert_spread

async def monitor():
    init_db()
    monitors = {symbol: SpreadMonitor() for symbol in SYMBOLS}

    while True:
        for symbol in SYMBOLS:
            b = await get_binance_price(symbol)
            bb = await get_bybit_price(symbol)
            ok = await get_okx_price(symbol)

            if b is None or bb is None or ok is None:
                print(f"[SKIP] No price for {symbol}")
                continue

            prices = {"binance": b, "bybit": bb, "okx": ok}


            print(f"[DATA] {symbol} → {prices}")

            ev = monitors[symbol].check(symbol, prices, THRESHOLD)

            if ev:
                if ev[0] == "start":
                    print(f"[START] {symbol} spread {ev[1]:.2f}% between {ev[2]} and {ev[3]}")
                
                elif ev[0] == "end":
                    (typ, spread_end, duration, max_spread,
                     exs, start_prices, end_prices,
                     start_t, end_t) = ev

                    data = (
                        symbol,
                        exs[0], exs[1],
                        start_prices[0], start_prices[1],
                        end_prices[0], end_prices[1],
                        THRESHOLD, spread_end, max_spread,
                        start_t.isoformat(), end_t.isoformat(),
                        duration
                    )
                    insert_spread(data)

                    print(f"[END] {symbol} max {max_spread:.2f}% duration {duration:.2f}s")

        await asyncio.sleep(FETCH_INTERVAL)

asyncio.run(monitor())
