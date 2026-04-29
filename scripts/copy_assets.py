"""Copy static assets to _site/."""

import shutil
from config import ROOT_DIR, SITE_DIR, TEMPLATES_DIR


ASSETS = [
    (TEMPLATES_DIR / "favicon.svg", SITE_DIR / "assets" / "favicon-cv.svg"),
    (TEMPLATES_DIR / "og-image.png", SITE_DIR / "assets" / "og-image.png"),
]


def main() -> None:
    for src, dst in ASSETS:
        if not src.exists():
            print(f"⚠ Missing asset: {src}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"✓ Copied {src.name} → {dst.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
