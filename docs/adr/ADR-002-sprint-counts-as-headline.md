# ADR-002: Report sprint counts as the headline and derive dates

Status: accepted

## Context

A forecast can be expressed as a number of sprints or as a calendar date. Dates are what a
stakeholder wants to hear. But a date depends on sprint length, a start date, and a calendar
that the forecasting code does not own, while a sprint count is a pure property of the
throughput distribution and the backlog.

## Decision

The engine computes and stores sprint counts. The report layer, and only the report layer,
turns a sprint count into a date given a start date and a sprint length supplied by the
caller. Every headline figure in the README and the defense guide is a count or a ratio,
never a bare date.

## Alternatives considered

- **Forecast dates end to end.** Simpler for the reader, but it bakes calendar assumptions
  into the engine and into every published number, so a figure could change because someone
  changed the sprint length, not because the code or the data changed.

## Consequences

- Published figures are machine independent and reproduce exactly across runs and machines,
  which is what lets `check_numbers.py` guard them.
- The CLI still prints dates, because that is what a human reads; they are clearly derived.
- A reader who wants a date supplies the two inputs a date actually needs, and sees that
  they are inputs, not forecasts.
