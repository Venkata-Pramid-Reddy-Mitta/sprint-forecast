# ADR-001: Resample observed throughput rather than fit a parametric distribution

Status: accepted

## Context

To forecast completion we need a distribution of future per-sprint throughput. Two families
are available: fit a parametric model (Poisson, negative binomial, a fitted gamma) to the
history and sample from it, or resample the observed history directly (a bootstrap).

The candidate's background is delivery analytics, not statistics. A choice that a delivery
lead can explain and defend in a stakeholder room is worth more here than a marginally
tighter fit that rests on an assumed functional form.

## Decision

Resample the observed history with replacement. Each simulated sprint is a value the team
actually recorded. No distribution is fitted and no shape is assumed.

## Alternatives considered

- **Fit a negative binomial.** Captures overdispersion and could extrapolate a tail beyond
  the observed values. Rejected as the default because it assumes a shape the data may not
  have, and because the failure it would hide (a bad fit on a bimodal or trending team) is
  harder to see than the failure the bootstrap wears openly.
- **Fit then widen the tail.** Adds a correction factor whose size is itself unverified.

## Consequences

- The method is honest about its own weakness: a bootstrap cannot produce a value the team
  has never recorded, so it under-covers an unobserved tail on a short history. This is not
  papered over; it is measured (calibration experiment) and published (README, ADR-004).
- The forecast is only as good as the history is representative, which is the right thing
  for the tool to be sensitive to.
- The parametric route is the natural v2 for genuinely non-stationary teams (ADR-004, the
  Pivot).
