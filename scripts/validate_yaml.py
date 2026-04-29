"""Validate YAML syntax for all source and workflow files."""

import sys

import yaml

from config import ROOT_DIR

files = []
files.extend((ROOT_DIR / "src").rglob("*.yaml"))
files.extend((ROOT_DIR / "src").rglob("*.yml"))
files.extend((ROOT_DIR / ".github/workflows").glob("*.yml"))

# Exclude encrypted files (not valid plain YAML)
files = sorted({f for f in files if ".enc." not in f.name})

errors = []
for path in files:
    try:
        with path.open(encoding="utf-8") as fh:
            yaml.safe_load(fh)
        print(f"  OK  {path.relative_to(ROOT_DIR)}")
    except yaml.YAMLError as exc:
        print(f"  FAIL {path.relative_to(ROOT_DIR)}: {exc}")
        errors.append(path)

if errors:
    print(f"\n{len(errors)} file(s) with YAML errors.")
    sys.exit(1)
else:
    print(f"\nAll {len(files)} YAML file(s) are valid.")
