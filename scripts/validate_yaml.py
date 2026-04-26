"""Validate YAML syntax for all source and workflow files."""

import sys
from pathlib import Path

import yaml

files = []
files.extend(Path("src").rglob("*.yaml"))
files.extend(Path("src").rglob("*.yml"))
files.extend(Path(".github/workflows").glob("*.yml"))

# Exclude encrypted files (not valid plain YAML)
files = sorted({f for f in files if ".enc." not in f.name})

errors = []
for path in files:
    try:
        with path.open(encoding="utf-8") as fh:
            yaml.safe_load(fh)
        print(f"  OK  {path}")
    except yaml.YAMLError as exc:
        print(f"  FAIL {path}: {exc}")
        errors.append(path)

if errors:
    print(f"\n{len(errors)} file(s) with YAML errors.")
    sys.exit(1)
else:
    print(f"\nAll {len(files)} YAML file(s) are valid.")
