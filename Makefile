VENV_BIN   ?= .venv/bin
PYTHON     ?= $(VENV_BIN)/python
PYTEST     ?= $(VENV_BIN)/pytest
RUFF       ?= $(VENV_BIN)/ruff
OUT        := $(abspath _cv)
PORT       ?= 8080

.DEFAULT_GOAL := help
.PHONY: help setup lock build serve preview all dry rebuild clean test lint act

# ── Help ─────────────────────────────────────────────────────────────

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "  setup    Create .venv and install from requirements-dev.txt"
	@echo "  lock     Recompile requirements*.txt from *.in (update hashes)"
	@echo "  build    Build full public site → _site/"
	@echo "  serve    Build + preview on port $(PORT)"
	@echo "  rebuild  Clean + build"
	@echo ""
	@echo "  all      Render final PDFs (with secrets) → _cv/"
	@echo "  dry      Render preview PDFs (no secrets) → _cv/"
	@echo ""
	@echo "  test     Run pytest"
	@echo "  lint     Run ruff"
	@echo "  act      Simulate CI locally with act"
	@echo "  clean    Remove _site/ _cv/ rendercv_output/"

# ── Setup ────────────────────────────────────────────────────────────

setup:
	uv venv .venv
	uv pip sync requirements-dev.txt
	@echo "Setup complete. Run 'make build' or 'make serve'."

lock:
	uv pip compile requirements.in --generate-hashes -o requirements.txt --python-version 3.14
	uv pip compile requirements-dev.in --generate-hashes -o requirements-dev.txt --python-version 3.14

# ── Site build ───────────────────────────────────────────────────────

build:
	@test -x $(PYTHON) || { echo "python not found — run: make setup"; exit 1; }
	@echo "Generating index.html + 404.html..."
	$(PYTHON) scripts/generate_index.py
	@echo "Copying static assets..."
	$(PYTHON) scripts/copy_assets.py
	@echo "Rendering CV templates (dry-run)..."
	$(PYTHON) scripts/render.py
	@echo "Generating sitemap.xml + robots.txt..."
	$(PYTHON) scripts/generate_sitemap.py
	@echo "Build complete → _site/"

serve: build
	-lsof -ti:$(PORT) | xargs kill -9 2>/dev/null || true
	@echo "Preview at http://localhost:$(PORT)"
	$(PYTHON) scripts/preview_server.py $(PORT)

preview: serve

rebuild: clean build

# ── CV generation (with secrets) ─────────────────────────────────────

$(OUT):
	mkdir -p $(OUT)

all: | $(OUT)
	@test -x $(PYTHON) || { echo "python not found — run: make setup"; exit 1; }
	$(PYTHON) scripts/injector.py render src/it/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_IT.pdf \
		-nomd -nohtml -nopng
	$(PYTHON) scripts/injector.py render src/en/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_EN.pdf \
		-nomd -nohtml -nopng

dry: | $(OUT)
	@test -x $(PYTHON) || { echo "python not found — run: make setup"; exit 1; }
	$(PYTHON) scripts/injector.py --dry-run render src/it/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_IT_preview.pdf \
		-nomd -nohtml -nopng
	$(PYTHON) scripts/injector.py --dry-run render src/en/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_EN_preview.pdf \
		-nomd -nohtml -nopng

# ── Dev ──────────────────────────────────────────────────────────────

test:
	@test -x $(PYTEST) || { echo "pytest not found — run: make setup"; exit 1; }
	$(PYTEST) tests/ -v

lint:
	@test -x $(RUFF) || { echo "ruff not found — run: make setup"; exit 1; }
	$(RUFF) check scripts/

act:
	act --job lint-and-validate \
		--workflows .github/workflows/ci.yml \
		--container-architecture linux/amd64 -v

clean:
	rm -rf _site _cv src/*/rendercv_output
