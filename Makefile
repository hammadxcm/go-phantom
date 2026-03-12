.PHONY: install dev lint format typecheck test test-cov test-verbose build clean run setup uninstall tui release bump-patch bump-minor bump-major check

# ─── Quick setup (one command — works on macOS, Linux, Windows via Git Bash) ─
setup:
	@bash install.sh

# ─── Development ─────────────────────────────────────────────────────────────
install:
	pip install -e .

dev:
	pip install -e ".[dev]"

lint:
	ruff check phantom/ tests/

format:
	ruff format phantom/ tests/

typecheck:
	mypy phantom/

# ─── Testing ─────────────────────────────────────────────────────────────────
test:
	pytest

test-cov:
	pytest --cov --cov-report=term-missing

test-verbose:
	pytest -v --tb=long

# Full pre-commit check: format → lint → test with coverage gate
check:
	ruff format --check phantom/ tests/
	ruff check phantom/ tests/
	mypy phantom/
	pytest --cov --cov-report=term-missing

# ─── Run ─────────────────────────────────────────────────────────────────────
run:
	python -m phantom

run-verbose:
	python -m phantom -v

tui:
	python -m phantom --tui

# ─── Build ───────────────────────────────────────────────────────────────────
build:
	pyinstaller build/phantom.spec --distpath dist/ --workpath build/tmp --clean

# ─── Cleanup ─────────────────────────────────────────────────────────────────
clean:
	rm -rf dist/ build/tmp/ build/__pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage htmlcov/

uninstall:
	rm -rf "$$HOME/.phantom" "$$HOME/.local/bin/phantom" "$$HOME/.local/bin/phantom.cmd" "$$HOME/.local/bin/phantom.ps1"
	@echo "Phantom uninstalled."

# ─── Version Bump ────────────────────────────────────────────────────────────
bump-patch:
	python scripts/bump_version.py --patch

bump-minor:
	python scripts/bump_version.py --minor

bump-major:
	python scripts/bump_version.py --major

# ─── Release ─────────────────────────────────────────────────────────────────
release:
	@echo "Creating release tag..."
	@read -p "Version (e.g. 0.0.1): " ver && git tag "v$$ver" && git push --tags
	@echo "Release tag pushed. GitHub Actions will build and publish."
