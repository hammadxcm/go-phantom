.PHONY: install dev lint format test build clean run setup uninstall tui release bump-patch bump-minor bump-major

# ─── Quick setup (one command — works on macOS, Linux, Windows via Git Bash) ─
setup:
	@bash install.sh

# ─── Development ─────────────────────────────────────────────────────────────
install:
	pip install -e .

dev:
	pip install -e ".[dev]" && pip install pytest pytest-cov

lint:
	ruff check phantom/

format:
	ruff format phantom/

test:
	pytest --tb=short -q

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
