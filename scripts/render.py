"""Render CV templates via injector.py and copy outputs to _site/.

This script handles the "render + copy" step of the site build:
1) Discover master.yaml templates under src/<lang>/
2) Run injector.py --dry-run for each template
3) Copy generated PDFs and Markdown to _site/<lang>/<template>/

Orchestration (calling generate_index, copy_assets, generate_sitemap)
is handled by the Makefile, not by this script.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from config import ROOT_DIR, SRC_DIR, SITE_DIR


def discover_templates() -> list[Path]:
    """Find master.yaml CV templates (one per language directory).

    Only files named 'master.yaml' are rendered for the site.
    Other YAML files (e.g. master-anon.yaml) are for PDF-only rendering.
    """
    templates = []
    for lang_dir in sorted(SRC_DIR.iterdir()):
        if not lang_dir.is_dir():
            continue
        master = lang_dir / "master.yaml"
        if master.exists():
            templates.append(master)
    return templates


def clean_output_dir(output_dir: Path) -> None:
    """Clean generated files from output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.pdf", "*.png", "*.md", "*.html", "*.typ"):
        for file_path in output_dir.glob(pattern):
            file_path.unlink()


def pick_latest_file(files: list[Path], file_type: str, output_dir: Path) -> Path:
    """Pick the most recently modified file of a given type."""
    if not files:
        raise RuntimeError(f"Expected at least 1 {file_type} in {output_dir}, found 0")
    return max(files, key=lambda file_path: (file_path.stat().st_mtime, file_path.name))


def build_template(template_path: Path, preview_mode: bool = False) -> None:
    """Build a single CV template (render to PDF/Markdown).

    In normal mode, copies outputs to _site/<lang>/<template>/ for GitHub Pages.
    In preview mode (--preview), renames outputs in place inside rendercv_output/
    so they can be picked up as CI artifacts without building the full site.
    """
    language = template_path.parent.name
    template_name = template_path.stem
    output_dir = template_path.parent / "rendercv_output"

    print(f"Building {language}/{template_name}...")
    clean_output_dir(output_dir)

    subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "injector.py"), "--dry-run", "render", str(template_path)],
        cwd=ROOT_DIR,
        check=True,
    )

    # Find generated files
    pdf_files = sorted(output_dir.glob("*.pdf"))
    md_files = sorted(output_dir.glob("*.md"))

    pdf_file = pick_latest_file(pdf_files, "PDF", output_dir)
    md_file = pick_latest_file(md_files, "Markdown", output_dir) if md_files else None

    target_pdf_name = f"CV_{language}_{template_name}.pdf"
    target_md_name = f"CV_{language}_{template_name}.md"

    if preview_mode:
        # Rename in place so CI can upload as artifact
        pdf_file.rename(output_dir / target_pdf_name)
        print(f"Created: {output_dir / target_pdf_name}")
        if md_file:
            md_file.rename(output_dir / target_md_name)
            print(f"Created: {output_dir / target_md_name}")
    else:
        # Copy to _site/<lang>/<template>/ for GitHub Pages
        target_dir = SITE_DIR / language / template_name
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_file, target_dir / target_pdf_name)
        if md_file:
            shutil.copy2(md_file, target_dir / target_md_name)


def main() -> None:
    preview_mode = "--preview" in sys.argv

    templates = discover_templates()
    if not templates:
        raise RuntimeError("No master.yaml templates found under src/<lang>/.")

    if not preview_mode:
        SITE_DIR.mkdir(parents=True, exist_ok=True)

    for template_path in templates:
        build_template(template_path, preview_mode=preview_mode)

    print("✓ Render complete")


if __name__ == "__main__":
    main()
