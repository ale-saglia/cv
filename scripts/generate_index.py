"""Generate integrated site/index.html from YAML source files."""

import re
import shutil
import yaml
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
SITE_DIR = ROOT_DIR / "site"


def load_cv_as_code_philosophy() -> str:
    """Extract CV-as-Code philosophy description from README.md and format as HTML."""
    readme_path = ROOT_DIR / "README.md"
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract everything from Rationale section to the next ## heading
        rationale_match = re.search(r"##\s+.*?Rationale.*?\n\n(.*?)(?=\n##\s|\Z)", content, re.DOTALL)
        if not rationale_match:
            return "<p>This curriculum is built with code, not proprietary tools.</p>"
        
        rationale_text = rationale_match.group(1).strip()
        
        # Convert markdown to HTML
        html = md_to_html(rationale_text)
        
        return html
    except Exception as e:
        print(f"Error loading philosophy: {e}")
        pass
    
    # Fallback text
    return "<p>This curriculum is built with code, not proprietary tools.</p>"


def load_locale(lang: str) -> dict:
    """Load locale data for month names."""
    locale_path = SRC_DIR / lang / "locale.yaml"
    with open(locale_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("locale", {})


def load_cv_data(lang: str) -> dict:
    """Load CV data from master.yaml."""
    yaml_path = SRC_DIR / lang / "master.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return data["cv"]


def format_date_range(start_date, end_date, lang="it", month_abbrs=None):
    """Format date range for display with localized month names.
    
    Converts dates from YYYY-MM format to "Mon YYYY" format (e.g., "Sept 2016").
    """
    if month_abbrs is None:
        month_abbrs = []
    
    def parse_date(date_str):
        """Parse YYYY-MM or YYYY-MM-DD format date string."""
        if not isinstance(date_str, str) or not date_str:
            return date_str
        
        parts = date_str.split("-")
        if len(parts) >= 2:
            try:
                year = parts[0]
                month_num = int(parts[1]) - 1  # 0-indexed for month_abbrs
                if 0 <= month_num < len(month_abbrs):
                    month = month_abbrs[month_num]
                    return f"{month} {year}"
            except (ValueError, IndexError):
                pass
        return date_str
    
    start = parse_date(start_date) if isinstance(start_date, str) else ""
    
    if end_date == "present" or end_date is None:
        end = "in corso" if lang == "it" else "ongoing"
    elif isinstance(end_date, str):
        end = parse_date(end_date)
    else:
        end = str(end_date.year) if hasattr(end_date, 'year') else str(end_date)
    
    return f"{start} - {end}" if start and end else f"{start}{end}".strip()


def escape_html(text):
    """Escape HTML special characters."""
    if not isinstance(text, str):
        return str(text)
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))


def md_to_html(text):
    """Convert markdown formatting to HTML."""
    if not isinstance(text, str):
        return str(text)
    
    lines = text.split('\n')
    html_lines = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        
        # Handle headings (###, ##, #)
        if stripped.startswith('###'):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            heading_text = stripped.lstrip('#').strip()
            heading_text = md_to_html_inline(heading_text)
            html_lines.append(f'<h3>{heading_text}</h3>')
        elif stripped.startswith('##'):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            heading_text = stripped.lstrip('#').strip()
            heading_text = md_to_html_inline(heading_text)
            html_lines.append(f'<h2>{heading_text}</h2>')
        elif stripped.startswith('#'):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            heading_text = stripped.lstrip('#').strip()
            heading_text = md_to_html_inline(heading_text)
            html_lines.append(f'<h1>{heading_text}</h1>')
        # Handle bullet points
        elif stripped.startswith('-'):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            item_text = stripped.lstrip('-').strip()
            item_text = md_to_html_inline(item_text)
            html_lines.append(f'<li>{item_text}</li>')
        # Handle paragraph breaks and content
        elif stripped:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            # Process inline markdown
            paragraph_text = md_to_html_inline(stripped)
            html_lines.append(f'<p>{paragraph_text}</p>')
        elif in_list:
            # Empty line while in list - close list
            html_lines.append('</ul>')
            in_list = False
    
    # Close any open list
    if in_list:
        html_lines.append('</ul>')
    
    return '\n'.join(html_lines)


def md_to_html_inline(text):
    """Convert inline markdown formatting to HTML."""
    if not isinstance(text, str):
        return str(text)
    
    # Escape HTML first
    text = escape_html(text)
    
    # Handle **bold**
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # Handle *italic*
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    
    return text


def safe_list(value, filter_empty=True):
    """Convert value to list safely. Remove None/empty values if filter_empty=True."""
    if value is None:
        return []
    if not isinstance(value, list):
        return [value] if value else []
    if filter_empty:
        return [item for item in value if item]
    return value


def find_section_key(sections: dict, *possible_keys) -> str | None:
    """Find which key exists in sections dict from list of possibilities."""
    for key in possible_keys:
        if key in sections:
            return key
    return None


def render_text(text: str) -> str:
    """Render text with HTML escaping and markdown conversion."""
    return md_to_html(escape_html(text))


def slugify(text: str) -> str:
    """Convert text to URL-safe slug for anchor IDs."""
    text = text.lower()
    # Replace spaces and special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text


