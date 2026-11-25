"""Typed failures, so the CLI can map a cause to an exit code.

The whole point of the exit-code taxonomy (see ADR-003) is to separate "the tool
ran and the honest answer is no" from "the tool could not answer at all". Those two
outcomes share a shell convention of "non-zero" but mean opposite things to a CI gate,
so they are different exception types here rather than a single ValueError.
"""

from __future__ import annotations


class ForecastError(Exception):
    """Base class for every failure this package raises deliberately."""


class InvalidInput(ForecastError):
    """The caller handed in data that cannot be forecast: empty or negative
    throughput, a non-positive backlog, an all-zero history. Maps to exit code 3,
    because the tool did not answer the question, it rejected it."""


class UnboundedForecast(ForecastError):
    """The backlog cannot be burned down within the simulation cap, because the
    sampled throughput is too often zero. There is no honest date to report, so the
    tool says so rather than inventing one. Maps to exit code 3."""
