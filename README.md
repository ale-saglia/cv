# Alessandro Saglia - Curriculum Vitae (Source)

This repository contains the source files for my professional curriculum vitae, managed using a **CV-as-Code** approach. This methodology ensures version control, structural consistency, and a clean separation between professional data and its visual representation.

## 🛠️ Tech Stack
*   **Framework:** [RenderCV](https://github.com/sinaatalay/rendercv) — transforms YAML data into professional documents (PDF, HTML, Markdown, Typst).
*   **Data Format:** YAML (structured professional data with anchor/alias support).
*   **Code Quality:** [ruff](https://github.com/astral-sh/ruff) for Python linting (local + CI).
*   **Secrets Management:** gitignore + placeholder injection.
*   **Output Formats:** PDF, Markdown, HTML, Typst.
*   **Version Control:** Git.

Repository note: all documentation, comments, and configuration are kept in English for consistency.

## 🏛️ Rationale

CV data is stored in version-controlled YAML and rendered into multiple formats. The approach is organized around three core principles:

### No Proprietary Lock-in
The CV is generated without relying on proprietary platforms.  
All data (roles, dates, links) remains under direct control and ownership.

### Single Source of Truth
Professional data is stored in YAML and versioned through Git.  
Changes are tracked over time, making career evolution explicit and reproducible.

### Data Reusability
A single structured dataset generates multiple outputs (HTML, PDF, Markdown).  
The same source powers both the downloadable CV and the web representation.

### In practice:
- Career versioning through Git  
- Multi-format generation from a single dataset  
- Separation between data and presentation  
- Privacy handled at render time (sensitive data injected locally)

## 📂 Repository Structure

```
.
├── scripts/
│   └── injector.py          # Load secrets / dry-run sanitize → render → cleanup
├── src/
│   ├── design.yaml          # Global design shared by all CVs
│   ├── settings.yaml        # Global settings shared by all CVs
│   ├── en/
│   │   ├── master.yaml      # English CV template (cv section only)
│   │   └── locale.yaml      # English locale shared by all English CVs
│   ├── it/
│   │   └── locale.yaml      # Italian locale shared by all Italian CVs
│   └── secret.example.yaml  # Example secret schema (committed)
├── requirements.txt
└── README.md
```

Secret fields in the YAML templates use `${SECRET_<KEY>}` placeholders, or are left empty and filled automatically by the injector when a matching key exists in `src/secret.yaml`.

`src/secret.yaml` is intentionally **not** committed.

## 🚀 How to Render

### Prerequisites

```bash
# Python dependencies
pip install -r requirements.txt
```

### Local secrets setup

Create your local plaintext secrets file from the example template:

```bash
cp src/secret.example.yaml src/secret.yaml
```

Fill values in `src/secret.yaml`.

Do not commit `src/secret.yaml`.

### Render

```bash
# English CV
python scripts/injector.py render src/en/master.yaml

# Another English variant (if present)
python scripts/injector.py render src/en/one-page.yaml
```

`injector.py` now auto-loads overlays before rendering:

- global design: `src/design.yaml`
- global settings: `src/settings.yaml`
- per-language locale: `src/<lang>/locale.yaml`

So each `src/<lang>/*.yaml` CV file can contain only the `cv` section.

The injector will:
1. Load `src/secret.yaml` when present.
2. Replace `${SECRET_*}` placeholders and fill empty `cv` fields with local secret values.
3. Run `rendercv render` on a temporary file.
4. Delete the temporary injected YAML file.

If `src/secret.yaml` is missing, injector automatically falls back to a sanitized dry-run behavior by removing lines containing `${SECRET_*}` placeholders.

The injected render template may contain secret values temporarily and is always removed at the end of execution.

Output is generated in `src/<lang>/rendercv_output/`.

### Render sanitized preview (CI)

The `Render Preview` workflow runs `injector.py --dry-run`, renders all CV YAML files under `src/<lang>/` (excluding locale/config overlays), and uploads sanitized public artifacts as:

- `CV_en_master.pdf`
- `CV_<lang>_<template>.pdf` (generic pattern)

This workflow does not require local/remote secret files.

### Debug & Development Tasks (VS Code)

The repository includes pre-configured tasks in `.vscode/tasks.json` for local development and debugging.

**Available tasks** (via `Cmd+Shift+B` or Command Palette → "Run Task"):

- **Generate Index (Local Debug)** — Run `generate_index.py` to build the main website (`site/index.html`). Use this for rapid iteration on the integrated CV display.
- **Inject Secrets & Render CV (Dry-run)** — Run `injector.py --dry-run` to test CV rendering without local secrets. Simulates CI behavior.
- **Build Full Site (Local)** — Orchestrate all build steps: generate index, render all templates, place outputs in `site/<lang>/`. Default build task.
- **View Generated Site** — Open the generated `site/index.html` in the browser (depends on "Generate Index").
- **Simulate CI with act (render-preview)** — Run the GitHub Actions workflow locally using [act](https://github.com/nektos/act). Simulates the sanitized preview rendering.
- **Simulate CI with act (ci.yml)** — Run the linting/format checks workflow locally. Requires `act` installed.
- **Lint & Format (Ruff)** — Apply ruff fixes to Python scripts.
- **Clean Generated Files** — Remove all generated artifacts (output directories and `site/index.html`).

**Debug configurations** (`.vscode/launch.json`):

- Press `F5` or use the Run & Debug panel to attach a debugger to:
  - Debug: Generate Index
  - Debug: Injector (Dry-run)
  - Debug: Build Site

**Prerequisites for CI simulation:**

Install [act](https://github.com/nektos/act) to simulate GitHub Actions locally:

```bash
brew install act
```

### One-click preview & website

The repository publishes the CV to GitHub Pages via [cv.ale-saglia.com](https://cv.ale-saglia.com) on pushes to `main`.

The main website (`site/index.html`) includes:
- **Integrated CV display**: Full CV embedded directly (no iframe)
- **Language switcher**: Italian and English selection
- **Download options**: PDF and Markdown in both languages
- **Design**: Consistent with [ale-saglia.com](https://ale-saglia.com) and [insight.ale-saglia.com](https://insight.ale-saglia.com) (Georgia, color palette, responsive)
- **Dark mode**: Automatic per system preference
- **Language persistence**: LocalStorage caching

The build process (`build_pages_site.py`):
1. Discovers CV templates under `src/<lang>/`
2. Renders templates via `injector.py --dry-run`
3. Copies outputs (PDF, HTML, Markdown) to `site/<lang>/<template>/`  
4. Preserves `site/index.html` (manually maintained)

See [site/README.md](site/README.md) for website structure details.

## 🧪 Compatibility

The repository is tested in CI with Python 3.14. Newer local versions may work, but 3.14 is the reference runtime for reproducible checks. Dependency versions are pinned in [`requirements.txt`](requirements.txt) and kept up to date by Renovate.

## 📄 License

This repository is distributed under the terms described in [LICENSE](LICENSE).
The CV content and generated documents remain proprietary to the author.

## ⚖️ Privacy & Data Protection

This repository implements data minimization: only professional information necessary for networking is included in source files.

**Sensitive fields** (phone, email, address) are represented as `${SECRET_*}` placeholders in templates. Actual values are stored in the local file `src/secret.yaml` (excluded via `.gitignore`, not committed). At-rest protection uses OS-level full-disk encryption.

**No encrypted secrets are stored in the repository** — keeping personal data in version control creates permanent history records. A local plaintext file excluded from version control is the appropriate approach for a minimal set of three contact identifiers.

*Note: Earlier iterations explored `sops` + `age` for encrypted secrets storage. This was reconsidered: a local plaintext file provides proportionate protection without repository history constraints.*

**Maintained by Alessandro Saglia**
*Digital Governance Specialist | IT Engineering Student | Open Source Contributor*
