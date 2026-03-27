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
        if ".enc." in path.name:
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
    html_file = pick_latest_file(html_files, "HTML", output_dir)
    pdf_file = pick_latest_file(pdf_files, "PDF", output_dir)

    target_dir = SITE_DIR / language / template_name
    target_dir.mkdir(parents=True, exist_ok=True)
    target_pdf_name = f"CV_{language}_{template_name}.pdf"

    shutil.copy2(html_file, target_dir / "index.html")
    shutil.copy2(pdf_file, target_dir / target_pdf_name)

    return {
        "language": language,
        "template": template_name,
        "html": f"{language}/{template_name}/",
        "pdf": f"{language}/{template_name}/{target_pdf_name}",
    }


def write_index(entries: list[dict[str, str]]) -> None:
    entries.sort(key=lambda entry: (entry["language"], entry["template"]))
    items = []
    for entry in entries:
        language = html.escape(entry["language"])
        template_name = html.escape(entry["template"])
        html_path = html.escape(entry["html"])
        pdf_path = html.escape(entry["pdf"])
        items.append(
            f"<li><strong>{language}/{template_name}</strong> "
            f"<a href=\"{html_path}\">HTML</a> "
            f"<a href=\"{pdf_path}\">PDF</a></li>"
        )

    index = f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Alessandro Saglia | CV Index</title>
    <style>
      :root {{ color-scheme: light; }}
      body {{
        margin: 0;
        font-family: Georgia, 'Times New Roman', serif;
        line-height: 1.5;
        background-color: #f8f7f4;
        color: #1d1d1d;
      }}
      main {{ max-width: 760px; min-height: 100vh; box-sizing: border-box; margin: 0 auto; padding: 48px 24px 64px; }}
      h1 {{ margin: 0 0 12px; font-size: 2.2rem; }}
      p {{ line-height: 1.6; color: #444; }}
      ul {{ padding-left: 20px; line-height: 1.9; }}
      a {{ color: #0b57d0; text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
    </style>
  </head>
  <body>
    <main>
      <h1>Curriculum Vitae</h1>
      <p>Available public previews generated automatically from the RenderCV sources.</p>
      <ul>
        {''.join(items)}
      </ul>
    </main>
  </body>
</html>
"""
    (SITE_DIR / "index.html").write_text(index, encoding="utf-8")


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