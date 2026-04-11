"""Generate integrated site/index.html from YAML source files."""

import yaml
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
SITE_DIR = ROOT_DIR / "site"


def load_cv_data(lang: str) -> dict:
    """Load CV data from master.yaml.
    
    WORKAROUND: Temporarily inject location from hardcoded values if ${SECRET_ADDRESS}
    is found. This is a temporary solution until a better approach is implemented.
    TODO: Move location configuration to separate config or environment variables.
    """
    yaml_path = SRC_DIR / lang / "master.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    cv = data["cv"]
    
    # Workaround: Replace ${SECRET_ADDRESS} with language-specific location
    if cv.get("location") == "${SECRET_ADDRESS}":
        cv["location"] = "Torino, Italia" if lang == "it" else "Turin, Italy"
    
    return cv


def format_date_range(start_date, end_date, lang="it"):
    """Format date range for display."""
    if isinstance(start_date, str):
        start = start_date
    else:
        start = ""
    
    if end_date == "present" or end_date is None:
        end = "in corso" if lang == "it" else "ongoing"
    elif isinstance(end_date, str):
        end = end_date
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
    """Convert simple markdown formatting to HTML."""
    if not isinstance(text, str):
        return str(text)
    
    import re
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


def find_section_key(sections: dict, *possible_keys) -> str:
    """Find which key exists in sections dict from list of possibilities."""
    for key in possible_keys:
        if key in sections:
            return key
    return None


