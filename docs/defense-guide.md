# Defense guide: sprint-forecast

How to talk about this repository in an interview without overclaiming. Every number here
is guarded by `tools/check_numbers.py`, so this document cannot drift from the code.

## The 30 second version

"A committed delivery date is a point, and a point has no probability. sprint-forecast
resamples a team's own past throughput to build a distribution of completion dates, and
reads the committed date off it as a probability. On a mixed fixture, 4 of 12 committed
dates were below P50, a coin flip or worse. And it grades itself: against synthetic teams
with a known distribution, its P95 covered 90.8%, not 95, so it reports its own tail as
slightly optimistic rather than pretending otherwise."

Then stop. The question that usually comes next is "how is that different from just taking
an average velocity", which is the opening for claim 1.

## The claims, and how each is proved

### Claim 1: a committed date can be priced as a probability

- Proof: `sprint-forecast forecast --history "7 12 3 9 5 11 4 8 6 10" --backlog 70 --committed 7`
  returns a 14 percent probability and exit code 2.
- The number: across the fixture, 4 of 12 committed dates were below P50 and 8 of 12 failed
  the 85% target.
- If pushed ("isn't that just average velocity?"): an average gives one date and no spread.
  The whole value is the spread. The P50-to-P85 gap runs up to 4 sprints in the fixture, and
  that gap is exactly what an average throws away.

### Claim 2: the forecaster's percentiles are measured, not asserted

- Proof: `sprint-forecast --trials 2000 calibrate --teams 2000 --history-len 8` builds
  synthetic teams from a known distribution and measures empirical coverage.
- The number: P85 covered 82.9% of outcomes and P95 covered 90.8%, on 2000 teams, a
  4.1-point shortfall in the tail.
- If pushed ("so your tool is wrong?"): it is optimistic in the tail by a known, published
  amount, for a structural reason (a bootstrap cannot resample an unseen value). Knowing the
  size of the error is what makes it usable. A forecaster that could not state its own error
  would be the one to distrust.

### Claim 3: it refuses rather than invents

- Proof: `sprint-forecast forecast --history "0 0 0 0 1" --backlog 600` exits 3 with
  "cannot forecast", not a fabricated date.
- The number: 3 of 4 degenerate inputs are refused with exit 3.
- If pushed: the exit-code taxonomy (ADR-003) is the point. A delivery gate must tell a
  risky date (exit 2) apart from an uncomputable one (exit 3), and a single non-zero code
  cannot.

### Claim 4: every number reproduces

- Proof: `make verify` from a fresh clone, offline, runs 94 tests at 99.5% line coverage,
  re-runs the experiments, and checks this guide and the README against the measured values.
- If pushed ("did you just hardcode the numbers?"): change one figure in the README and the
  build fails. There is a note in the build output confirming the checker runs, and the
  checker has been seen to fail on a deliberately broken figure.

## Questions that are meant to be hard

**"Isn't this just a wrapper around numpy's random?"** The sampling is one line of numpy; the
engineering is everything around it: the stationary-bootstrap completion model, the absolute
cap that turns a near-stalled team into an honest "unbounded" instead of a huge number, the
exit-code contract, and above all the calibration harness that grades the percentiles. The
numpy call is not the contribution; the measurement of whether the output can be trusted is.

**"The corpus is synthetic. Does any of this transfer?"** The fixture and the calibration
ground truth are synthetic, and the README says so. What transfers is a statement about the
method, not about one team: a bootstrap under-covers an unobserved tail, by an amount that
shrinks as history grows (from 83.8% at four sprints to 94.9% at forty sprints). On a real
team you would feed real Jira throughput; the method and its known weakness are unchanged.

**"What is the weakest part?"** The stationarity assumption (ADR-004). The forecaster is
blind to a structural change that has not happened yet: a team scaling, a scope change, a
reorg. On a genuinely non-stationary team the forecast is wrong in a direction throughput
alone cannot reveal. I did not engineer around it because the fixture has no documented
break to validate a fix against; it is the Pivot, with a concrete trigger.

**"Why only a negative binomial for the calibration ground truth?"** Because it is
overdispersed the way real velocity is (variance above the mean), and it is a shape the
bootstrap does not get to see directly. A single ground truth is enough to demonstrate the
structural point. Testing more shapes is cheap follow-up work, not a different design.

**"What would you do differently with more time?"** Add changepoint detection and a
trend-aware resampler for non-stationary teams, and validate it the same way the stationary
version is validated now: does calibrated coverage hold across a known break. I would also
add the Playwright evidence path once a browser is available (ADR-005).

**"Why report sprint counts and not dates?"** A sprint count is a property of the data; a
date also depends on sprint length and a start date the caller supplies (ADR-002). Counts
reproduce exactly across machines, which is what lets the numbers be machine-checked.

## Things to say, and things not to say

Say:

- "Its P95 is optimistic by a measured 4.1-point margin on a short history, and the amount
  is published."
- "It refuses a team it cannot honestly date."
- "Every number in the README is re-measured by CI and breaking one fails the build."

Do not say:

- "It predicts delivery dates accurately." It prices a date as a probability; accuracy of
  the upper percentiles is measured and is imperfect on short history.
- "It is calibrated." Say P85 covered 82.9% of outcomes and P95 covered 90.8% on 2000 teams,
  with the resolution floor; do not round it to "calibrated".
- "It works on any team." It assumes stationarity; say that before someone asks.

## The live demo script

```bash
# 1. a committed date that looks fine but is a long shot
sprint-forecast forecast --history "7 12 3 9 5 11 4 8 6 10" --backlog 70 --committed 7

# 2. the same team, a safe commitment
sprint-forecast forecast --history "7 12 3 9 5 11 4 8 6 10" --backlog 70 --committed 11

# 3. the headline across the fixture
sprint-forecast scenarios

# 4. the forecaster grading itself
sprint-forecast --trials 2000 calibrate --teams 2000 --history-len 8

# 5. a team it refuses to date
sprint-forecast forecast --history "0 0 0 0 1" --backlog 600
```
