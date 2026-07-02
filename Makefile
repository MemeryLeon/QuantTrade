.PHONY: doctor bootstrap dev check test test-integration e2e down

PYTHON ?= python

doctor:
	$(PYTHON) scripts/dev.py doctor

bootstrap:
	$(PYTHON) scripts/dev.py bootstrap

dev:
	$(PYTHON) scripts/dev.py dev

check:
	$(PYTHON) scripts/dev.py check

test:
	$(PYTHON) scripts/dev.py test

test-integration:
	$(PYTHON) scripts/dev.py test-integration

e2e:
	$(PYTHON) scripts/dev.py e2e

down:
	$(PYTHON) scripts/dev.py down