def generate_cv_html(lang: str, cv_data: dict) -> str:
    """Generate HTML section for CV in given language."""
    
    cv_id = f"cv-{lang}"
    cv_class = "cv-content active" if lang == "it" else "cv-content"
    
    html = f'      <!-- {lang.upper()} CV -->\n'
    html += f'      <section id="{cv_id}" class="{cv_class}">\n'
    
    # Links section
    location = cv_data.get("location", "")
    html += '        <div class="cv-links">\n'
    html += f'          <span>📍 {escape_html(location)}</span>\n'
    
    # Social networks
    for network in cv_data.get("social_networks", []):
        if network["network"].lower() == "linkedin":
            username = network["username"]
            html += f'          <a href="https://linkedin.com/in/{username}" target="_blank" rel="noopener">🔗 LinkedIn</a>\n'
        elif network["network"].lower() == "github":
            username = network["username"]
            html += f'          <a href="https://github.com/{username}" target="_blank" rel="noopener">💻 GitHub</a>\n'
    
    html += '        </div>\n\n'
    
    # Sections
    sections = cv_data.get("sections", {})
    
    # Summary / In breve
    summary_key = find_section_key(sections, "summary", "In breve")
    if summary_key:
        section_title = "Summary" if lang == "en" else "In breve"
        html += f'        <h1>{section_title}</h1>\n'
        for item in safe_list(sections[summary_key]):
            if isinstance(item, str):
                html += f'        <p>{md_to_html(escape_html(item))}</p>\n'
        html += '\n'
    
    # Generate table of contents
    toc_items = []
    if find_section_key(sections, "experience", "Esperienza lavorativa"):
        toc_items.append(("Experience" if lang == "en" else "Esperienza lavorativa", "experience" if lang == "en" else "esperienza-lavorativa"))
    if find_section_key(sections, "education", "formazione"):
        toc_items.append(("Education" if lang == "en" else "Formazione", "education" if lang == "en" else "formazione"))
    if find_section_key(sections, "volunteering", "volontariato"):
        toc_items.append(("Volunteering" if lang == "en" else "Volontariato", "volunteering" if lang == "en" else "volontariato"))
    if find_section_key(sections, "certification", "certificati"):
        toc_items.append(("Certifications" if lang == "en" else "Certificati", "certifications" if lang == "en" else "certificati"))
    if find_section_key(sections, "selected_honors", "riconoscimenti"):
        toc_items.append(("Awards & Recognition" if lang == "en" else "Riconoscimenti", "awards-and-recognition" if lang == "en" else "riconoscimenti"))
    if find_section_key(sections, "skills", "competenze"):
        toc_items.append(("Skills" if lang == "en" else "Competenze", "skills" if lang == "en" else "competenze"))
    
    if toc_items:
        html += '        <nav class="cv-toc">\n'
        for title, anchor_id in toc_items:
            html += f'          <a href="#{anchor_id}">{title}</a>\n'
        html += '        </nav>\n\n'
    
    # Experience
    exp_key = find_section_key(sections, "experience", "Esperienza lavorativa")
    if exp_key:
        section_title = "Experience" if lang == "en" else "Esperienza lavorativa"
        section_id = "experience" if lang == "en" else "esperienza-lavorativa"
        html += f'        <h1 id="{section_id}">{section_title}</h1>\n\n'
        for exp in sections[exp_key]:
            html += '        <div class="cv-entry">\n'
            
            position = exp.get("position", "")
            company = exp.get("company", "")
            location = exp.get("location", "")
            start = exp.get("start_date", "")
            end = exp.get("end_date", "")
            date_field = exp.get("date", "")
            summary = exp.get("summary", "")
            highlights = exp.get("highlights", [])
            
            # Position title
            html += f'        <h2><strong>{escape_html(position)}</strong></h2>\n'
            
            # Company and dates
            if company or start or end or date_field:
                if date_field and not start and not end:
                    date_str = date_field
                else:
                    date_str = format_date_range(start, end, lang)
                comp_str = f'<strong>{escape_html(company)}</strong>'
                if location:
                    comp_str += f', {escape_html(location)}'
                html += f'        <div class="cv-meta">\n          <div>{comp_str}</div>\n'
                if date_str:
                    html += f'          <div class="cv-date"><em>{date_str}</em></div>\n'
                html += '        </div>\n'
            
            # Summary
            if summary:
                html += f'        <p>{md_to_html(escape_html(summary))}</p>\n'
            
            # Highlights (bullet points)
            if highlights:
                html += '        <ul>\n'
                for highlight in safe_list(highlights):
                    html += f'          <li>{md_to_html(escape_html(highlight))}</li>\n'
                html += '        </ul>\n'
            
            html += '        </div>\n\n'
    
    # Education
    edu_key = find_section_key(sections, "education", "formazione")
    if edu_key:
        section_title = "Education" if lang == "en" else "Formazione"
        section_id = "education" if lang == "en" else "formazione"
        html += f'        <h1 id="{section_id}">{section_title}</h1>\n\n'
        for edu in sections[edu_key]:
            html += '        <div class="cv-entry">\n'
            
            institution = edu.get("institution", "")
            degree = edu.get("degree", "")
            area = edu.get("area", "")
            start = edu.get("start_date", "")
            end = edu.get("end_date", "")
            summary = edu.get("summary", "")
            highlights = edu.get("highlights", [])
            
            # Title: Degree type + Area
            title = f'<strong>{escape_html(degree)}'
            if area:
                title += f' in {escape_html(area)}'
            title += '</strong>'
            html += f'        <h2>{title}</h2>\n'
            
            # Institution and dates
            if institution or start or end:
                date_str = format_date_range(start, end, lang) if (start or end) else ""
                inst_str = f'<strong>{escape_html(institution)}</strong>'
                html += f'        <div class="cv-meta">\n          <div>{inst_str}</div>\n'
                if date_str:
                    html += f'          <div class="cv-date"><em>{date_str}</em></div>\n'
                html += '        </div>\n'
            
            # Summary
            if summary:
                html += f'        <p>{md_to_html(escape_html(summary))}</p>\n'
            
            # Highlights
            if highlights:
                html += '        <ul>\n'
                for highlight in safe_list(highlights):
                    html += f'          <li>{md_to_html(escape_html(highlight))}</li>\n'
                html += '        </ul>\n'
            
            html += '        </div>\n\n'
    
    # Volunteering
    vol_key = find_section_key(sections, "volunteering", "volontariato")
    if vol_key:
        section_title = "Volunteering" if lang == "en" else "Volontariato"
        section_id = "volunteering" if lang == "en" else "volontariato"
        html += f'        <h1 id="{section_id}">{section_title}</h1>\n\n'
        for vol in sections[vol_key]:
            html += '        <div class="cv-entry">\n'
            
            position = vol.get("position", "")
            company = vol.get("company", "")
            start = vol.get("start_date", "")
            end = vol.get("end_date", "")
            date_field = vol.get("date", "")
            summary = vol.get("summary", "")
            highlights = vol.get("highlights", [])
            
            # Position title
            if position:
                html += f'        <h2><strong>{escape_html(position)}</strong></h2>\n'
            
            # Company and dates (same as experience)
            if company or start or end or date_field:
                if date_field and not start and not end:
                    date_str = date_field
                else:
                    date_str = format_date_range(start, end, lang)
                comp_str = f'<strong>{escape_html(company)}</strong>'
                html += f'        <div class="cv-meta">\n          <div>{comp_str}</div>\n'
                if date_str:
                    html += f'          <div class="cv-date"><em>{date_str}</em></div>\n'
                html += '        </div>\n'
            
            # Summary
            if summary:
                html += f'        <p>{md_to_html(escape_html(summary))}</p>\n'
            
            # Highlights
            if highlights:
                html += '        <ul>\n'
                for highlight in safe_list(highlights):
                    html += f'          <li>{md_to_html(escape_html(highlight))}</li>\n'
                html += '        </ul>\n'
            
            html += '        </div>\n\n'
    
    # Certifications
    cert_key = find_section_key(sections, "certification", "certificati")
    if cert_key:
        section_title = "Certifications" if lang == "en" else "Certificati"
        section_id = "certifications" if lang == "en" else "certificati"
        html += f'        <h1 id="{section_id}">{section_title}</h1>\n'
        for cert in sections[cert_key]:
            label = cert.get("label", "")
            details = cert.get("details", "")
            if label:
                html += f'        <p><strong>{escape_html(label)}:</strong> {escape_html(details)}</p>\n'
        html += '\n'
    
    # Awards
    awards_key = find_section_key(sections, "selected_honors", "riconoscimenti")
    if awards_key:
        section_title = "Awards & Recognition" if lang == "en" else "Riconoscimenti"
        section_id = "awards-and-recognition" if lang == "en" else "riconoscimenti"
        html += f'        <h1 id="{section_id}">{section_title}</h1>\n'
        html += '        <ul>\n'
        for award in sections[awards_key]:
            bullet = award.get("bullet", "")
            if bullet:
                html += f'          <li>{md_to_html(escape_html(bullet))}</li>\n'
        html += '        </ul>\n\n'
    
    # Skills
    skills_key = find_section_key(sections, "skills", "competenze")
    if skills_key:
        section_title = "Skills" if lang == "en" else "Competenze"
        section_id = "skills" if lang == "en" else "competenze"
        html += f'        <h1 id="{section_id}">{section_title}</h1>\n'
        for skill in sections[skills_key]:
            label = skill.get("label", "")
            details = skill.get("details", "")
            if label:
                html += f'        <p><strong>{escape_html(label)}:</strong> {escape_html(details)}</p>\n'
    
    html += '      </section>\n\n'
    return html


