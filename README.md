# Alessandro Saglia - Curriculum Vitae (Source)

This repository contains the source files for my professional curriculum vitae, managed using a **CV-as-Code** approach. This methodology ensures version control, structural consistency, and a clean separation between professional data and its visual representation.

## 🛠️ Tech Stack

- **Framework:** [RenderCV](https://github.com/sinaatalay/rendercv) — transforms YAML data into professional documents (PDF, HTML, Markdown, Typst)
- **Data Format:** YAML (structured professional data)
- **Templating:** Jinja2 + [mistune](https://github.com/lepture/mistune) for the site generator
- **Code Quality:** [ruff](https://github.com/astral-sh/ruff) for Python linting (local + CI)
- **Secrets Management:** gitignore + placeholder injection
- **Dependency Updates:** [Renovate](https://github.com/renovatebot/renovate) (weekly grouped PRs, automerge on patches)

Repository note: all documentation, comments, and configuration are kept in English for consistency.

## 🏛️ Rationale

See [philosophy.md](philosophy.md).

## 📂 Repository Structure

```
.
├── scripts/
│   ├── injector.py             # Secret injection + render orchestration
│   ├── generate_index.py       # Generates site/index.html from YAML source
│   ├── build_pages_site.py     # Copies rendered outputs into site/
│   ├── validate_yaml.py        # YAML validation (used by CI)
│   └── templates/
│       └── index.html.j2       # Jinja2 template for the public site
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
├── cv_generated/               # Rendered PDFs (gitignored)
├── site/                       # GitHub Pages output
├── Makefile                    # Primary task runner
├── renovate.json               # Automated dependency updates config
└── requirements.txt
```

Secret fields in the YAML templates use `${SECRET_<KEY>}` placeholders, or are left empty and filled automatically by the injector when a matching key exists in `src/secret.yaml`.

`src/secret.yaml` is intentionally **not** committed.

## 🚀 How to Render

### Prerequisites

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Local secrets setup

```bash
cp src/secret.example.yaml src/secret.yaml
# fill in values — do not commit
```

### Render

```bash
make all      # Render all CVs → cv_generated/
make dry      # Dry-run (no secrets injected, _preview suffix)
```

Output goes to `cv_generated/` (gitignored).

If `src/secret.yaml` is missing, the injector strips `${SECRET_*}` placeholders automatically (same behaviour as `--dry-run`).

### Site

```bash
make site     # Generate site/index.html + copy rendered outputs
make preview  # Build site + serve on :8080 + open browser
```

### Dev

```bash
make test     # pytest
make lint     # ruff
make clean    # Remove cv_generated/ and rendercv_output/ directories
make act      # Simulate CI locally with act (requires brew install act)
```

### VS Code

All tasks are available via `Cmd+Shift+B` → Run Task:

| Task | Command |
|---|---|
| Render (with secrets) | `make all` |
| Render (dry-run) | `make dry` |
| Build Site | `make site` |
| Preview Site | `make preview` |
| Test (pytest) | `make test` |
| Lint (ruff) | `make lint` |
| Clean | `make clean` |
| Simulate CI (act) | `make act` |

Debug configurations (F5 / Run & Debug panel):
- **Debug: Generate Index** — attach debugger to `generate_index.py`
- **Debug: Build Site** — attach debugger to `build_pages_site.py`

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
The build automation scripts under `scripts/` are released under the MIT License — see [`scripts/LICENSE`](scripts/LICENSE).

## ⚖️ Privacy & Data Protection

This repository implements data minimization: only professional information necessary for networking is included in source files.

**Sensitive fields** (phone, email, address) are represented as `${SECRET_*}` placeholders in templates. Actual values are stored in the local file `src/secret.yaml` (excluded via `.gitignore`, not committed). At-rest protection uses OS-level full-disk encryption.

**No encrypted secrets are stored in the repository** — keeping personal data in version control creates permanent history records. A local plaintext file excluded from version control is the appropriate approach for a minimal set of three contact identifiers.

*Note: Earlier iterations explored `sops` + `age` for encrypted secrets storage. This was reconsidered: a local plaintext file provides proportionate protection without repository history constraints.*