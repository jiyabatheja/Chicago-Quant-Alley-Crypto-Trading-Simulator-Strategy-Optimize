# Strategy.py

from datetime import datetime
import config
import re

class Strategy:
    def __init__(self, simulator):
        self.simulator = simulator
        self.entry_price = None
        self.call_strike = None
        self.put_strike = None
        self.in_position = False
        self.pnl = 0

    def onMarketData(self, row):
        time = row["timestamp"]
        symbol = row["Symbol"]
        price = row["close"]
        dt = datetime.fromtimestamp(time)

        if not self.in_position and "BTCUSDT" in symbol:
            print(f"[DEBUG] Checking timestamp: {dt} for symbol: {symbol}")

            if dt.hour == 13 and dt.minute == 0:
                self.entry_price = price
                atm_strike = round(price / 1000) * 1000

                # Extract all expiry dates from config.symbols
                expiries = set()
                for sym in config.symbols:
                    match = re.search(r'C-BTC-\d+-(\d+)', sym)
                    if match:
                        expiries.add(match.group(1))

                if not expiries:
                    print("[ERROR] No expiry found in config.symbols!")
                    return

                expiry = sorted(expiries)[0]  # pick earliest expiry
                self.call_strike = f"C-BTC-{atm_strike}-{expiry}"
                self.put_strike = f"P-BTC-{atm_strike}-{expiry}"

                print(f"[DEBUG] Attempting strikes: {self.call_strike}, {self.put_strike}")
                print(f"[DEBUG] Available symbols: {config.symbols}")

                if self.call_strike in config.symbols and self.put_strike in config.symbols:
                    self.simulator.onOrder(self.call_strike, "sell", 0.1, self.simulator.currentPrice.get(self.call_strike, price))
                    self.simulator.onOrder(self.put_strike, "sell", 0.1, self.simulator.currentPrice.get(self.put_strike, price))
                    self.in_position = True
                    print(f"[DEBUG] Straddle entered at {dt}")
                else:
                    print("[WARNING] Strikes not in config.symbols. No trade placed.")

        if self.in_position:
            fut_price = self.simulator.currentPrice.get("BTCUSDT", 0)
            if abs(fut_price - self.entry_price) / self.entry_price > 0.01 or self.pnl >= 500 or self.pnl <= -500:
                self.simulator.onOrder(self.call_strike, "buy", 0.1, self.simulator.currentPrice.get(self.call_strike, price))
                self.simulator.onOrder(self.put_strike, "buy", 0.1, self.simulator.currentPrice.get(self.put_strike, price))
                self.in_position = False
                print(f"[DEBUG] Straddle exited at {dt}")

    def onTradeConfirmation(self, symbol, side, quantity, price):
        value = quantity * price
        if side == "buy":
            self.pnl -= value
        else:
            self.pnl += value