def render_entry_block(entry: dict, field_map: dict, lang: str, month_abbrs: list) -> str:
    """Render a single entry block (experience, volunteering, education).
    
    field_map: dict with keys:
        - 'title_main': main title field name (e.g., 'position', 'degree')
        - 'title_secondary': optional subtitle/details field (e.g., 'area'), or None if unused
        - 'org': organization field name (e.g., 'company', 'institution')
        - 'include_location': whether to append location to org (True for experience/volunteering)
    """
    html = '        <div class="cv-entry">\n'
    
    # Main title
    title_main_key = field_map.get('title_main', '')
    title_secondary_key = field_map.get('title_secondary')

    title_main = entry.get(title_main_key, '')
    title_secondary = entry.get(title_secondary_key, '') if title_secondary_key else ''
    
    if title_main:
        html += f'        <h2><strong>{escape_html(title_main)}</strong>'
        if title_secondary:
            html += f' in {escape_html(title_secondary)}'
        html += '</h2>\n'
    
    # Organization/company and dates
    org_key = field_map.get('org', '')
    org = entry.get(org_key, '')
    location = entry.get('location', '')
    start = entry.get('start_date', '')
    end = entry.get('end_date', '')
    date_field = entry.get('date', '')
    include_location = field_map.get('include_location', False)
    
    if org or start or end or date_field:
        if date_field and not start and not end:
            date_str = date_field
        else:
            date_str = format_date_range(start, end, lang, month_abbrs)
        
        org_str = f'<strong>{escape_html(org)}</strong>'
        if location and include_location:
            org_str += f', {escape_html(location)}'
        
        html += f'        <div class="cv-meta">\n          <div>{org_str}</div>\n'
        if date_str:
            html += f'          <div class="cv-date"><em>{date_str}</em></div>\n'
        html += '        </div>\n'
    
    # Summary
    summary = entry.get('summary', '')
    if summary:
        html += f'        <p>{render_text(summary)}</p>\n'
    
    # Highlights (bullet points)
    highlights = entry.get('highlights', [])
    if highlights:
        html += '        <ul>\n'
        for highlight in safe_list(highlights):
            html += f'          <li>{render_text(highlight)}</li>\n'
        html += '        </ul>\n'
    
    html += '        </div>\n\n'
    return html


