# sprint-forecast: offline, deterministic, one command to reproduce every number.
# `make verify` is the promise the README makes to a reviewer: lint, test, re-measure, check.

PY ?= python
PKG = sprint_forecast

.PHONY: help install lint test cov experiments receipts evidence verify clean

help:
	@echo "install     editable install with dev extras"
	@echo "lint        ruff check"
	@echo "test        pytest with coverage report (json + xml + terminal)"
	@echo "experiments run all experiments, writing JSON to docs/experiments/"
	@echo "receipts    re-measure every published figure and check the docs against it"
	@echo "evidence    render the committed charts and the demo manifest (offline)"
	@echo "verify      lint + test + experiments + receipts (the clone-and-trust target)"

install:
	$(PY) -m pip install -e ".[dev,charts]"

lint:
	$(PY) -m ruff check .

test:
	$(PY) -m pytest --cov=$(PKG) --cov-branch \
		--cov-report=term-missing \
		--cov-report=json:coverage.json \
		--cov-report=xml:coverage.xml \
		--junitxml=reports/junit.xml

experiments:
	$(PY) experiments/exp01_commitment_honesty.py
	$(PY) experiments/exp02_p50_p85_gap.py
	$(PY) experiments/exp03_calibration.py
	$(PY) experiments/exp04_sample_size.py
	$(PY) experiments/exp05_degenerate.py

receipts:
	$(PY) tools/collect_metrics.py --skip-tests
	$(PY) tools/check_numbers.py

evidence:
	$(PY) tools/render_diagram.py
	$(PY) tools/render_charts.py
	$(PY) tools/record_demo.py

verify: lint test experiments receipts

clean:
	rm -rf .pytest_cache .ruff_cache reports coverage.json coverage.xml .coverage htmlcov
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
