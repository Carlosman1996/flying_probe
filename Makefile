setup:
	python3 -m venv .venv && . .venv/bin/activate
	pip install --upgrade pip
	pip install -r requirements.dev

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.benchmarks' -exec rm -fr {} +
	find . -name '.pytest_cache' -exec rm -fr {} +
	find . -name '.mypy_cache' -exec rm -fr {} +

clean-test:
	rm -f .coverage
	rm -f .coverage.*

clean: clean-pyc clean-test

test:
	. .venv/bin/activate && py.test tests -n=auto --cov=source --cov-report=term-missing --cov-fail-under 0

mypy:
	. .venv/bin/activate && mypy source

lint:
	. .venv/bin/activate && pylint source -j 4 --reports=y

flake8:
	. .venv/bin/activate && flake8 source --ignore E501,N801,N802,N806,N803,D,E402

check: test flake8 clean
