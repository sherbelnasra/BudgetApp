"""Configuration for the daily stock picker and scalping dashboard."""

from dataclasses import dataclass, field

# Curated large-cap universe (S&P 100-style). Keeps screening fast and reliable.
DEFAULT_TICKERS: list[str] = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH", "JNJ",
    "V", "XOM", "JPM", "WMT", "MA", "PG", "CVX", "HD", "MRK", "ABBV",
    "KO", "PEP", "COST", "AVGO", "LLY", "TMO", "MCD", "CSCO", "ACN", "ABT",
    "DHR", "WFC", "BAC", "DIS", "VZ", "ADBE", "CRM", "NFLX", "CMCSA", "NKE",
    "TXN", "PM", "INTC", "AMD", "QCOM", "UNP", "HON", "IBM", "AMGN", "CAT",
    "GE", "BA", "GS", "MS", "BLK", "SPGI", "AXP", "RTX", "LOW", "SBUX",
    "DE", "ISRG", "GILD", "BKNG", "MDLZ", "ADI", "TJX", "VRTX", "REGN", "LMT",
    "SYK", "MMC", "CB", "CI", "SO", "DUK", "PLD", "EQIX", "SCHW", "CME",
    "MO", "ZTS", "CL", "EOG", "SLB", "USB", "PNC", "TGT", "GM", "F",
    "PYPL", "SHOP", "SNOW", "UBER", "ABNB", "COIN", "PANW", "CRWD", "NET", "ARM",
]

MA_PERIOD = 150
MA_SLOPE_LOOKBACK = 20
MIN_HISTORY_DAYS = MA_PERIOD + MA_SLOPE_LOOKBACK + 5
DEFAULT_TOP_N = 10
MAX_PCT_ABOVE_MA = 15.0  # Avoid stocks too extended above the MA

# Scalping defaults — 5% profit target with a tighter stop for positive R:R.
SCALP_TARGET_PCT = 5.0
SCALP_STOP_PCT = 2.0
SCALP_MIN_ATR_PCT = 2.5  # Need daily ATR room so 5% is plausible
SCALP_ATR_PERIOD = 14
SCALP_RSI_PERIOD = 14
SCALP_DEFAULT_TOP_N = 15


@dataclass
class ScreenerSettings:
    tickers: list[str] = field(default_factory=lambda: DEFAULT_TICKERS.copy())
    ma_period: int = MA_PERIOD
    top_n: int = DEFAULT_TOP_N
    require_price_above_ma: bool = True
    require_rising_ma: bool = True
    max_pct_above_ma: float = MAX_PCT_ABOVE_MA
    min_avg_volume: int = 500_000


@dataclass
class ScalpSettings:
    tickers: list[str] = field(default_factory=lambda: DEFAULT_TICKERS.copy())
    top_n: int = SCALP_DEFAULT_TOP_N
    target_pct: float = SCALP_TARGET_PCT
    stop_pct: float = SCALP_STOP_PCT
    min_atr_pct: float = SCALP_MIN_ATR_PCT
    atr_period: int = SCALP_ATR_PERIOD
    rsi_period: int = SCALP_RSI_PERIOD
    min_avg_volume: int = 1_000_000
    long_only: bool = True
    require_actionable: bool = True
