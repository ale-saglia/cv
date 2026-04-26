#!/usr/bin/env python3
"""Update .devcontainer/Dockerfile Python base image to match .python-version."""
import re
import sys
from pathlib import Path

root = Path(__file__).parent.parent
version = (root / ".python-version").read_text().strip()
dockerfile = root / ".devcontainer" / "Dockerfile"
original = dockerfile.read_text()
updated = re.sub(r"FROM python:\S+-slim", f"FROM python:{version}-slim", original)

if updated == original:
    print(f"Dockerfile already on python:{version}-slim")
else:
    dockerfile.write_text(updated)
    print(f"Dockerfile updated to python:{version}-slim")
    sys.exit(1)
