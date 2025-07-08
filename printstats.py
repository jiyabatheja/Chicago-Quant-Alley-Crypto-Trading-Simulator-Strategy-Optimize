#!/usr/bin/env python3
"""
printStats.py

Analyze simulation output (timestamped PnL) and produce performance metrics and plots.

Usage:
    python printStats.py --input output/timestamped_pnl.csv --output_dir output
"""
import os
import argparse
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def compute_performance_metrics(equity_series):
    """
    Given a pandas Series of cumulative PnL (indexed by timestamp),
    compute performance metrics:
      - Mean, median, std of the equity Series
      - Daily returns and annualized Sharpe ratio
      - Maximum drawdown
      - VaR and Expected Shortfall at 95%
    Returns a dict of metrics and derived series (daily_returns, drawdown).
    """
    # Basic stats on equity
    metrics = {}
    metrics['mean_pnl'] = equity_series.mean()
    metrics['median_pnl'] = equity_series.median()
    metrics['std_pnl'] = equity_series.std()

    # Resample to end-of-day to get daily equity
    daily_equity = equity_series.resample('D').last().ffill()
    # Daily PnL changes as returns
    daily_returns = daily_equity.diff().fillna(0)

    # Sharpe ratio (annualized, assuming 252 trading days)
    mean_ret = daily_returns.mean()
    std_ret = daily_returns.std()
    sharpe = (mean_ret / std_ret * np.sqrt(252)) if std_ret != 0 else np.nan

    metrics['mean_daily_return'] = mean_ret
    metrics['std_daily_return'] = std_ret
    metrics['sharpe_ratio'] = sharpe

    # Drawdown series
    running_max = equity_series.cummax()
    drawdown = equity_series - running_max
    metrics['max_drawdown'] = drawdown.min()

    # VaR and Expected Shortfall at 95%
    var_95 = np.percentile(daily_returns, 5)
    es_95 = daily_returns[daily_returns <= var_95].mean()
    metrics['var_95'] = var_95
    metrics['es_95'] = es_95

    return metrics, daily_returns, drawdown


def plot_and_save(equity_series, drawdown_series, output_dir):
    """Generate and save two plots: cumulative PnL and drawdown."""
    os.makedirs(output_dir, exist_ok=True)

    # Cumulative PnL curve
    plt.figure()
    equity_series.plot(title='Cumulative P&L')
    plt.xlabel('Time')
    plt.ylabel('P&L')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'cumulative_pnl.png'))
    plt.close()

    # Drawdown curve
    plt.figure()
    drawdown_series.plot(title='Drawdown')
    plt.xlabel('Time')
    plt.ylabel('Drawdown')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'drawdown.png'))
    plt.close()


def main(input_path, output_dir):
    # Load data
    df = pd.read_csv(input_path)
    # Convert timestamp column
    if 'timestamp' in df.columns:
        # assume timestamp is in seconds since epoch
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    else:
        df.index = pd.to_datetime(df.index)

    df = df.set_index('timestamp')
    if 'PnL' not in df.columns:
        raise ValueError(f"Expected 'PnL' column in input CSV, found {df.columns.tolist()}")

    equity = df['PnL']

    # Compute metrics
    metrics, daily_returns, drawdown = compute_performance_metrics(equity)

    # Print metrics
    print("\nPerformance Metrics")
    print("-------------------")
    print(f"Mean P&L: {metrics['mean_pnl']:.2f}")
    print(f"Median P&L: {metrics['median_pnl']:.2f}")
    print(f"Std of P&L: {metrics['std_pnl']:.2f}\n")

    print(f"Mean daily return: {metrics['mean_daily_return']:.4f}")
    print(f"Std daily return: {metrics['std_daily_return']:.4f}")
    print(f"Annualized Sharpe Ratio: {metrics['sharpe_ratio']:.2f}\n")

    print(f"Maximum Drawdown: {metrics['max_drawdown']:.2f}")
    print(f"VaR (95%): {metrics['var_95']:.4f}")
    print(f"Expected Shortfall (95%): {metrics['es_95']:.4f}\n")

    # Plot and save
    plot_and_save(equity, drawdown, output_dir)
    print(f"Plots saved to '{output_dir}' directory.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze simulation PnL and plot results')
    parser.add_argument('--input', dest='input_path', default='output/timestamped_pnl.csv',
                        help='Path to timestamped PnL CSV')
    parser.add_argument('--output_dir', dest='output_dir', default='output',
                        help='Directory to save plots')
    args = parser.parse_args()

    main(args.input_path, args.output_dir)
