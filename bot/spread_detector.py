from datetime import datetime

class SpreadMonitor:
    def __init__(self):
        self.active = False
        self.start_time = None
        self.max_spread = 0
        self.start_prices = None
        self.start_exchanges = None

    def check(self, symbol, prices, threshold):
        # prices = {"binance": price, "bybit": price, "okx": price}
        
        exchanges = list(prices.keys())
        vals = list(prices.values())

        max_ex = exchanges[vals.index(max(vals))]
        min_ex = exchanges[vals.index(min(vals))]

        max_p = max(vals)
        min_p = min(vals)

        spread = ((max_p - min_p) / min_p) * 100

        # Старт
        if not self.active and spread >= threshold:
            self.active = True
            self.start_time = datetime.now()
            self.max_spread = spread
            self.start_prices = (min_p, max_p)
            self.start_exchanges = (min_ex, max_ex)

            return ("start", spread, min_ex, max_ex, min_p, max_p, self.start_time)

        # Триває
        if self.active:
            self.max_spread = max(self.max_spread, spread)

            # Якщо спред впав нижче порогу → кінець
            if spread < threshold:
                end_time = datetime.now()
                duration = (end_time - self.start_time).total_seconds()

                self.active = False

                return (
                    "end",
                    spread,
                    duration,
                    self.max_spread,
                    self.start_exchanges,
                    self.start_prices,
                    (min_p, max_p),
                    self.start_time,
                    end_time
                )

        return None
