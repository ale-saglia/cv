"""Generate integrated site/index.html from YAML source files."""

import re
import shutil
import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
SITE_DIR = ROOT_DIR / "site"
TEMPLATES_DIR = Path(__file__).parent / "templates"

_SECTION_ALIASES = {
    "In breve": "summary",
    "Esperienza lavorativa": "experience",
    "formazione": "education",
    "volontariato": "volunteering_and_personal_projects",
    "certificati": "certification",
    "riconoscimenti": "selected_awards",
    "competenze": "skills",
}


def normalize_sections(sections: dict) -> dict:
    return {_SECTION_ALIASES.get(k, k): v for k, v in sections.items()}


def load_locale(lang: str) -> dict:
    """Load locale data (RenderCV locale block + section_labels)."""
    locale_path = SRC_DIR / lang / "locale.yaml"
    with open(locale_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    result = data.get("locale", {})
    result["sections"] = data.get("section_labels", {})
    return result


def load_cv_data(lang: str) -> dict:
    """Load CV data from master.yaml, with sections normalized to canonical keys."""
    yaml_path = SRC_DIR / lang / "master.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    cv = data["cv"]
    cv["sections"] = normalize_sections(cv.get("sections", {}))
    return cv


def load_cv_as_code_philosophy() -> str:
    """Extract CV-as-Code philosophy from README.md and format as HTML."""
    readme_path = ROOT_DIR / "README.md"
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        rationale_match = re.search(
            r"##\s+.*?Rationale.*?\n\n(.*?)(?=\n##\s|\Z)", content, re.DOTALL
        )
        if rationale_match:
            return md_to_html(rationale_match.group(1).strip())
    except Exception:
        pass
    return "<p>This curriculum is built with code, not proprietary tools.</p>"


def format_date_range(start_date, end_date, lang="it", month_abbrs=None):
    """Format date range for display with localized month names."""
    if month_abbrs is None:
        month_abbrs = []

    def parse_date(date_str):
        if not isinstance(date_str, str) or not date_str:
            return date_str
        parts = date_str.split("-")
        if len(parts) >= 2:
            try:
                year = parts[0]
                month_num = int(parts[1]) - 1
                if 0 <= month_num < len(month_abbrs):
                    return f"{month_abbrs[month_num]} {year}"
            except (ValueError, IndexError):
                pass
        return date_str

    start = parse_date(start_date) if isinstance(start_date, str) else ""
    if end_date == "present" or end_date is None:
        end = "in corso" if lang == "it" else "ongoing"
    elif isinstance(end_date, str):
        end = parse_date(end_date)
    else:
        end = str(end_date.year) if hasattr(end_date, "year") else str(end_date)

    return f"{start} - {end}" if start and end else f"{start}{end}".strip()


def slugify(text: str) -> str:
    """Convert text to URL-safe slug for anchor IDs."""
    text = str(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def escape_html(text):
    if not isinstance(text, str):
        return str(text)
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
    )


def md_to_html_inline(text):
    """Convert inline markdown (links, bold, italic) to HTML, with HTML escaping."""
    if not isinstance(text, str):
        return str(text)
    # Extract links before escaping to preserve URL characters
    links = []
    def stash_link(m):
        links.append((m.group(1), m.group(2)))
        return f"\x00LINK{len(links) - 1}\x00"
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", stash_link, text)
    text = escape_html(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    for i, (label, url) in enumerate(links):
        text = text.replace(
            f"\x00LINK{i}\x00",
            f'<a href="{url}" target="_blank" rel="noopener">{escape_html(label)}</a>',
        )
    return text


def md_to_html(text):
    """Convert markdown (headings, lists, paragraphs, inline) to HTML."""
    if not isinstance(text, str):
        return str(text)
    lines = text.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("###"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{md_to_html_inline(stripped.lstrip('#').strip())}</h3>")
        elif stripped.startswith("##"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{md_to_html_inline(stripped.lstrip('#').strip())}</h2>")
        elif stripped.startswith("#"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{md_to_html_inline(stripped.lstrip('#').strip())}</h1>")
        elif stripped.startswith("-"):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{md_to_html_inline(stripped.lstrip('-').strip())}</li>")
        elif stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{md_to_html_inline(stripped)}</p>")
        elif in_list:
            html_lines.append("</ul>")
            in_list = False

    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)


def build_cv_links(cv_data: dict) -> list:
    """Build header link list from website, custom_connections, and social_networks."""
    links = []
    if website := cv_data.get("website"):
        links.append({
            "url": website,
            "label_it": "Sito Web",
            "label_en": "Website",
            "emoji": "🌐",
        })

    for conn in cv_data.get("custom_connections") or []:
        placeholder = conn.get("placeholder", "")
        url = conn.get("url", "")
        if url and placeholder:
            links.append({
                "url": url,
                "label_it": conn.get("label_it", placeholder),
                "label_en": conn.get("label_en", placeholder),
                "emoji": conn.get("emoji", "🔗"),
            })

    networks = {n["network"].lower(): n for n in cv_data.get("social_networks") or []}
    for net in ["linkedin", "github"]:
        if net not in networks:
            continue
        username = networks[net].get("username", "")
        if not username:
            continue
        if net == "linkedin":
            links.append({
                "url": f"https://linkedin.com/in/{username}",
                "label_it": "LinkedIn",
                "label_en": "LinkedIn",
                "emoji": "🔗",
            })
        elif net == "github":
            links.append({
                "url": f"https://github.com/{username}",
                "label_it": "GitHub",
                "label_en": "GitHub",
                "emoji": "💻",
            })
    return links


def render_html(cv_it, cv_en, locale_it, locale_en, philosophy):
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["md"] = md_to_html
    env.filters["slug"] = slugify
    env.globals["format_date_range"] = format_date_range
    template = env.get_template("index.html.j2")
    return template.render(
        cv_it=cv_it,
        cv_en=cv_en,
        locale_it=locale_it,
        locale_en=locale_en,
        links=build_cv_links(cv_it),
        philosophy=philosophy,
    )


def main():
    """Generate index.html from YAML source files."""
    print("Loading CV data from YAML...")
    cv_it = load_cv_data("it")
    cv_en = load_cv_data("en")
    locale_it = load_locale("it")
    locale_en = load_locale("en")
    philosophy = load_cv_as_code_philosophy()

    print("Generating HTML...")
    html = render_html(cv_it, cv_en, locale_it, locale_en, philosophy)

    output_path = SITE_DIR / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ Generated {output_path}")

    favicon_src = ROOT_DIR / "favicon.svg"
    favicon_dst = SITE_DIR / "assets" / "favicon-cv.svg"
    favicon_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(favicon_src, favicon_dst)
    print(f"✓ Copied favicon to {favicon_dst}")


if __name__ == "__main__":
    main()
