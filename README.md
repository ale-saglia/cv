# Alessandro Saglia - Curriculum Vitae (Source)

This repository contains the source files for my professional curriculum vitae, managed using a **CV-as-Code** approach. This methodology ensures version control, structural consistency, and a clean separation between professional data and its visual representation.

## 🛠️ Tech Stack

- **Framework:** [RenderCV](https://github.com/sinaatalay/rendercv) — transforms YAML data into professional documents (PDF, HTML, Markdown, Typst)
- **Data Format:** YAML (structured professional data)
- **Templating:** Jinja2 + [mistune](https://github.com/lepture/mistune) for the site generator
- **Code Quality:** [ruff](https://github.com/astral-sh/ruff) for Python linting (local + CI)
- **Secrets Management:** gitignore + placeholder injection
- **Dependency Management:** [uv](https://github.com/astral-sh/uv) with hash-locked `requirements*.txt`
- **Dependency Updates:** [Renovate](https://github.com/renovatebot/renovate) (weekly grouped PRs, automerge on patches)

Repository note: all documentation, comments, and configuration are kept in English for consistency.

## 🏛️ Rationale

See [philosophy.md](philosophy.md).

## 📂 Repository Structure

```text
.
├── scripts/
│   ├── config.py               # Shared paths and constants
│   ├── injector.py             # Secret injection + rendercv orchestration
│   ├── render.py               # Discovers templates, renders via injector, copies to _site/
│   ├── generate_index.py       # Generates _site/index.html + 404.html from YAML source
│   ├── generate_sitemap.py     # Generates _site/sitemap.xml + robots.txt
│   ├── copy_assets.py          # Copies favicon and OG image to _site/assets/
│   ├── preview_server.py       # Dev server on :8080 (used by make serve)
│   ├── sync_python_version.py  # Keeps .devcontainer/Dockerfile in sync with .python-version
│   ├── validate_yaml.py        # YAML validation (used by CI)
│   └── templates/
│       ├── index.html.j2       # Jinja2 template for the public site
│       ├── 404.html.j2         # Jinja2 template for the 404 page
│       ├── favicon.svg         # Site favicon
│       └── og-image.png        # Open Graph image
├── src/
│   ├── design.yaml             # Global RenderCV design shared by all CVs
│   ├── en/
│   │   ├── master.yaml         # English CV (uses ${SECRET_*} placeholders)
│   │   └── locale.yaml         # English locale (labels, date abbreviations)
│   ├── it/
│   │   ├── master.yaml         # Italian CV
│   │   └── locale.yaml         # Italian locale
│   └── secret.example.yaml     # Example secret schema (committed)
├── tests/                      # pytest unit tests
├── .devcontainer/              # DevContainer for GitHub Codespaces / VS Code Remote
├── _cv/                        # Rendered PDFs (gitignored)
├── _site/                      # GitHub Pages output
├── Makefile                    # Primary task runner
├── renovate.json               # Automated dependency updates config
├── requirements.in             # Runtime deps (source)
├── requirements.txt            # Runtime deps, hash-locked by uv
├── requirements-dev.in         # Dev deps (source)
└── requirements-dev.txt        # Dev deps, hash-locked by uv
```

Secret fields in the YAML templates use `${SECRET_<KEY>}` placeholders, or are left empty and filled automatically by the injector when a matching key exists in `src/secret.yaml`.

`src/secret.yaml` is intentionally **not** committed.

## 🚀 How to Render

### Prerequisites

```bash
make setup      # create .venv + install runtime deps
# or
make setup-dev  # create .venv + install runtime + dev deps (tests, linting)
```

Requires [uv](https://github.com/astral-sh/uv) (`brew install uv` or `pip install uv`).

### Local secrets setup

```bash
cp src/secret.example.yaml src/secret.yaml
# fill in values — do not commit
```

### Render PDFs

```bash
make all      # Render final PDFs (with secrets) → _cv/
make dry      # Render preview PDFs (no secrets) → _cv/
```

Output goes to `_cv/` (gitignored).

If `src/secret.yaml` is missing, the injector strips `${SECRET_*}` placeholders automatically (same behaviour as `--dry-run`).

### Site

```bash
make build    # Generate _site/ (HTML, PDFs, sitemap, assets)
make serve    # Build + serve on :8080   (alias: make preview)
make rebuild  # clean + build
```

### Dev

```bash
make test     # pytest
make lint     # ruff
make clean    # Remove _site/, _cv/, rendercv_output/
make lock     # Recompile requirements*.txt from *.in (update hashes)
make act      # Simulate CI locally with act (requires brew install act)
```

### VS Code

All tasks are available via `Cmd+Shift+B` → Run Task:

| Task | Command |
| --- | --- |
| Render (with secrets) | `make all` |
| Render (dry-run) | `make dry` |
| Build Site | `make build` |
| Preview Site | `make serve` |
| Test (pytest) | `make test` |
| Lint (ruff) | `make lint` |
| Clean | `make clean` |
| Simulate CI (act) | `make act` |

Debug configurations (F5 / Run & Debug panel):

- **Debug: Generate Index** — attach debugger to `generate_index.py`
- **Debug: Copy Assets** — attach debugger to `copy_assets.py`

## 🌐 Published site

The CV is published to [cv.ale-saglia.com](https://cv.ale-saglia.com) via GitHub Pages on every push to `main`.

The site includes:

- Full CV in Italian and English with language switcher (LocalStorage persistence)
- PDF download links
- Dark mode (system preference)
- Accessible: inactive language panel carries `aria-hidden="true"`
- Consistent design with [ale-saglia.com](https://ale-saglia.com)

## 🧪 Compatibility

Tested in CI with the Python version in [`.python-version`](.python-version). Dependency versions are pinned in [`requirements.txt`](requirements.txt).

## 📄 License

This repository is distributed under the terms described in [LICENSE](LICENSE).  
The CV content and generated documents remain proprietary to the author.  

## ⚖️ Privacy & Data Protection

This repository implements data minimization: only professional information necessary for networking is included in source files.

**Sensitive fields** (phone, email, address) are represented as `${SECRET_*}` placeholders in templates. Actual values are stored in the local file `src/secret.yaml` (excluded via `.gitignore`, not committed). At-rest protection uses OS-level full-disk encryption.

**No encrypted secrets are stored in the repository** — keeping personal data in version control creates permanent history records. A local plaintext file excluded from version control is the appropriate approach for a minimal set of three contact identifiers.

*Note: Earlier iterations explored `sops` + `age` for encrypted secrets storage. This was reconsidered: a local plaintext file provides proportionate protection without repository history constraints.*
