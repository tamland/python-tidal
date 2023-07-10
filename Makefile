.PHONY: lint test install format all
POETRY ?= poetry run

help:
	@printf "Chose one of install, format, lint or test.\n"

install:
	rm -rf dist
	poetry build
	pip install dist/*.whl

format:
	${POETRY} isort tidalapi tests
	${POETRY} black tidalapi tests
	${POETRY} docformatter -i tidalapi tests
	# ${POETRY} ruff . # Don't autofix as ruff can break things

lint:
	${POETRY} isort --check tidalapi tests
	${POETRY} black --check tidalapi tests
	${POETRY} docformatter --check tidalapi tests
	# ${POETRY} ruff .


test:
	${POETRY} pytest tests/
