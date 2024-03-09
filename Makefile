.PHONY: build* clean wheel test*
build:
	python -m build

clean:
	rm -rf build dist *.egg-info

wheel:
	python -m build --wheel

build/venv:
	.venv/bin/python -m build --no-isolation

test:
	python -m pytest

test/integration:
	python -m pytest --integration
