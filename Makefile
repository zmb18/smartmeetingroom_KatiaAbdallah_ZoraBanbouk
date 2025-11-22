.PHONY: help docs clean test profile

help:
	@echo "Available commands:"
	@echo "  make docs      - Generate Sphinx documentation"
	@echo "  make clean     - Clean build artifacts"
	@echo "  make test      - Run all tests"
	@echo "  make profile   - Run performance profiling"

docs:
	cd docs && sphinx-build -b html . _build/html

clean:
	rm -rf docs/_build
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

test:
	pytest services/*/app/tests/ -v

profile:
	python scripts/profile_services.py

