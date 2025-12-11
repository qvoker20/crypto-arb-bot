import aiohttp

async def get_binance_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return float(data["price"])

async def get_bybit_price(symbol):
    url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return float(data["result"]["list"][0]["lastPrice"])


async def get_okx_price(symbol):
    okx_symbol = symbol.replace("USDT", "-USDT")  # APTUSDT -> APT-USDT
    url = f"https://www.okx.com/api/v5/market/ticker?instId={okx_symbol}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

            # OKX може повернути data = []
            if "data" in data and len(data["data"]) > 0:
                return float(data["data"][0]["last"])

            return None


