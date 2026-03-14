# Alessandro Saglia - Curriculum Vitae (Source)

This repository contains the source files for my professional curriculum vitae, managed using a **CV-as-Code** approach. This methodology ensures version control, structural consistency, and a clean separation between professional data and its visual representation.

## 🛠️ Tech Stack
*   **Framework:** [RenderCV](https://github.com/sinaatalay/rendercv) — transforms YAML data into professional documents (PDF, HTML, Markdown, Typst).
*   **Data Format:** YAML (structured professional data with anchor/alias support).
*   **Secrets Management:** [sops](https://github.com/getsops/sops) + [age](https://github.com/FiloSottile/age) encryption.
*   **Output Formats:** PDF, Markdown, HTML, Typst.
*   **Version Control:** Git.

Repository note: documentation is written in English and repository comments/configuration are kept in English for consistency.

## 🏛️ Rationale
As a professional working at the intersection of **Digital Governance** and **Computer Engineering**, I believe that even a resume should reflect "Systems Awareness". Managing my CV as code allows for:
*   **Technical Consistency:** Precise management of technical milestones and career evolution.
*   **Career Versioning:** Tracking the evolution of my roles, from **Legal Enforcement** in local government to **Healthcare Digital Governance** at a regional level.
*   **Privacy by Design:** Sensitive personal data (eg. birthplace and date, phone, email...) is encrypted at rest with sops and injected at render time only.

## 📂 Repository Structure

```
.
├── scripts/
│   └── injector.py          # Decrypt → inject secrets → render → cleanup
├── src/
│   ├── design.yaml          # Global design shared by all CVs
│   ├── settings.yaml        # Global settings shared by all CVs
│   ├── en/
│   │   ├── master.yaml      # English CV template (cv section only)
│   │   └── locale.yaml      # English locale shared by all English CVs
│   ├── it/
│   │   └── locale.yaml      # Italian locale shared by all Italian CVs
│   └── secret.example.yaml  # Example secret schema (committed)
├── .sops.yaml               # sops encryption rules (age key)
├── requirements.txt
└── README.md
```

Secret fields in the YAML templates use `${SECRET_<KEY>}` placeholders, or are left empty and filled automatically by the injector when a matching key exists in `src/secret.enc.yaml`.

`src/secret.enc.yaml` is intentionally **not** committed.

## 🚀 How to Render

### Prerequisites

```bash
# Python dependencies
pip install -r requirements.txt

# sops and age (macOS)
brew install sops age
```

You also need your age private key available in the default location (`~/.config/sops/age/keys.txt`) or exported as `SOPS_AGE_KEY`.

Note: the value in `.sops.yaml` is an age **public recipient key** (safe to commit), not a private key. The private key is never committed.

### Local secrets setup

Create your local plaintext secrets file from the example template:

```bash
cp src/secret.example.yaml src/secret.yaml
```

Fill values in `src/secret.yaml`, then encrypt locally:

```bash
sops --encrypt src/secret.yaml > src/secret.enc.yaml
```

Do not commit `src/secret.yaml` or `src/secret.enc.yaml`.

### Render

```bash
# English CV
python scripts/injector.py render src/en/master.yaml

# Another English variant (example)
python scripts/injector.py render src/en/one-page.yaml
```

`injector.py` now auto-loads overlays before rendering:

- global design: `src/design.yaml`
- global settings: `src/settings.yaml`
- per-language locale: `src/<lang>/locale.yaml`

So each `src/<lang>/*.yaml` CV file can contain only the `cv` section.

The injector will:
1. Decrypt `src/secret.enc.yaml` using sops.
2. Replace `${SECRET_*}` placeholders and fill empty `cv` fields with the decrypted values.
3. Run `rendercv render` on a temporary file.
4. Delete the temporary injected YAML file.

Decrypted secrets are parsed in memory and are not written to a dedicated decrypted file on disk.
The injected render template may contain secret values temporarily and is always removed at the end of execution.

Output is generated in `src/<lang>/rendercv_output/`.

### Render sanitized preview (CI)

The `Render Preview` workflow runs `injector.py --dry-run`, renders all CV YAML files under `src/<lang>/` (excluding locale/config overlays), and uploads sanitized public artifacts as:

- `CV_en_master.pdf`
- `CV_it_master.pdf`
- `CV_<lang>_<template>.pdf` (generic pattern)

This workflow does not require local/remote secret files.

### One-click preview

The repository publishes all available sanitized public CV variants through GitHub Pages on pushes to `main`.
Pages generates a dynamic index and exposes, for each available template under `src/<lang>/`, both:

- an HTML preview
- a PDF download named `CV_<lang>_<template>.pdf`

### Encrypting secrets (local)

```bash
sops --encrypt src/secret.yaml > src/secret.enc.yaml
```

## 🧪 Compatibility

| Component | Version |
|-----------|--------|
| Python | 3.13 |
| rendercv | 2.7 |
| PyYAML | 6.0.3 |
| ruff (CI) | latest |

## 📄 License

This repository is distributed under the terms described in [LICENSE](LICENSE).
The CV content and generated documents remain proprietary to the author.

## ⚖️ Privacy & Data Protection
Consistent with my academic specialization in GDPR and the legal framework of data governance, this repository adheres to the principle of data minimization.
Only professional information necessary for networking and recruitment is included in the public source files. Sensitive identifiers (phone, email, address) are encrypted with sops/age and never committed in plaintext, in accordance with Art. 5(1)(c) GDPR.

-----------------------------------------------------------------------------

**Maintained by Alessandro Saglia**
*Digital Governance Specialist | IT Engineering Student | Open Source Contributor*
