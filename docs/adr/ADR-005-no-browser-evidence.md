# ADR-005: No browser in the build, so evidence is charts not screenshots

Status: accepted

## Context

The standard evidence pattern for this kind of repository is a Playwright screenshot of an
HTML report and a replay video of the CLI, both rendered through Chromium. The build
environment had Playwright installed but no Chromium binary, and no network route to
download one (the package CDN was not reachable). Convention on this project is to surface a
missing tool rather than work around it silently.

## Decision

- The committed evidence is matplotlib charts rendered headless (the Agg backend, no
  browser), straight from the forecaster and the experiment JSON. They reproduce offline
  with `make evidence`.
- The demo is captured as `docs/video/manifest.json` and `docs/video/transcript.txt`: every
  command with its real stdout, exit code and wall time. The run asserts it exercised all
  three exit codes. This is a replay a reviewer can reproduce exactly, which is what the
  evidence is meant to prove.
- The HTML report (`report.render_html`) still exists and is tested; a browser screenshot of
  it is simply not part of the committed evidence, because it could not be generated here
  without inventing a result.

## Alternatives considered

- **Ship a screenshot generated elsewhere.** Rejected: a screenshot that `make evidence`
  cannot regenerate is exactly the stale artifact the receipts discipline exists to prevent.
- **Claim the screenshots exist.** Not an option; the evidence has to be real.

## Consequences

- All evidence in the repository regenerates offline with one command, which is stronger
  than a screenshot a reviewer cannot reproduce.
- If a browser is available later, `tools/capture_screenshots.py` is the natural addition;
  it is deliberately absent rather than present and broken.
