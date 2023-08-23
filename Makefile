.PHONY: clean-pyc clean-build build

ENV=env
PY_VERSION=python3.10
USERNAME=seluxit

clean: clean-pyc clean-build

clean-all: clean-pyc clean-build clean-env

clean-pyc:
	find . -name '__pycache__' -exec rm --force --recursive {} + 
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~'    -exec rm --force {} +

clean-build:
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info
	rm --force --recursive .tox
	rm --force --recursive htmlcov
	rm --force --recursive .coverage
	rm --force --recursive .mypy_cache
	rm --force --recursive coverage.json

clean-env:
	rm --force --recursive ${ENV}/

lint:
	${ENV}/bin/flake8 --docstring-convention google --ignore D212,W503  slxjsonrpc/*.py slxjsonrpc/**/*.py
	${ENV}/bin/mypy --strict --follow-imports=normal --python-version 3.7  slxjsonrpc/*.py slxjsonrpc/**/*.py

test: lint
	${ENV}/bin/tox

build: clean-all setup
	${ENV}/bin/python3 setup.py sdist bdist_wheel

publish: test build
	@echo "Please make sure that you have set 'TWINE_PASSWORD'."
	${ENV}/bin/python3 -m twine upload -u "${USERNAME}" --skip-existing dist/*

install:
	pip3 install .

setup:
	${PY_VERSION} -m venv ${ENV}/.
	${ENV}/bin/pip3 install --upgrade pip
	${ENV}/bin/pip3 install --requirement requirements.txt

