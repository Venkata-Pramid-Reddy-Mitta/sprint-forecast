"""The report layer owns dates and the HTML, including the badge CSS collision guard."""

from __future__ import annotations

import re

from sprint_forecast.config import ForecastConfig
from sprint_forecast.forecast import forecast
from sprint_forecast.report import (
    BADGE_CLASSES,
    STYLE,
    completion_date,
    forecast_to_dict,
    render_html,
    render_text,
)

FC = forecast([8, 5, 9, 7, 6, 10, 4, 8], 60, ForecastConfig(trials=500), committed_sprints=7)


def test_completion_date_adds_sprint_days_per_sprint():
    assert completion_date("2026-01-06", 3, 14) == "2026-02-17"


def test_forecast_to_dict_is_json_serialisable_and_carries_dates():
    import json

    d = forecast_to_dict(FC, "demo", "2026-01-06", 14)
    json.dumps(d)  # must not raise
    assert d["name"] == "demo"
    assert d["percentile_dates"]["85"] is not None
    assert d["committed_date"] is not None


def test_render_text_leads_with_the_percentile_table_and_states_the_verdict():
    text = render_text(FC, "demo", "2026-01-06", 14)
    assert "percentile" in text
    assert "P50" in text
    assert "verdict" in text


def test_render_text_marks_a_below_p50_commitment_as_a_coin_flip():
    text = render_text(FC, "demo", "2026-01-06", 14)
    assert "coin flip" in text


def test_render_html_has_one_data_row_per_record_plus_the_header():
    one = render_html([(FC, "demo", "2026-01-06", 14)])
    two = render_html([(FC, "a", "2026-01-06", 14), (FC, "b", "2026-01-06", 14)])
    assert "UNSAFE" in one
    assert one.count("<tr>") == 2  # header plus one data row
    assert two.count("<tr>") == 3  # header plus two data rows


def test_every_css_class_used_in_the_markup_has_a_rule_in_the_stylesheet():
    """Guards the real failure mode from an earlier project: a badge class that has no
    rule renders invisibly. Every class the HTML emits must be declared in STYLE."""
    html = render_html([(FC, "demo", "2026-01-06", 14)])
    used = set(re.findall(r'class="([^"]+)"', html))
    classes = {c for group in used for c in group.split()}
    for cls in classes:
        assert f".{cls}" in STYLE, f"class {cls} used in markup but absent from STYLE"


def test_all_declared_badge_classes_are_present_in_the_stylesheet():
    for cls in BADGE_CLASSES:
        assert f".{cls}" in STYLE


def test_a_forecast_with_no_commitment_renders_a_no_commit_badge():
    fc = forecast([8, 5, 9, 7, 6], 50, ForecastConfig(trials=400))
    html = render_html([(fc, "nocommit", "2026-01-06", 14)])
    assert "NO COMMIT" in html


def test_render_text_prints_unbounded_for_a_percentile_that_was_not_reached():
    """A percentile can be unbounded even when the forecast as a whole is bounded, so
    the text report must say so rather than print a blank or a fake sprint number."""
    from sprint_forecast.forecast import Forecast

    fc = Forecast(
        n_history=5, mean_throughput=4.0, backlog=50.0, trials=100, naive_sprints=13,
        cap_sprints=130, not_reached_fraction=0.03,
        percentile_sprints={50: 13, 85: None}, histogram={13: 97},
        committed_sprints=None, prob_meet_committed=None, confidence_target=0.85,
    )
    text = render_text(fc, "edge", "2026-01-06", 14)
    assert "unbounded" in text
