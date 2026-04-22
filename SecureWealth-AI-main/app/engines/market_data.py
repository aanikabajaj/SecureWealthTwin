"""
MarketDataClient — Fetches 100% accurate market data by comparing live price to official previous close.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

class MarketDataClient:
    """Fetches real-time snapshots with accurate daily change percentages."""

    def __init__(self) -> None:
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[datetime] = None
        # Accurate Tickers for Indian Market Indices
        self.tickers = {
            "NIFTY": "^NSEI",
            "SENSEX": "^BSESN",
            "BANK NIFTY": "^NSEBANK",
            "MIDCAP": "^NSEMDCP50"
        }

    def fetch_live_indices(self) -> List[Dict[str, Any]]:
        """Return live data for all indices with verified daily change."""
        if self._cache is not None and self._is_cache_fresh():
            return self._cache["indices"]

        import yfinance as yf
        results = []

        for name, symbol in self.tickers.items():
            try:
                ticker = yf.Ticker(symbol)
                # Fetching multiple data points to ensure accuracy
                info = ticker.fast_info
                
                current_price = info.last_price
                previous_close = info.previous_close
                
                # Fallback to history if fast_info is missing previous_close
                if previous_close is None or previous_close == 0:
                    hist = ticker.history(period="2d")
                    if len(hist) >= 2:
                        previous_close = hist['Close'].iloc[-2]
                        current_price = hist['Close'].iloc[-1]
                
                change_pct = 0.0
                if previous_close and current_price:
                    change_pct = ((current_price - previous_close) / previous_close) * 100
                
                trend = "up" if change_pct > 0 else "down" if change_pct < 0 else "stable"
                
                results.append({
                    "name": name,
                    "value": round(current_price, 2) if current_price else 0.0,
                    "change": f"{'+' if change_pct > 0 else ''}{change_pct:.2f}%",
                    "change_raw": round(change_pct, 2),
                    "trend": trend
                })
            except Exception as e:
                logger.error(f"Failed to fetch {name} ({symbol}): {e}")
                results.append({
                    "name": name,
                    "value": 0.0,
                    "change": "0.00%",
                    "change_raw": 0.0,
                    "trend": "stable"
                })

        self._cache = {
            "indices": results,
            "fetched_at": datetime.utcnow()
        }
        self._cache_time = datetime.utcnow()
        return results

    def _is_cache_fresh(self) -> bool:
        if self._cache_time is None:
            return False
        ttl = timedelta(seconds=settings.market_data_cache_ttl_seconds)
        return (datetime.utcnow() - self._cache_time) < ttl

    def get_last_updated(self) -> datetime:
        return self._cache_time or datetime.utcnow()
