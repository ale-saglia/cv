"""Build static GitHub Pages site.

Flow:
1) Generate the main integrated CV site (site/index.html) via generate_index.py
2) Render all CV templates via injector.py --dry-run to generate PDFs/Markdown for downloads
3) Place generated files in site/<lang>/<template>/ for download links
"""

import shutil
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
SITE_DIR = ROOT_DIR / "site"


def discover_templates() -> list[Path]:
    """Find all CV template YAML files (excluding locale/config)."""
    templates = []
    for path in sorted(SRC_DIR.glob("*/*")):
        if path.suffix not in {".yaml", ".yml"}:
            continue
        if path.name == "locale.yaml":
            continue
        if "rendercv_output" in path.parts:
            continue
        templates.append(path)
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


def generate_main_site() -> None:
    """Generate the main integrated CV site/index.html via generate_index.py"""
    print("Generating main CV site (site/index.html)...")
    subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "generate_index.py")],
        cwd=ROOT_DIR,
        check=True,
    )


def build_template(template_path: Path, preview_mode: bool = False) -> None:
    """Build a single CV template (render to PDF/Markdown).

    In normal mode, copies outputs to site/<lang>/<template>/ for GitHub Pages.
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
        # Copy to site/<lang>/<template>/ for GitHub Pages
        target_dir = SITE_DIR / language / template_name
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_file, target_dir / target_pdf_name)
        if md_file:
            shutil.copy2(md_file, target_dir / target_md_name)


def main() -> None:
    preview_mode = "--preview" in sys.argv

    templates = discover_templates()
    if not templates:
        raise RuntimeError("No CV templates found under src/<lang>/.")

    if not preview_mode:
        # Full build: generate integrated site + render templates for download links
        SITE_DIR.mkdir(parents=True, exist_ok=True)
        generate_main_site()

    for template_path in templates:
        build_template(template_path, preview_mode=preview_mode)

    print("✓ Build complete")


if __name__ == "__main__":
    main()