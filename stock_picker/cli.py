"""Command-line interface for scalp entries and daily MA picks."""

import argparse
import json
import sys

from stock_picker.config import ScalpSettings, ScreenerSettings
from stock_picker.scalper import run_scalp_screen
from stock_picker.screener import run_daily_screen


def _print_scalps(result: dict, settings: ScalpSettings) -> int:
    print(f"\nScalp Entries (+{settings.target_pct:.0f}% target) — {result['date']}")
    print("=" * 88)
    print(
        f"Criteria: min ATR {settings.min_atr_pct}%, "
        f"stop {settings.stop_pct}%, "
        f"{'long-only' if settings.long_only else 'long+short'}\n"
    )

    if not result["entries"]:
        print("No scalp setups matched today's criteria.")
        return 1

    header = (
        f"{'Ticker':<7} {'Bias':<6} {'Setup':<22} {'Entry':>9} "
        f"{'Target':>9} {'Stop':>9} {'ATR%':>6} {'R:R':>5} {'Score':>6}"
    )
    print(header)
    print("-" * 88)
    for e in result["entries"]:
        print(
            f"{e['ticker']:<7} "
            f"{e['bias']:<6} "
            f"{e['setup']:<22} "
            f"${e['entry']:>8.2f} "
            f"${e['target']:>8.2f} "
            f"${e['stop']:>8.2f} "
            f"{e['atr_pct']:>5.2f}% "
            f"{e['risk_reward']:>5.2f} "
            f"{e['score']:>6.2f}"
        )

    print(f"\n{result['entries_count']} entr(y/ies) from {result['universe_size']} stocks screened.")
    return 0


def _print_ma(result: dict, settings: ScreenerSettings) -> int:
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stock scalping entries (5% target) and 150-MA daily picks."
    )
    parser.add_argument(
        "--mode",
        choices=["scalp", "ma"],
        default="scalp",
        help="Screen mode: scalp (default) or ma",
    )
    parser.add_argument(
        "--top-n", type=int, default=None, help="Number of results to return"
    )
    parser.add_argument(
        "--target-pct", type=float, default=5.0, help="Scalp profit target %% (default: 5)"
    )
    parser.add_argument(
        "--stop-pct", type=float, default=2.0, help="Scalp stop loss %% (default: 2)"
    )
    parser.add_argument(
        "--min-atr-pct", type=float, default=2.5, help="Minimum ATR %% for scalp mode"
    )
    parser.add_argument(
        "--allow-short", action="store_true", help="Include short scalp setups"
    )
    parser.add_argument(
        "--include-watchlist",
        action="store_true",
        help="Include weak/watchlist scalp setups",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--allow-below-ma",
        action="store_true",
        help="MA mode: include stocks below the 150 MA",
    )
    parser.add_argument(
        "--no-rising-ma",
        action="store_true",
        help="MA mode: do not require rising 150 MA",
    )
    args = parser.parse_args()

    if args.mode == "scalp":
        settings = ScalpSettings(
            top_n=args.top_n or 15,
            target_pct=args.target_pct,
            stop_pct=args.stop_pct,
            min_atr_pct=args.min_atr_pct,
            long_only=not args.allow_short,
            require_actionable=not args.include_watchlist,
        )
        result = run_scalp_screen(settings)
        if args.json:
            print(json.dumps(result, indent=2))
            return 0
        return _print_scalps(result, settings)

    settings = ScreenerSettings(
        top_n=args.top_n or 10,
        require_price_above_ma=not args.allow_below_ma,
        require_rising_ma=not args.no_rising_ma,
    )
    result = run_daily_screen(settings)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    return _print_ma(result, settings)


if __name__ == "__main__":
    sys.exit(main())
