"""Every bad input must be refused here, at the boundary, with a typed error."""

from __future__ import annotations

import math
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from sprint_forecast.errors import InvalidInput
from sprint_forecast.throughput import (
    ThroughputHistory,
    validate_backlog,
    validate_history,
)


def test_a_clean_history_is_accepted_and_summarised():
    h = validate_history([8, 5, 9, 7, 6])
    assert h.n == 5
    assert math.isclose(h.mean, 7.0)
    assert h.nonzero_count == 5


def test_a_history_with_a_zero_sprint_keeps_the_zero_but_counts_nonzero():
    h = validate_history([8, 0, 9])
    assert h.n == 3
    assert h.nonzero_count == 2


def test_as_array_returns_a_float_numpy_array():
    arr = validate_history([1, 2, 3]).as_array()
    assert isinstance(arr, np.ndarray)
    assert arr.dtype == float


def test_a_tuple_input_is_accepted_like_a_list():
    assert validate_history((4, 4, 4)).mean == 4.0


def test_an_empty_history_is_rejected():
    with pytest.raises(InvalidInput, match="empty"):
        validate_history([])


@pytest.mark.parametrize("bad", ["8 5 9", b"859"])
def test_a_string_or_bytes_history_is_rejected_not_iterated_char_by_char(bad):
    with pytest.raises(InvalidInput, match="sequence"):
        validate_history(bad)


def test_a_non_iterable_history_is_rejected():
    with pytest.raises(InvalidInput, match="sequence"):
        validate_history(42)


def test_a_negative_throughput_is_rejected():
    with pytest.raises(InvalidInput, match="negative"):
        validate_history([5, -1, 5])


def test_a_non_finite_throughput_is_rejected():
    with pytest.raises(InvalidInput, match="finite"):
        validate_history([5, float("inf"), 5])


def test_a_boolean_throughput_is_rejected_even_though_bool_is_an_int():
    with pytest.raises(InvalidInput, match="not a number"):
        validate_history([5, True, 5])


def test_a_non_numeric_throughput_is_rejected():
    with pytest.raises(InvalidInput, match="not a number"):
        validate_history([5, "x", 5])


def test_an_all_zero_history_is_rejected_because_nothing_ever_completes():
    with pytest.raises(InvalidInput, match="zero"):
        validate_history([0, 0, 0])


def test_the_throughput_history_is_frozen():
    h = ThroughputHistory(values=(1.0, 2.0))
    with pytest.raises(FrozenInstanceError):
        h.values = (3.0,)  # type: ignore[misc]


def test_a_positive_backlog_is_accepted():
    assert validate_backlog(60) == 60.0


@pytest.mark.parametrize("bad", [0, -5])
def test_a_non_positive_backlog_is_rejected(bad):
    with pytest.raises(InvalidInput, match="positive"):
        validate_backlog(bad)


def test_a_boolean_backlog_is_rejected():
    with pytest.raises(InvalidInput, match="number"):
        validate_backlog(True)


def test_a_non_finite_backlog_is_rejected():
    with pytest.raises(InvalidInput, match="finite"):
        validate_backlog(float("nan"))


def test_a_non_numeric_backlog_is_rejected():
    with pytest.raises(InvalidInput, match="number"):
        validate_backlog("sixty")
