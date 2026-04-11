"""Build a static GitHub Pages site from sanitized CV previews.

Flow:
1) Discover all CV YAML templates under src/<lang>/ (excluding locale/config overlays).
2) Render each template via injector.py --dry-run (no secrets).
3) Copy the generated HTML and PDF into site/<lang>/<template>/.
4) Write a root index.html linking all available previews.
"""

import html
import shutil
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
SITE_DIR = ROOT_DIR / "site"


def discover_templates() -> list[Path]:
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
    output_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.pdf", "*.png", "*.md", "*.html", "*.typ"):
        for file_path in output_dir.glob(pattern):
            file_path.unlink()


def pick_latest_file(files: list[Path], file_type: str, output_dir: Path) -> Path:
    if not files:
        raise RuntimeError(f"Expected at least 1 {file_type} in {output_dir}, found 0")
    return max(files, key=lambda file_path: (file_path.stat().st_mtime, file_path.name))


def build_template(template_path: Path) -> dict[str, str]:
    language = template_path.parent.name
    template_name = template_path.stem
    output_dir = template_path.parent / "rendercv_output"
    clean_output_dir(output_dir)

    subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "injector.py"), "--dry-run", "render", str(template_path)],
        cwd=ROOT_DIR,
        check=True,
    )

    html_files = sorted(output_dir.glob("*.html"))
    pdf_files = sorted(output_dir.glob("*.pdf"))
    md_files = sorted(output_dir.glob("*.md"))
    html_file = pick_latest_file(html_files, "HTML", output_dir)
    pdf_file = pick_latest_file(pdf_files, "PDF", output_dir)
    md_file = pick_latest_file(md_files, "Markdown", output_dir) if md_files else None

    target_dir = SITE_DIR / language / template_name
    target_dir.mkdir(parents=True, exist_ok=True)
    target_pdf_name = f"CV_{language}_{template_name}.pdf"
    target_md_name = f"CV_{language}_{template_name}.md"

    shutil.copy2(html_file, target_dir / "index.html")
    shutil.copy2(pdf_file, target_dir / target_pdf_name)
    if md_file:
        shutil.copy2(md_file, target_dir / target_md_name)

    return {
        "language": language,
        "template": template_name,
        "html": f"{language}/{template_name}/",
        "pdf": f"{language}/{template_name}/{target_pdf_name}",
        "md": f"{language}/{template_name}/{target_md_name}" if md_file else None,
    }


def write_index(entries: list[dict[str, str]]) -> None:
    # Note: index.html is now manually maintained to include the integrated CV site.
    # This function is kept for backward compatibility but does not overwrite index.html.
    # The index.html file in site/ contains the main CV display with language switcher and downloads.
    pass


def main() -> None:
    templates = discover_templates()
    if not templates:
        raise RuntimeError("No CV templates found under src/<lang>/.")

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    entries = [build_template(template_path) for template_path in templates]
    write_index(entries)


if __name__ == "__main__":
    main()