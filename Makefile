.PHONY: validate test check

validate:
	python3 scripts/badf_gate.py repo

test:
	python3 -m unittest discover -s tests -p 'test_*.py'

check: validate test