def generate_cv_html(lang: str, cv_data: dict, locale: dict | None = None) -> str:
    """Generate HTML section for CV in given language."""
    
    if locale is None:
        locale = {}
    
    month_abbrs = locale.get("month_abbreviations", [])
    cv_id = f"cv-{lang}"
    cv_class = "cv-content active" if lang == "it" else "cv-content"
    
    html = f'      <!-- {lang.upper()} CV -->\n'
    html += f'      <section id="{cv_id}" class="{cv_class}">\n'
    
    # Links section with responsive dropdown
    location = cv_data.get("location", "")
    html += '        <div class="cv-header-links">\n'
    html += f'          <span class="cv-location">📍 {escape_html(location)}</span>\n'
    
    # Build links list
    website_url = cv_data.get("website", "")
    custom_links = []
    
    if website_url:
        custom_links.append({
            "name": "website",
            "url": website_url,
            "label_it": "Sito Web",
            "label_en": "Website",
            "emoji": "🌐",
        })
    
    # Load custom connections from YAML (with labels for HTML generation)
    for custom_conn in safe_list(cv_data.get("custom_connections", [])):
        placeholder = custom_conn.get("placeholder", "")
        url = custom_conn.get("url", "")
        label_it = custom_conn.get("label_it", placeholder)
        label_en = custom_conn.get("label_en", placeholder)
        
        if url and placeholder:
            custom_links.append({
                "name": placeholder,
                "url": url,
                "label_it": label_it,
                "label_en": label_en,
                "emoji": custom_conn.get("emoji", "🔗"),
            })
    
    # Social networks from YAML
    network_order = ["linkedin", "github"]
    networks_dict = {n["network"].lower(): n for n in cv_data.get("social_networks", [])}
    
    for net_name in network_order:
        if net_name not in networks_dict:
            continue
        network = networks_dict[net_name]
        username = network.get("username", "")
        if not username:
            continue
        
        if net_name == "linkedin":
            custom_links.append({
                "name": "linkedin",
                "url": f"https://linkedin.com/in/{username}",
                "label_it": "LinkedIn",
                "label_en": "LinkedIn",
                "emoji": "🔗",
            })
        elif net_name == "github":
            custom_links.append({
                "name": "github",
                "url": f"https://github.com/{username}",
                "label_it": "GitHub",
                "label_en": "GitHub",
                "emoji": "💻",
            })
    
    # Inline links group (shown on wide screens)
    html += '          <div class="cv-links-group" id="cv-links-group-' + lang + '">\n'
    for custom in custom_links:
        label = custom["label_it"] if lang == "it" else custom["label_en"]
        url = custom["url"]
        emoji = custom["emoji"]
        html += f'            <a href="{url}" target="_blank" rel="noopener">{emoji} {label}</a>\n'
    html += '          </div>\n'
    
    # Dropdown menu (shown on narrow screens)
    dropdown_label = "Link" if lang == "it" else "Links"
    html += '          <div class="cv-links-dropdown" id="cv-links-dropdown-' + lang + '" aria-label="Links menu">\n'
    html += f'            <button class="cv-links-dropdown-trigger" aria-expanded="false" aria-haspopup="true">{dropdown_label} <span class="cv-links-dropdown-arrow">▼</span></button>\n'
    html += '            <div class="cv-links-dropdown-menu">\n'
    for custom in custom_links:
        label = custom["label_it"] if lang == "it" else custom["label_en"]
        url = custom["url"]
        emoji = custom["emoji"]
        html += f'              <a href="{url}" target="_blank" rel="noopener" class="cv-links-dropdown-item">{emoji} {label}</a>\n'
    html += '            </div>\n'
    html += '          </div>\n'
    
    html += '        </div>\n\n'
    
    # Sections
    sections = cv_data.get("sections", {})
    
    # Summary / In breve
    summary_key = find_section_key(sections, "summary", "In breve")
    if summary_key:
        section_title = "Summary" if lang == "en" else "In breve"
        html += f'        <p class="cv-summary-title"><strong>{section_title}</strong></p>\n'
        for item in safe_list(sections[summary_key]):
            if isinstance(item, str):
                html += f'        <p>{render_text(item)}</p>\n'
        html += '\n'
    
    # Generate table of contents with auto-generated slugs from titles
    toc_items = []
    section_checks = [
        ("experience", "Esperienza lavorativa", "Experience", "Esperienza lavorativa"),
        ("education", "formazione", "Education", "Formazione"),
        ("volunteering", "volontariato", "Volunteering", "Volontariato"),
        ("certification", "certificati", "Certifications", "Certificati"),
        ("selected_honors", "riconoscimenti", "Awards & Recognition", "Riconoscimenti"),
        ("skills", "competenze", "Skills", "Competenze"),
    ]
    
    for section_key, section_key_it, title_en, title_it in section_checks:
        if find_section_key(sections, section_key, section_key_it):
            title = title_en if lang == "en" else title_it
            anchor_id = slugify(title)
            toc_items.append((title, anchor_id))
    
    if toc_items:
        html += '        <nav class="cv-toc">\n'
        for title, anchor_id in toc_items:
            html += f'          <a href="#{anchor_id}">{title}</a>\n'
        html += '        </nav>\n\n'
    
    # Experience
    exp_key = find_section_key(sections, "experience", "Esperienza lavorativa")
    if exp_key:
        section_title = "Experience" if lang == "en" else "Esperienza lavorativa"
        section_id = slugify(section_title)
        html += f'        <h2 id="{section_id}">{section_title}</h2>\n\n'
        for exp in sections[exp_key]:
            html += render_entry_block(
                exp,
                {'title_main': 'position', 'title_secondary': None, 'org': 'company', 'include_location': True},
                lang,
                month_abbrs
            )

    # Education
    edu_key = find_section_key(sections, "education", "formazione")
    if edu_key:
        section_title = "Education" if lang == "en" else "Formazione"
        section_id = slugify(section_title)
        html += f'        <h2 id="{section_id}">{section_title}</h2>\n\n'
        for edu in sections[edu_key]:
            html += render_entry_block(
                edu,
                {'title_main': 'degree', 'title_secondary': 'area', 'org': 'institution'},
                lang,
                month_abbrs
            )

    # Volunteering
    vol_key = find_section_key(sections, "volunteering", "volontariato")
    if vol_key:
        section_title = "Volunteering" if lang == "en" else "Volontariato"
        section_id = slugify(section_title)
        html += f'        <h2 id="{section_id}">{section_title}</h2>\n\n'
        for vol in sections[vol_key]:
            html += render_entry_block(
                vol,
                {'title_main': 'position', 'title_secondary': None, 'org': 'company', 'include_location': True},
                lang,
                month_abbrs
            )

    # Certifications
    cert_key = find_section_key(sections, "certification", "certificati")
    if cert_key:
        section_title = "Certifications" if lang == "en" else "Certificati"
        section_id = slugify(section_title)
        html += f'        <h2 id="{section_id}">{section_title}</h2>\n\n'
        for cert in sections[cert_key]:
            label = cert.get("label", "")
            details = cert.get("details", "")
            if label:
                html += '        <div class="cv-entry cv-entry-minimal">\n'
                html += f'        <p><strong>{escape_html(label)}:</strong> {escape_html(details)}</p>\n'
                html += '        </div>\n'
        html += '\n'
    
    # Awards
    awards_key = find_section_key(sections, "selected_honors", "riconoscimenti")
    if awards_key:
        section_title = "Awards & Recognition" if lang == "en" else "Riconoscimenti"
        section_id = slugify(section_title)
        html += f'        <h2 id="{section_id}">{section_title}</h2>\n\n'
        for award in sections[awards_key]:
            bullet = award.get("bullet", "")
            if bullet:
                html += '        <div class="cv-entry cv-entry-minimal">\n'
                html += f'          <p>{render_text(bullet)}</p>\n'
                html += '        </div>\n'
        html += '\n'
    
    # Skills
    skills_key = find_section_key(sections, "skills", "competenze")
    if skills_key:
        section_title = "Skills" if lang == "en" else "Competenze"
        section_id = slugify(section_title)
        html += f'        <h2 id="{section_id}">{section_title}</h2>\n\n'
        for skill in sections[skills_key]:
            label = skill.get("label", "")
            details = skill.get("details", "")
            if label:
                html += '        <div class="cv-entry cv-entry-minimal">\n'
                html += f'        <p><strong>{escape_html(label)}:</strong> {escape_html(details)}</p>\n'
                html += '        </div>\n'
    
    html += '      </section>\n'
    return html


