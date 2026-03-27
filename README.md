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
As a professional working at the intersection of **Digital Governance** and **Computer Engineering**, I believe that even a resume should reflect *systems awareness*. Managing my CV as code enables:
*   **Technical Consistency:** Precise management of technical milestones and career evolution.
*   **Career Versioning:** Tracking the evolution of my roles, from **Legal Enforcement** in local government to **Healthcare Digital Governance** at a regional level.
*   **Privacy by Design:** Sensitive personal data (e.g., phone, email, address) is managed through local placeholders and injected only at render time.

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

### One-click preview

The repository publishes all available sanitized public CV variants through GitHub Pages on pushes to `main`.
Pages generates a dynamic index and exposes, for each available template under `src/<lang>/`, both:

- an HTML preview
- a PDF download named `CV_<lang>_<template>.pdf`

## 🧪 Compatibility

| Component | Version |
|-----------|--------|
| Python | 3.13 (CI baseline) |
| rendercv | 2.7 |
| PyYAML | 6.0.3 |
| ruff | 0.13.2 |

The repository is tested in CI with Python 3.13. Newer local versions may work, but 3.13 is the reference runtime for reproducible checks.

## 📄 License

This repository is distributed under the terms described in [LICENSE](LICENSE).
The CV content and generated documents remain proprietary to the author.

## ⚖️ Privacy & Data Protection
Consistent with my academic specialization in GDPR and the legal framework of data governance, this repository adheres to the principle of data minimization.
Only professional information necessary for networking and recruitment is included in the public source files.

Sensitive identifiers (phone, email, address) are represented in templates using `${SECRET_*}` placeholders. Real values are stored only in the local plaintext file `src/secret.yaml`, which is excluded by `.gitignore` and never committed. Local at-rest protection relies on OS-level full-disk encryption.

-----------------------------------------------------------------------------

**Maintained by Alessandro Saglia**
*Digital Governance Specialist | IT Engineering Student | Open Source Contributor*
