PYTHON := .venv/bin/python
OUT    := $(abspath cv_generated)

.PHONY: it en anon all dry site index preview act test lint clean help

# ── CV generation ────────────────────────────────────────────────────────────

$(OUT):
	mkdir -p $(OUT)

it: | $(OUT)
	$(PYTHON) scripts/injector.py render src/it/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_IT.pdf \
		-nomd -nohtml -nopng

en: | $(OUT)
	$(PYTHON) scripts/injector.py render src/en/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_EN.pdf \
		-nomd -nohtml -nopng

anon: | $(OUT)
	$(PYTHON) scripts/injector.py render src/en/master-anon.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_EN_anon.pdf \
		-nomd -nohtml -nopng

all: it en anon

dry: | $(OUT)
	$(PYTHON) scripts/injector.py --dry-run render src/it/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_IT_preview.pdf \
		-nomd -nohtml -nopng
	$(PYTHON) scripts/injector.py --dry-run render src/en/master.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_EN_preview.pdf \
		-nomd -nohtml -nopng
	$(PYTHON) scripts/injector.py --dry-run render src/en/master-anon.yaml \
		--pdf-path $(OUT)/Alessandro_Saglia_CV_EN_anon_preview.pdf \
		-nomd -nohtml -nopng

# ── Site ─────────────────────────────────────────────────────────────────────

site:
	$(PYTHON) scripts/generate_index.py
	$(PYTHON) scripts/build_pages_site.py

index:
	$(PYTHON) scripts/generate_index.py

preview: site
	(sleep 1 && open http://localhost:8080) & \
	python -m http.server 8080 --directory site

# ── CI ───────────────────────────────────────────────────────────────────────

act:
	act --job lint-and-validate \
		--workflows .github/workflows/ci.yml \
		--container-architecture linux/amd64 -v

# ── Dev ──────────────────────────────────────────────────────────────────────

test:
	.venv/bin/pytest tests/ -v

lint:
	.venv/bin/ruff check scripts/

clean:
	rm -rf cv_generated src/*/rendercv_output

# ── Help ─────────────────────────────────────────────────────────────────────

help:
	@echo "CV generation (with secrets):"
	@echo "  make it      — IT"
	@echo "  make en      — EN"
	@echo "  make anon    — EN anon"
	@echo "  make all     — tutti e tre"
	@echo "  make dry     — tutti e tre, dry-run (senza segreti)"
	@echo ""
	@echo "Site:"
	@echo "  make site    — genera site/index.html + copia output"
	@echo "  make index   — solo site/index.html"
	@echo "  make preview — build site + serve su :8080 + apre browser"
	@echo ""
	@echo "CI:"
	@echo "  make act     — simula ci.yml in locale con act"
	@echo ""
	@echo "Dev:"
	@echo "  make test    — pytest"
	@echo "  make lint    — ruff"
	@echo "  make clean   — rimuove cv_generated/ e rendercv_output/"
