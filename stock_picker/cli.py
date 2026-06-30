"""Command-line interface for daily stock picks."""

import argparse
import json
import sys

from stock_picker.config import ScreenerSettings
from stock_picker.screener import run_daily_screen


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pick stocks for today using the 150-day moving average."
    )
    parser.add_argument(
        "--top-n", type=int, default=10, help="Number of stocks to return (default: 10)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results as JSON"
    )
    parser.add_argument(
        "--allow-below-ma",
        action="store_true",
        help="Include stocks below the 150 MA (not recommended)",
    )
    parser.add_argument(
        "--no-rising-ma",
        action="store_true",
        help="Do not require the 150 MA to be rising",
    )
    args = parser.parse_args()

    settings = ScreenerSettings(
        top_n=args.top_n,
        require_price_above_ma=not args.allow_below_ma,
        require_rising_ma=not args.no_rising_ma,
    )

    result = run_daily_screen(settings)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"\nDaily Stock Picks — {result['date']}")
    print("=" * 60)
    print("Criteria: price above 150-day MA", end="")
    if settings.require_rising_ma:
        print(", 150 MA trending up", end="")
    print(f", max {settings.max_pct_above_ma}% above MA\n")

    if not result["picks"]:
        print("No stocks matched today's criteria.")
        return 1

    print(f"{'Ticker':<8} {'Price':>10} {'150 MA':>10} {'% Above':>9} {'MA Slope':>10} {'Score':>8}")
    print("-" * 60)
    for pick in result["picks"]:
        print(
            f"{pick['ticker']:<8} "
            f"${pick['price']:>9.2f} "
            f"${pick['ma_150']:>9.2f} "
            f"{pick['pct_above_ma']:>8.2f}% "
            f"{pick['ma_slope_pct']:>9.2f}% "
            f"{pick['score']:>8.2f}"
        )

    print(f"\n{result['picks_count']} pick(s) from {result['universe_size']} stocks screened.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