def generate_full_html(cv_it: dict, cv_en: dict, locale_it: dict | None = None, locale_en: dict | None = None, philosophy: str = "") -> str:
    """Generate complete HTML file."""
    
    html = '''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="theme-color" content="#ffffff" />
  <meta name="color-scheme" content="light dark" />
  <script>
    (function(){var l=localStorage.getItem("cv-lang");if(l==="en"||l==="it")document.documentElement.lang=l;})();
  </script>
  <title>Alessandro Saglia - CV</title>
  <meta name="description" content="Alessandro Saglia - Curriculum Vitae. Digital Governance, Healthcare Systems, Data Interoperability." />
  <style>
    :root {
      --bg: #ffffff;
      --text: #1b1f23;
      --muted: #5b636a;
      --line: #e6e8eb;
      --link: #0b57d0;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      transition: background-color 0.2s, color 0.2s;
    }

    .wrap {
      width: min(760px, 92vw);
      margin: 0 auto;
    }

    /* Navigation Bar */
    .site-nav {
      display: flex;
      flex-wrap: nowrap;
      justify-content: flex-start;
      gap: 1.5rem;
      padding: 1.2rem 0;
      border-bottom: 1px solid var(--line);
      margin-bottom: 0.7rem;
      align-items: center;
    }

    .nav-title {
      margin: 0;
      font-size: 1.8rem;
      font-weight: 600;
      letter-spacing: -0.5px;
      flex: 1;
      text-align: left;
      white-space: normal;
      min-width: 0;
    }

    .nav-title a {
      color: var(--text);
      text-decoration: none;
    }

    .nav-title a:hover {
      color: var(--link);
    }

    .nav-controls {
      display: flex;
      flex-wrap: nowrap;
      justify-content: flex-end;
      gap: 1rem;
      align-items: center;
      flex-shrink: 1;
      min-width: 0;
      overflow: visible;
    }

    .lang-switcher {
      display: flex;
      gap: 0.5rem;
    }

    .lang-btn {
      background: transparent;
      border: 1px solid var(--line);
      padding: 0.4rem 0.6rem;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 0.9rem;
      cursor: pointer;
      color: var(--text);
      border-radius: 3px;
      transition: all 0.2s;
    }

    .lang-btn.active {
      background: var(--link);
      color: white;
      border-color: var(--link);
    }

    .lang-btn:not(.active):hover {
      border-color: var(--link);
      color: var(--link);
    }

    /* Dropdown */
    .dropdown {
      position: relative;
      margin-left: auto;
    }

    .dropdown-trigger {
      background: transparent;
      border: 1px solid var(--line);
      padding: 0.4rem 0.8rem;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 0.9rem;
      cursor: pointer;
      color: var(--text);
      border-radius: 3px;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.2s;
    }

    .dropdown-trigger:hover {
      border-color: var(--link);
      color: var(--link);
    }

    .dropdown-trigger::after {
      content: "▼";
      font-size: 0.6rem;
    }

    .dropdown-menu {
      position: absolute;
      top: 100%;
      right: 0;
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 3px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      margin-top: 0.5rem;
      z-index: 1000;
      display: none;
      min-width: 150px;
    }

    .dropdown-menu.active {
      display: block;
    }

    .dropdown-menu a {
      display: block;
      padding: 0.7rem 1rem;
      color: var(--link);
      text-decoration: none;
      border-bottom: 1px solid var(--line);
      font-size: 0.9rem;
      transition: background-color 0.2s;
    }

    .dropdown-menu a:last-child {
      border-bottom: none;
    }

    .dropdown-menu a:hover {
      background: var(--line);
    }

    /* Main Content */
    main {
      margin-bottom: 2rem;
    }

    /* CV Content */
    .cv-content {
      display: none;
    }

    .cv-content.active {
      display: block;
    }

    .cv-content h1 {
      margin: 1.5rem 0 1rem;
      font-size: 1.3rem;
      font-weight: 600;
      border-bottom: 1px solid var(--line);
      padding-bottom: 0.5rem;
    }

    .cv-content h1:first-of-type {
      margin-top: 0;
    }

    .cv-content h2 {
      margin: 0 0 0.5rem;
      font-size: 1.1rem;
      font-weight: 600;
    }

    .cv-content h2[id] {
      margin: 2.5rem 0 1.5rem;
      border-bottom: 1px solid var(--line);
      padding-bottom: 0.5rem;
      font-size: 1.2rem;
    }

    .cv-content h2[id]:first-of-type {
      margin-top: 1.5rem;
    }

    .cv-entry {
      margin-bottom: 1rem;
      border-bottom: 1px solid var(--line);
    }

    .cv-entry:last-child {
      margin-bottom: 0;
      border-bottom: none;
    }

    .cv-entry-minimal {
      border-bottom: none;
    }

    .cv-entry-minimal:last-child {
      border-bottom: 1px solid var(--line);
    }

    /* Date alignment */
    .cv-meta {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
    }

    .cv-date {
      text-align: right;
      flex-shrink: 0;
      white-space: nowrap;
    }

    .cv-content ul {
      margin: 0.5rem 0 1.5rem;
      padding-left: 1.5rem;
    }

    .cv-content li {
      margin: 0.4rem 0;
      line-height: 1.6;
    }

    .cv-content p {
      margin: 0.5rem 0;
      line-height: 1.7;
    }

    .cv-content strong {
      font-weight: 600;
    }

    .cv-content a {
      color: var(--link);
      text-decoration: none;
    }

    .cv-content a:hover {
      text-decoration: underline;
    }

    /* CV Links Container */
    .cv-header-links {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin: 0.2rem 0 1.5rem;
      font-size: 0.95rem;
      padding: 0;
      list-style: none;
    }

    .cv-location {
      margin: 0;
      padding: 0;
      white-space: nowrap;
    }

    /* Inline links group (shown on wider screens) */
    .cv-links-group {
      display: flex;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
      margin-left: auto;
    }

    .cv-links-group.hidden {
      display: none;
    }

    .cv-links-group a {
      color: var(--link);
      text-decoration: none;
      margin: 0;
      padding: 0;
      white-space: nowrap;
    }

    .cv-links-group a:hover {
      text-decoration: underline;
    }

    /* Dropdown menu (shown on narrow screens) */
    .cv-links-dropdown {
      display: none;
      position: relative;
      margin-left: auto;
    }

    .cv-links-dropdown.visible {
      display: block;
    }

    .cv-links-dropdown-trigger {
      background: none;
      border: none;
      color: var(--link);
      font-size: 0.95rem;
      font-family: inherit;
      cursor: pointer;
      padding: 0;
      margin: 0;
      text-decoration: none;
      transition: text-decoration 0.15s ease;
      font-weight: normal;
      display: flex;
      align-items: center;
      gap: 0.3rem;
    }

    .cv-links-dropdown-arrow {
      display: inline-block;
      font-size: 0.8rem;
      transition: transform 0.2s ease;
      line-height: 1;
    }

    .cv-links-dropdown-trigger[aria-expanded="true"] .cv-links-dropdown-arrow {
      transform: rotate(180deg);
    }

    .cv-links-dropdown-trigger:hover {
      text-decoration: underline;
    }

    .cv-links-dropdown-trigger:focus {
      outline: 2px solid var(--link);
      outline-offset: 2px;
      border-radius: 2px;
    }

    .cv-links-dropdown-menu {
      display: none;
      position: absolute;
      top: 100%;
      right: 0;
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 4px;
      margin-top: 0.5rem;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      min-width: 160px;
      z-index: 100;
      flex-direction: column;
    }

    @media (prefers-color-scheme: dark) {
      .cv-links-dropdown-menu {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
      }
    }

    .cv-links-dropdown-menu.open {
      display: flex;
    }

    .cv-links-dropdown-item {
      display: block;
      padding: 0.6rem 1rem;
      color: var(--link);
      text-decoration: none;
      transition: background 0.1s ease;
    }

    .cv-links-dropdown-item:hover {
      background: var(--line);
      text-decoration: none;
    }

    .cv-links-dropdown-item:first-child {
      border-radius: 3px 3px 0 0;
    }

    .cv-links-dropdown-item:last-child {
      border-radius: 0 0 3px 3px;
    }

    .cv-toc {
      display: flex;
      flex-wrap: wrap;
      gap: 1.5rem;
      justify-content: center;
      margin: 1.5rem 0;
      padding: 1rem 0;
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      font-size: 0.9rem;
    }

    .cv-toc a {
      color: var(--link);
      text-decoration: none;
    }

    .cv-toc a:hover {
      text-decoration: underline;
    }
    .site-footer {
      margin-top: 3rem;
      padding: 1.5rem 0;
      border-top: 1px solid var(--line);
      text-align: center;
      color: var(--muted);
      font-size: 0.9rem;
      width: 100%;
      box-sizing: border-box;
    }

    .site-footer a {
      color: var(--link);
      text-decoration: none;
    }

    .site-footer a:hover {
      text-decoration: underline;
    }

    .site-footer.hidden {
      display: none;
    }

    /* Back to Top */
    .back-to-top {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.3s, visibility 0.3s;
      background: var(--link);
      color: white;
      padding: 0.6rem 0.9rem;
      border-radius: 3px;
      text-decoration: none;
      font-size: 0.9rem;
      z-index: 999;
      font-family: Georgia, "Times New Roman", serif;
    }

    .back-to-top.visible {
      opacity: 1;
      visibility: visible;
    }

    .back-to-top:hover {
      color: white;
      text-decoration: underline;
    }

    /* Dark Mode */
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0d1117;
        --text: #e6edf3;
        --muted: #8b949e;
        --line: #30363d;
        --link: #58a6ff;
      }

      .dropdown-menu {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      }
    }

    /* Responsive */
    @media (max-width: 768px) {
      .site-nav {
        flex-wrap: wrap;
        gap: 0.8rem;
      }

      .nav-title {
        font-size: 1.2rem;
        order: 2;
        width: 100%;
        text-align: center;
        margin-top: 0.6rem;
        flex: auto;
      }

      .nav-controls {
        order: 1;
        width: 100%;
        justify-content: flex-start;
        flex-wrap: nowrap;
      }
    }

    /* CV-as-code button */
    .cv-as-code-btn {
      background: transparent;
      border: none;
      padding: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 0.9rem;
      cursor: pointer;
      color: var(--link);
      transition: all 0.2s;
      font-weight: 600;
      text-decoration: none;
      border-bottom: 1px solid transparent;
    }

    .cv-as-code-btn:hover {
      border-bottom-color: var(--link);
    }

    .cv-as-code-btn:focus {
      outline: none;
    }

    /* Modal Styles */
    .cv-as-code-modal {
      display: none;
      position: fixed;
      z-index: 2000;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      animation: fadeIn 0.2s ease-in;
    }

    .cv-as-code-modal.active {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .cv-as-code-modal-content {
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 8px;
      max-width: 500px;
      width: 90vw;
      max-height: 70vh;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
      animation: slideUp 0.3s ease-out;
      position: relative;
      display: flex;
      flex-direction: column;
    }

    .cv-as-code-modal-close {
      position: absolute;
      top: 1rem;
      right: 1rem;
      background: transparent;
      border: none;
      font-size: 1.5rem;
      cursor: pointer;
      color: var(--text);
      padding: 0;
      width: 2rem;
      height: 2rem;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: color 0.2s;
    }

    .cv-as-code-modal-close:hover {
      color: var(--link);
    }

    .cv-as-code-modal h2 {
      margin-top: 0;
      margin-bottom: 0;
      font-size: 1.5rem;
      color: var(--text);
      padding: 2rem 2rem 1rem 2rem;
      flex-shrink: 0;
    }

    .cv-as-code-philosophy {
      color: var(--text);
      line-height: 1.4;
      padding: 0 2rem;
      overflow-y: auto;
      flex: 1;
    }

    .cv-as-code-philosophy p {
      margin: 0.4rem 0 0.1rem 0;
    }

    .cv-as-code-philosophy p:first-child {
      margin-top: 0;
    }

    .cv-as-code-philosophy h3 {
      font-size: 1.1rem;
      font-weight: 600;
      margin: 0.8rem 0 0 0;
      color: var(--text);
    }

    .cv-as-code-philosophy h3 + p {
      margin-top: 0.1rem;
      margin-bottom: 0.1rem;
    }

    .cv-as-code-philosophy h3 + ul {
      margin-top: 0;
    }

    .cv-as-code-philosophy p + ul {
      margin-top: 0;
    }

    .cv-as-code-philosophy ul {
      margin: 0.3rem 0;
      padding-left: 1.5rem;
    }

    .cv-as-code-philosophy li {
      margin: 0.2rem 0;
    }

    .cv-as-code-modal-footer {
      display: flex;
      gap: 1rem;
      padding: 1.5rem 2rem 2rem 2rem;
      justify-content: flex-end;
      flex-shrink: 0;
      border-top: 1px solid var(--line);
    }

    .cv-as-code-modal-btn {
      padding: 0.6rem 1.2rem;
      border-radius: 4px;
      border: 1px solid var(--line);
      font-family: Georgia, "Times New Roman", serif;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.2s;
    }

    .cv-as-code-modal-btn.primary {
      background: var(--link);
      color: white;
      border-color: var(--link);
    }

    .cv-as-code-modal-btn.primary:hover {
      opacity: 0.9;
    }

    .cv-as-code-modal-btn.secondary {
      background: transparent;
      color: var(--text);
    }

    .cv-as-code-modal-btn.secondary:hover {
      border-color: var(--link);
      color: var(--link);
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    @keyframes slideUp {
      from {
        transform: translateY(20px);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }

    /* Full-width footer wrapper */
    .site-footer-wrapper {
      width: 100vw;
      position: relative;
      left: 50%;
      right: 50%;
      margin-left: -50vw;
      margin-right: -50vw;
    }
    button:focus,
    a:focus {
      outline: 2px solid var(--link);
      outline-offset: 2px;
      border-radius: 2px;
    }


  </style>
  <link rel="icon" href="assets/favicon-cv.svg" type="image/svg+xml" />
</head>
<body id="top">
  <div class="wrap">
    <nav class="site-nav" aria-label="Primary">
      <h1 class="nav-title"><a href="#top">Alessandro Saglia</a></h1>
      <div class="nav-controls">
        <button class="cv-as-code-btn" id="cv-as-code-btn" title="Learn about CV-as-code philosophy">CV-as-code</button>
        <div class="lang-switcher">
          <button class="lang-btn active" id="lang-it" aria-label="Seleziona italiano">IT</button>
          <button class="lang-btn" id="lang-en" aria-label="Select English">EN</button>
        </div>
        <div class="dropdown">
          <button class="dropdown-trigger" aria-label="Download CV">Download</button>
          <div class="dropdown-menu" id="dropdown-menu">
            <a id="download-pdf" href="it/master/CV_it_master.pdf" download="CV_Saglia_Alessandro.pdf">PDF</a>
            <a id="download-md" href="it/master/CV_it_master.md" download="CV_Saglia_Alessandro.md">Markdown</a>
          </div>
        </div>
      </div>
    </nav>

    <main>
'''
    
    # Add Italian CV
    html += generate_cv_html("it", cv_it, locale_it)
    
    # Add English CV
    html += generate_cv_html("en", cv_en, locale_en)
    
    # Close main and wrap, add full-width footer
    html += '''
    </main>
  </div>

  <!-- Full-width footer -->
  <div class="site-footer-wrapper">
    <footer id="footer-it" class="site-footer">
      <p>Realizzato con HTML, principi e dedizione • Nessun tracciamento. Nessun cookie. <a href="https://github.com/ale-saglia/cv" target="_blank" rel="noopener">Aperto per trasparenza</a></p>
    </footer>
    <footer id="footer-en" class="site-footer hidden">
      <p>Built with HTML, principles, and care • No tracking. No cookies. <a href="https://github.com/ale-saglia/cv" target="_blank" rel="noopener">Open for transparency</a></p>
    </footer>
  </div>'''
    
    # Add back-to-top and scripting
    philosophy_text = philosophy if philosophy else "<p>This curriculum is built with code, not proprietary tools.</p>"
    html += '''
  <a href="#top" class="back-to-top" id="back-to-top">↑ Top</a>

  <!-- CV-as-code Modal -->
  <div class="cv-as-code-modal" id="cv-as-code-modal">
    <div class="cv-as-code-modal-content">
      <button class="cv-as-code-modal-close" id="cv-as-code-modal-close">&times;</button>
      <h2>CV-as-code Rationale</h2>
      <div class="cv-as-code-philosophy">'''
    html += philosophy_text
    html += '''</div>
      <div class="cv-as-code-modal-footer">
        <button class="cv-as-code-modal-btn secondary" id="cv-as-code-modal-close-btn">Close</button>
        <a href="https://github.com/ale-saglia/cv" target="_blank" rel="noopener" class="cv-as-code-modal-btn primary">Learn More →</a>
      </div>
    </div>
  </div>

  <script>
    // Responsive CV links dropdown logic
    function setupCVLinksDropdown(linksGroup, linksDropdown) {
      if (!linksGroup || !linksDropdown) return;

      const trigger = linksDropdown.querySelector(".cv-links-dropdown-trigger");
      const menu = linksDropdown.querySelector(".cv-links-dropdown-menu");
      const items = menu ? Array.from(menu.querySelectorAll("a")) : [];

      if (!trigger || !menu) return;

      let lastExpanded = null;
      let requiredWidth = null;
      let isCalculatingWidth = false;

      function calculateRequiredWidth() {
        if (isCalculatingWidth) return;
        isCalculatingWidth = true;

        try {
          const wasHidden = linksGroup.classList.contains("hidden");
          linksGroup.classList.remove("hidden");

          // Calculate total width needed
          let totalWidth = 0;
          
          // Add location width
          const location = linksGroup.parentElement.querySelector(".cv-location");
          if (location) {
            totalWidth += location.scrollWidth;
          }

          // Add links group + gaps
          const links = linksGroup.querySelectorAll("a");
          links.forEach(link => {
            totalWidth += link.scrollWidth;
          });

          // Add gaps between items (read actual computed gap instead of assuming 1rem = 16px)
          const gapCount = (location ? 1 : 0) + links.length;
          const containerGap = parseFloat(getComputedStyle(linksGroup.parentElement).gap) || 16;
          totalWidth += gapCount * containerGap;

          // Add padding buffer (container padding, margins, and overflow safety)
          totalWidth += 40;

          requiredWidth = totalWidth;

          if (wasHidden) {
            linksGroup.classList.add("hidden");
          }
        } finally {
          isCalculatingWidth = false;
        }
      }

      function checkLayout() {
        const containerWidth = linksGroup.parentElement.clientWidth;

        if (requiredWidth === null) {
          calculateRequiredWidth();
        }

        const shouldExpand = containerWidth >= requiredWidth;

        if (lastExpanded === shouldExpand) return;
        lastExpanded = shouldExpand;

        if (shouldExpand) {
          // Show inline, hide dropdown
          linksGroup.classList.remove("hidden");
          linksDropdown.classList.remove("visible");
          menu.classList.remove("open");
          trigger.setAttribute("aria-expanded", "false");
        } else {
          // Hide inline, show dropdown
          linksGroup.classList.add("hidden");
          linksDropdown.classList.add("visible");
        }
      }

      // Dropdown toggle
      trigger.addEventListener("click", (e) => {
        e.preventDefault();
        menu.classList.toggle("open");
        trigger.setAttribute("aria-expanded", menu.classList.contains("open") ? "true" : "false");
      });

      // Close dropdown when clicking outside
      document.addEventListener("click", (e) => {
        if (!linksDropdown.contains(e.target)) {
          menu.classList.remove("open");
          trigger.setAttribute("aria-expanded", "false");
        }
      });

      // Close dropdown when item is selected
      items.forEach((item) => {
        item.addEventListener("click", () => {
          menu.classList.remove("open");
          trigger.setAttribute("aria-expanded", "false");
        });
      });

      // Initial layout check with delay to ensure fonts are loaded
      if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(() => {
          checkLayout();
        });
      } else {
        setTimeout(checkLayout, 100);
      }

      // Listen for window resize
      let resizeTimeout;
      window.addEventListener("resize", () => {
        clearTimeout(resizeTimeout);
        requiredWidth = null;
        lastExpanded = null;
        resizeTimeout = setTimeout(checkLayout, 150);
      });

      // Return interface for programmatic recalculation (language switching)
      return {
        recalculateLayout() {
          requiredWidth = null;
          lastExpanded = null;
          checkLayout();
        }
      };
    }

    // Initialize responsive links for both languages
    const cvLinksGroupIt = document.getElementById("cv-links-group-it");
    const cvLinksGroupEn = document.getElementById("cv-links-group-en");
    const cvLinksDropdownIt = document.getElementById("cv-links-dropdown-it");
    const cvLinksDropdownEn = document.getElementById("cv-links-dropdown-en");

    const cvLayoutIt = setupCVLinksDropdown(cvLinksGroupIt, cvLinksDropdownIt);
    const cvLayoutEn = setupCVLinksDropdown(cvLinksGroupEn, cvLinksDropdownEn);

    const langButtons = document.querySelectorAll(".lang-btn");
    const dropdownTrigger = document.querySelector(".dropdown-trigger");
    const dropdownMenu = document.getElementById("dropdown-menu");
    const cvSections = [document.getElementById("cv-it"), document.getElementById("cv-en")];
    const downloadPdf = document.getElementById("download-pdf");
    const downloadMd = document.getElementById("download-md");
    const footerIt = document.getElementById("footer-it");
    const footerEn = document.getElementById("footer-en");

    function getLanguage() {
      return localStorage.getItem("cv-lang") || "it";
    }

    function setLanguage(lang) {
      localStorage.setItem("cv-lang", lang);
      document.documentElement.lang = lang;
      
      // Update CV display
      cvSections.forEach(section => section.classList.remove("active"));
      document.getElementById(`cv-${lang}`).classList.add("active");
      
      // Update language buttons
      langButtons.forEach(btn => btn.classList.remove("active"));
      document.getElementById(`lang-${lang}`).classList.add("active");
      
      // Immediately recalculate responsive layout for current language (no debounce)
      if (lang === "it" && cvLayoutIt) {
        cvLayoutIt.recalculateLayout();
      } else if (lang === "en" && cvLayoutEn) {
        cvLayoutEn.recalculateLayout();
      }
      
      // Update download links to point to the selected language
      updateDownloadLinks(lang);

      // Update dropdown aria-label
      dropdownTrigger.setAttribute("aria-label", `Download CV in ${lang.toUpperCase()}`);
      
      // Update footer
      footerIt.classList.toggle("hidden", lang !== "it");
      footerEn.classList.toggle("hidden", lang !== "en");
      
    }

    function updateDownloadLinks(lang) {
      const langPath = lang === "it" ? "it/master" : "en/master";
      downloadPdf.href = `${langPath}/CV_${lang}_master.pdf`;
      downloadMd.href = `${langPath}/CV_${lang}_master.md`;
    }

    // Language switching
    langButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        setLanguage(btn.id.replace("lang-", ""));
        dropdownMenu.classList.remove("active");
      });
    });

    // Dropdown toggle
    dropdownTrigger.addEventListener("click", () => {
      dropdownMenu.classList.toggle("active");
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".dropdown")) {
        dropdownMenu.classList.remove("active");
      }
    });

    // Initialize with browser language detection
    function getInitialLanguage() {
      // Check if user has previously set a language preference
      const saved = localStorage.getItem("cv-lang");
      if (saved) return saved;
      
      // Detect browser language
      const browserLang = (navigator.language || "en").substring(0, 2);
      return browserLang === "it" ? "it" : "en";
    }
    
    const initialLang = getInitialLanguage();
    setLanguage(initialLang);

    // CV-as-code modal
    const cvAsCodeBtn = document.getElementById("cv-as-code-btn");
    const cvAsCodeModal = document.getElementById("cv-as-code-modal");
    const cvAsCodeModalClose = document.getElementById("cv-as-code-modal-close");
    const cvAsCodeModalCloseBtn = document.getElementById("cv-as-code-modal-close-btn");

    cvAsCodeBtn.addEventListener("click", () => {
      cvAsCodeModal.classList.add("active");
    });

    function closeModal() {
      cvAsCodeModal.classList.remove("active");
    }

    cvAsCodeModalClose.addEventListener("click", closeModal);
    cvAsCodeModalCloseBtn.addEventListener("click", closeModal);

    // Close modal when clicking outside the content
    cvAsCodeModal.addEventListener("click", (e) => {
      if (e.target === cvAsCodeModal) {
        closeModal();
      }
    });

    // Close modal with Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && cvAsCodeModal.classList.contains("active")) {
        closeModal();
      }
    });

    // Back to top
    const backToTop = document.getElementById("back-to-top");
    window.addEventListener("scroll", () => {
      if (window.scrollY > 300) {
        backToTop.classList.add("visible");
      } else {
        backToTop.classList.remove("visible");
      }
    });
  </script>
</body>
</html>
'''
    
    return html


def main():
    """Generate index.html from YAML source files."""
    print("Loading CV data from YAML...")
    cv_it = load_cv_data("it")
    cv_en = load_cv_data("en")
    locale_it = load_locale("it")
    locale_en = load_locale("en")
    philosophy = load_cv_as_code_philosophy()
    
    print("Generating HTML...")
    html = generate_full_html(cv_it, cv_en, locale_it, locale_en, philosophy)
    
    output_path = SITE_DIR / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✓ Generated {output_path}")
    
    # Copy favicon
    favicon_src = ROOT_DIR / "favicon.svg"
    favicon_dst = SITE_DIR / "assets" / "favicon-cv.svg"
    favicon_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(favicon_src, favicon_dst)
    print(f"✓ Copied favicon to {favicon_dst}")


if __name__ == "__main__":
    main()
