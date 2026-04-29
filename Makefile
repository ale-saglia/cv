PYTHON ?= .venv/bin/python
PYTEST ?= .venv/bin/pytest
RUFF   ?= .venv/bin/ruff
OUT    := $(abspath _cv)

.PHONY: all dry site index preview act test lint clean help

# ── CV generation ────────────────────────────────────────────────────────────

$(OUT):
	mkdir -p $(OUT)

all: | $(OUT)
	$(PYTHON) scripts/injector.py render src/it/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_IT.pdf \
		-nomd -nohtml -nopng
	$(PYTHON) scripts/injector.py render src/en/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_EN.pdf \
		-nomd -nohtml -nopng

dry: | $(OUT)
	$(PYTHON) scripts/injector.py --dry-run render src/it/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_IT_preview.pdf \
		-nomd -nohtml -nopng
	$(PYTHON) scripts/injector.py --dry-run render src/en/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_EN_preview.pdf \
		-nomd -nohtml -nopng

# ── Site ─────────────────────────────────────────────────────────────────────

site:
	$(PYTHON) scripts/generate_index.py
	$(PYTHON) scripts/build_pages_site.py

index:
	$(PYTHON) scripts/generate_index.py

preview: site
	-lsof -ti:8080 | xargs kill -9 2>/dev/null || true
	@echo "Preview at http://localhost:8080"
	$(PYTHON) scripts/preview_server.py 8080

# ── CI ───────────────────────────────────────────────────────────────────────

act:
	act --job lint-and-validate \
		--workflows .github/workflows/ci.yml \
		--container-architecture linux/amd64 -v

# ── Dev ──────────────────────────────────────────────────────────────────────

test:
	$(PYTEST) tests/ -v

lint:
	$(RUFF) check scripts/

clean:
	rm -rf _cv src/*/rendercv_output

# ── Help ─────────────────────────────────────────────────────────────────────

help:
	@echo "CV generation (with secrets):"
	@echo "  make all     — IT + EN"
	@echo "  make dry     — IT + EN, dry-run (no secrets injected)"
	@echo ""
	@echo "Site:"
	@echo "  make site    — generate site/index.html + copy outputs"
	@echo "  make index   — generate site/index.html only"
	@echo "  make preview — build site + serve on :8080 + open browser"
	@echo ""
	@echo "CI:"
	@echo "  make act     — simulate ci.yml locally with act"
	@echo ""
	@echo "Dev:"
	@echo "  make test    — pytest"
	@echo "  make lint    — ruff"
	@echo "  make clean   — remove _cv/ and rendercv_output/"
