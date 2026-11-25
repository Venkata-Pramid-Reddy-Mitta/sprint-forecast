# ADR-004: The stationarity boundary (what this repository cannot measure)

Status: accepted

## Context

The forecaster resamples past throughput to predict future throughput. That is only valid
if the future is drawn from the same distribution as the past: stationarity. Real teams
break stationarity routinely, by scaling up, losing people, changing scope, or reorganising.
A tool that hid this assumption would be dangerous precisely when a team most needs a
forecast, because a reorg is both a structural break and a moment of high scheduling anxiety.

## Decision

State the boundary openly and do not engineer around it in v1. The repository declares, in
the README's "what this cannot measure" section and here, that:

- the forecast assumes stationarity and cannot detect a structural change from throughput
  alone;
- the measured tail optimism on short history (P95 covered 90.8% against a nominal 95 on the
  synthetic study) is a property of a bootstrap, reported rather than corrected;
- the calibration numbers are a statement about the method, measured against a chosen
  ground-truth distribution, not a promise about any one real team.

## Alternatives considered

- **Add changepoint detection now.** Rejected as premature: the fixture contains no
  documented structural break to validate it against, so it would be untested complexity.
  It is the Pivot, with a concrete trigger (a real scenario where the stationary forecast is
  provably miscalibrated on a known break).

## Consequences

- A reviewer sees the limit stated before they have to find it, which is the point.
- The v2 path is already named: a changepoint test plus a trend-aware resampler, validated
  by whether calibrated coverage holds across a known break.