def generate_full_html(cv_it: dict, cv_en: dict) -> str:
    """Generate complete HTML file."""
    
    html = '''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="theme-color" content="#ffffff" />
  <meta name="color-scheme" content="light dark" />
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
      flex-wrap: wrap;
      justify-content: flex-start;
      gap: 0.8rem;
      padding: 1.2rem 0;
      border-bottom: 1px solid var(--line);
      margin-bottom: 0.7rem;
    }

    .nav-title {
      margin: 0;
      font-size: 1.8rem;
      font-weight: 600;
      letter-spacing: -0.5px;
      order: 2;
      width: 100%;
      text-align: center;
      margin-top: 0.6rem;
      white-space: normal;
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
      order: 1;
      width: 100%;
      justify-content: space-between;
      gap: 1.5rem;
      align-items: center;
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

    .cv-entry {
      margin-bottom: 1rem;
      border-bottom: 1px solid var(--line);
    }

    .cv-entry:last-child {
      margin-bottom: 0;
      border-bottom: none;
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

    /* CV Links */
    .cv-links {
      display: flex;
      gap: 1rem;
      margin: 0.2rem 0 1.5rem;
      font-size: 0.95rem;
      padding: 0;
      list-style: none;
    }

    .cv-links span {
      margin: 0;
      padding: 0;
    }

    .cv-links a {
      color: var(--link);
      text-decoration: none;
      margin: 0;
      padding: 0;
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
        flex-wrap: wrap;
        gap: 1rem;
      }

      .nav-title {
        font-size: 1rem;
      }

      .nav-controls {
        width: 100%;
        justify-content: flex-start;
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
</head>
<body id="top">
  <div class="wrap">
    <nav class="site-nav" aria-label="Primary">
      <h1 class="nav-title"><a href="#top">Alessandro Saglia</a></h1>
      <div class="nav-controls">
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
    html += generate_cv_html("it", cv_it)
    
    # Add English CV
    html += generate_cv_html("en", cv_en)
    
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
    html += '''
  <a href="#top" class="back-to-top" id="back-to-top">↑ Top</a>

  <script>
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
      
      // Update CV display
      cvSections.forEach(section => section.classList.remove("active"));
      document.getElementById(`cv-${lang}`).classList.add("active");
      
      // Update language buttons
      langButtons.forEach(btn => btn.classList.remove("active"));
      document.getElementById(`lang-${lang}`).classList.add("active");
      
      // Update download links
      updateDownloadLinks(lang);
      
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
      const browserLang = (navigator.language || navigator.userLanguage || "en").substring(0, 2);
      return browserLang === "it" ? "it" : "en";
    }
    
    const initialLang = getInitialLanguage();
    setLanguage(initialLang);

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
    
    print("Generating HTML...")
    html = generate_full_html(cv_it, cv_en)
    
    output_path = SITE_DIR / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✓ Generated {output_path}")


if __name__ == "__main__":
    main()
