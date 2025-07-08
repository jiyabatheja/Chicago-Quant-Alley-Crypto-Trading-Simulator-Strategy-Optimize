import os
import pandas as pd
import config
from Strategy import Strategy
class Simulator:
    def __init__(self):
        self.df = None
        self.currentPrice = {}
        self.strategy = Strategy(self)
        self.buyValue = {}
        self.sellValue = {}
        self.currQuantity = {}
        self.pnl_log = []
    def readData(self):
        data_frames = []
        dates = pd.date_range(config.startDate, config.endDate).strftime('%Y%m%d')

        for date in dates:
            folder = os.path.join('data', date)
            for symbol in config.symbols:
                file_path = os.path.join(folder, f"MARK:{symbol}.csv")
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    df["Symbol"] = symbol
                    data_frames.append(df)

        self.df = pd.concat(data_frames) if data_frames else pd.DataFrame()
        self.df = self.df.sort_values(by="timestamp")
        print(f"[INFO] Loaded data shape: {self.df.shape}")
    def startSimulation(self):
        for _, row in self.df.iterrows():
            symbol = row["Symbol"]
            price = row["close"]
            self.currentPrice[symbol] = price
            self.strategy.onMarketData(row)
            total_pnl = 0
            for sym in config.symbols:
                buy = self.buyValue.get(sym, 0)
                sell = self.sellValue.get(sym, 0)
                qty = self.currQuantity.get(sym, 0)
                last_price = self.currentPrice.get(sym, 0)
                total_pnl += sell - buy + qty * last_price
            self.pnl_log.append([row["timestamp"], total_pnl])
        os.makedirs("output", exist_ok=True)
        pd.DataFrame(self.pnl_log, columns=["timestamp", "PnL"]).to_csv("output/timestamped_pnl.csv", index=False)
        print("[INFO] Saved output/timestamped_pnl.csv")
    def onOrder(self, symbol, side, quantity, price):
        slippage = 0.0001
        if side == "buy":
            trade_price = price * (1 + slippage)
            self.currQuantity[symbol] = self.currQuantity.get(symbol, 0) + quantity
            self.buyValue[symbol] = self.buyValue.get(symbol, 0) + trade_price * quantity
        else:
            trade_price = price * (1 - slippage)
            self.currQuantity[symbol] = self.currQuantity.get(symbol, 0) - quantity
            self.sellValue[symbol] = self.sellValue.get(symbol, 0) + trade_price * quantity
        print(f"[TRADE] {side.upper()} {symbol} @ {trade_price:.2f} x {quantity}")
        self.strategy.onTradeConfirmation(symbol, side, quantity, trade_price)
    def printPnL(self):
        total_pnl = 0
        for symbol in config.symbols:
            buy = self.buyValue.get(symbol, 0)
            sell = self.sellValue.get(symbol, 0)
            qty = self.currQuantity.get(symbol, 0)
            last_price = self.currentPrice.get(symbol, 0)
            pnl = sell - buy + qty * last_price
            total_pnl += pnl
        print(f"Buy Value: {self.buyValue}")
        print(f"Sell Value: {self.sellValue}")
        print(f"Current Quantity: {self.currQuantity}")
        print(f"Total PnL: {total_pnl}")
if __name__ == "__main__":
    sim = Simulator()
    sim.readData()
    sim.startSimulation()
    sim.printPnL()
