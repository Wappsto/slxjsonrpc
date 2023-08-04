TEST_PATH=./test

USERNAME=seluxit

.PHONY: clean-pyc clean-build build

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

clean-env:
	rm --force pyvenv.cfg
	rm --force --recursive bin/
	rm --force --recursive lib/
	rm --force --recursive lib64
	rm --force --recursive share/
	rm --force --recursive include/

lint:
	flake8 --docstring-convention google --ignore D212,W503  slxjsonrpc/*.py slxjsonrpc/**/*.py
	mypy --strict --python-version 3.7  slxjsonrpc/*.py slxjsonrpc/**/*.py

test: lint
	tox

mypy-stub:
	stubgen slxjsonrpc/{*,**/*}.py --out .

build: clean-all
	python3 setup.py sdist bdist_wheel

publish: test build
	@echo "Please make sure that you have set 'TWINE_PASSWORD'."
	python3 -m twine upload -u "${USERNAME}" --skip-existing dist/*

install:
	pip3 install .

setup:
	python3 -m venv .
	./bin/pip3 install --requirement requirements.txt

