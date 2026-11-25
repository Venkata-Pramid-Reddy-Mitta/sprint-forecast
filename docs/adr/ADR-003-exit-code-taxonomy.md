# ADR-003: An exit-code taxonomy that separates "unsafe" from "could not answer"

Status: accepted

## Context

The CLI is meant to sit in a delivery gate, where the exit code is the part a script
actually consumes. The usual shell convention is zero for success and non-zero for failure,
which collapses two very different outcomes into one: a forecast that ran and concluded the
committed date is risky, and a tool that could not produce a forecast at all. A gate must
treat those differently. Blocking a release because the date is risky is the tool working.
Blocking a release because the tool crashed on bad input is the tool failing.

## Decision

Three codes, documented in the CLI module and the README:

- `0`: a forecast was produced and the committed date is safe (clears the confidence
  target), or a forecast was produced with no commitment to judge.
- `2`: a forecast was produced and the committed date is unsafe. The tool did its job and
  the answer is no.
- `3`: the tool could not answer: invalid input, or an unbounded forecast.

The `2` versus `3` distinction is carried in the exception types (`InvalidInput` and
`UnboundedForecast` map to `3`; a low probability on a valid forecast maps to `2`).

## Alternatives considered

- **Zero or one only.** Loses the distinction a gate needs.
- **Exit `1` for unsafe.** Avoided because `1` is what Python emits on an uncaught
  exception, so an unsafe verdict and a crash would be indistinguishable. `2` and `3` are
  chosen deliberately to sit clear of that.

## Consequences

- A CI gate can fail the build on `2`, alert on `3`, and pass on `0`, which is exactly the
  three-way decision a delivery gate wants.
- The codes are pinned by tests, so the contract cannot drift silently.
