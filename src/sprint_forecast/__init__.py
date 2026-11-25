"""sprint-forecast: price a committed delivery date as a probability, not a promise.

The public surface is small on purpose: build a Forecast from a throughput history and a
backlog, and read its percentiles and its probability of meeting a committed date off it.
"""

from __future__ import annotations

from .config import ForecastConfig
from .errors import ForecastError, InvalidInput, UnboundedForecast
from .forecast import Forecast, forecast
from .throughput import ThroughputHistory, validate_backlog, validate_history

__all__ = [
    "ForecastConfig",
    "ForecastError",
    "InvalidInput",
    "UnboundedForecast",
    "Forecast",
    "forecast",
    "ThroughputHistory",
    "validate_backlog",
    "validate_history",
]

__version__ = "0.3.0"
