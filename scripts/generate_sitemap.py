"""Generate sitemap.xml and robots.txt."""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT_DIR / "_site"
BASE_URL = "https://cv.ale-saglia.com"


def generate_sitemap() -> None:
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    urls_to_add = ["/", "/#it", "/#en"]
    
    index_file = SITE_DIR / "index.html"
    if index_file.exists():
        index_mtime = index_file.stat().st_mtime
        index_date = datetime.fromtimestamp(index_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
    else:
        index_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    for url_path in urls_to_add:
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"{BASE_URL}{url_path}"
        lastmod = ET.SubElement(url, "lastmod")
        lastmod.text = index_date
            
    if SITE_DIR.exists():
        for pdf_path in sorted(SITE_DIR.glob("**/*.pdf")):
            relative_path = pdf_path.relative_to(SITE_DIR)
            url = ET.SubElement(urlset, "url")
            loc = ET.SubElement(url, "loc")
            loc.text = f"{BASE_URL}/{relative_path.as_posix()}"
            
            lastmod = ET.SubElement(url, "lastmod")
            mtime = pdf_path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            lastmod.text = dt.strftime("%Y-%m-%d")

    xml_str = ET.tostring(urlset, encoding='utf-8')
    parsed = minidom.parseString(xml_str)
    sitemap_content = parsed.toprettyxml(indent="  ")
    sitemap_content = '\n'.join([line for line in sitemap_content.split('\n') if line.strip()])
    sitemap_content = sitemap_content.replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>')
    
    sitemap_path = SITE_DIR / "sitemap.xml"
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(sitemap_content + "\n")
    print(f"✓ Generated {sitemap_path}")


def generate_robots() -> None:
    robots_content = f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n"
    robots_path = SITE_DIR / "robots.txt"
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(robots_content)
    print(f"✓ Generated {robots_path}")


def main() -> None:
    generate_sitemap()
    generate_robots()


if __name__ == "__main__":
    main()
