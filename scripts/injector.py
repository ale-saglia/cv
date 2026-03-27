"""RenderCV injector.

This script enables a "CV-as-code" workflow with optional secret injection:

Flow:
1) Load local plaintext secrets from src/secret.yaml when available.
2) Inject secrets into the YAML template (placeholder substitution + fallback for empty cv fields).
3) Run RenderCV using a temporary injected YAML file.
4) Always clean up temporary files.

Notes:
- The plaintext secret file is never committed and is ignored by git.
- The temporary injected YAML may contain secrets briefly, but it is always removed at the end.
- In --dry-run mode, YAML lines containing `${SECRET_*}` placeholders are removed.
- If src/secret.yaml is missing, the script automatically falls back to dry-run behavior.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

PLAINTEXT_SECRETS_PATH = SRC_DIR / "secret.yaml"

GLOBAL_DESIGN_PATH = SRC_DIR / "design.yaml"
GLOBAL_SETTINGS_PATH = SRC_DIR / "settings.yaml"
LOCALE_FILE_NAME = "locale.yaml"

def yaml_scalar(value: Any) -> str:
    """Serialize a Python value as an inline YAML scalar.

    For strings we use single-quoted YAML scalars to avoid multi-line formatting and
    to safely escape special characters.
    """
    if isinstance(value, str):
        # Normalize newlines to spaces: secrets should not accidentally become multi-line YAML.
        safe = value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")
        return "'" + safe.replace("'", "''") + "'"

    dumped = yaml.safe_dump(value, default_flow_style=True, allow_unicode=True).strip()
    return dumped.splitlines()[0] if dumped else "''"


def read_secrets(secrets_path: Path) -> dict[str, Any]:
    """Read plaintext secrets from YAML and return a mapping."""
    if not secrets_path.exists():
        return {}

    data = yaml.safe_load(secrets_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Secrets file does not contain a valid YAML mapping (dict).")
    return data


def find_template_argument(render_args: list[str]) -> tuple[int, Path]:
    """Find the first existing YAML template path among rendercv arguments.

    We skip YAML files used as values of known rendercv YAML options.
    """
    yaml_option_flags = {
        "--design",
        "-d",
        "--locale-catalog",
        "-lc",
        "--settings",
        "-s",
    }

    skip_next = False
    # Prefer starting after the subcommand (usually: "render").
    start_index = 1 if render_args and render_args[0] == "render" else 0

    for index, arg in enumerate(render_args[start_index:], start=start_index):
        if skip_next:
            skip_next = False
            continue

        if arg in yaml_option_flags:
            skip_next = True
            continue

        if any(arg.startswith(f"{option}=") for option in yaml_option_flags):
            continue

        if arg.startswith("-"):
            continue

        candidate = Path(arg)
        if candidate.suffix in {".yaml", ".yml"}:
            resolved = (ROOT_DIR / candidate).resolve() if not candidate.is_absolute() else candidate
            if resolved.exists():
                return index, resolved

    raise ValueError("No CV YAML template file found in the arguments passed to rendercv.")


def _write_temp_injected_yaml(content: str, template_path: Path) -> Path:
    """Write injected content to a temporary file and return its path."""
    # Keep output next to the original template directory? No:
    # using the OS temp dir prevents accidental commits and avoids collisions in parallel runs.
    # Render output is still forced to template_path.parent/rendercv_output.
    tmp_dir = Path(tempfile.gettempdir())
    unique = f"{template_path.stem}.injected.{os.getpid()}.{template_path.stat().st_mtime_ns}{template_path.suffix}"
    temp_path = tmp_dir / unique
    temp_path.write_text(content, encoding="utf-8")
    return temp_path


def inject_secrets_in_cv(template_path: Path, secrets: dict[str, Any]) -> Path:
    """Inject secrets into the YAML template while preserving formatting as much as possible.

    - Replaces `${SECRET_*}` placeholders found in raw YAML text using yaml_scalar() to safely quote values.
    - Fills empty top-level fields under `cv:` when a matching secret key exists.
    """
    template_content = template_path.read_text(encoding="utf-8")
    placeholder_pattern = re.compile(r"\$\{(SECRET_[A-Z0-9_]+)\}")
    found_placeholders = sorted(set(placeholder_pattern.findall(template_content)))

    replacement_count = 0
    missing_keys: list[str] = []

    for placeholder in found_placeholders:
        secret_key = placeholder.replace("SECRET_", "").lower()
        if secret_key in secrets:
            template_content = template_content.replace(
                f"${{{placeholder}}}",
                yaml_scalar(secrets[secret_key]),
            )
            replacement_count += 1
        else:
            missing_keys.append(secret_key)

    lines = template_content.splitlines()
    in_cv_section = False
    fallback_injected_keys: list[str] = []

    # Match simple `  field: value` entries at the first level inside `cv:`.
    cv_line_pattern = re.compile(r"^(\s{2})([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$")

    for idx, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("#") or not stripped:
            continue

        if line.startswith("cv:"):
            in_cv_section = True
            continue

        # If we leave the indented block and see a new top-level key, exit `cv:` section.
        if in_cv_section and not line.startswith(" ") and ":" in line:
            in_cv_section = False

        if not in_cv_section:
            continue

        match = cv_line_pattern.match(line)
        if not match:
            continue

        indent, field_name, raw_value = match.groups()
        normalized_value = raw_value.strip().lower()
        is_empty_field = raw_value.strip() in {"", "''", '""'} or normalized_value in {"null", "~"}

        if not is_empty_field:
            continue

        if field_name not in secrets:
            continue

        lines[idx] = f"{indent}{field_name}: {yaml_scalar(secrets[field_name])}"
        fallback_injected_keys.append(field_name)

    final_content = "\n".join(lines)
    if template_path.read_text(encoding="utf-8").endswith("\n"):
        final_content += "\n"

    temp_path = _write_temp_injected_yaml(final_content, template_path)

    if replacement_count:
        print(f"Placeholders replaced: {replacement_count}")
    else:
        print("No SECRET placeholders found in the template.")

    if fallback_injected_keys:
        unique_keys = sorted(set(fallback_injected_keys))
        print(f"Empty cv fields filled from secrets: {', '.join(unique_keys)}")

    if missing_keys:
        unique_missing = sorted(set(missing_keys))
        print(f"Missing secret keys: {', '.join(unique_missing)}")

    return temp_path


def has_cli_option(args: list[str], long_option: str, short_option: str) -> bool:
    """Check whether a CLI option is already present among arguments."""
    for arg in args:
        if arg in {long_option, short_option}:
            return True
        if arg.startswith(f"{long_option}=") or arg.startswith(f"{short_option}="):
            return True
    return False


def run_rendercv(
    render_args: list[str],
    template_arg_index: int,
    template_path: Path,
    temp_template_path: Path,
) -> int:
    """Run rendercv, replacing the original template with the injected temporary one."""
    command_args = list(render_args)
    command_args[template_arg_index] = str(temp_template_path)

    # Always force output to the original template folder, not the temp folder.
    output_dir = template_path.parent / "rendercv_output"
    if not has_cli_option(command_args, "--output-folder", "-o"):
        command_args.extend(["--output-folder", str(output_dir)])

    if not has_cli_option(command_args, "--design", "-d") and GLOBAL_DESIGN_PATH.exists():
        command_args.extend(["--design", str(GLOBAL_DESIGN_PATH)])

    if not has_cli_option(command_args, "--settings", "-s") and GLOBAL_SETTINGS_PATH.exists():
        command_args.extend(["--settings", str(GLOBAL_SETTINGS_PATH)])

    locale_path = template_path.parent / LOCALE_FILE_NAME
    if not has_cli_option(command_args, "--locale-catalog", "-lc") and locale_path.exists():
        command_args.extend(["--locale-catalog", str(locale_path)])

    command = ["rendercv", *command_args]
    print(f"Running: {' '.join(command)}")

    result = subprocess.run(command, cwd=ROOT_DIR, text=True, capture_output=True)

    # Print captured output for easier CI debugging.
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode


def safe_remove(path: Path) -> None:
    """Remove a file if it exists, without interrupting the flow on errors."""
    try:
        if path.exists():
            path.unlink()
            print(f"Removed temporary file: {path}")
    except Exception as error:
        print(f"Could not remove {path}: {error}", file=sys.stderr)


def strip_placeholders(template_path: Path, announce: bool = True) -> Path:
    """Dry-run mode: remove YAML lines containing `${SECRET_*}` placeholders.

    This keeps the original file untouched and generates a temporary sanitized YAML
    without secret-bound fields.
    """
    content = template_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    placeholder_pattern = re.compile(r"\$\{SECRET_[A-Z0-9_]+\}")
    kept_lines: list[str] = []
    removed_count = 0

    for line in lines:
        if placeholder_pattern.search(line):
            removed_count += 1
            continue
        kept_lines.append(line)

    sanitized_content = "\n".join(kept_lines)
    if content.endswith("\n"):
        sanitized_content += "\n"

    temp_path = _write_temp_injected_yaml(sanitized_content, template_path)
    if announce:
        print(f"Dry-run: removed {removed_count} YAML line(s) containing secret placeholders.")
    return temp_path


def main() -> None:
    """Entry point: load/inject -> render -> cleanup.

    Flags:
        --dry-run   Remove secret-placeholder lines.
    """
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    if dry_run:
        args = [a for a in args if a != "--dry-run"]

    if len(args) < 2:
        print("Usage: python scripts/injector.py [--dry-run] render <cv.yaml> [other rendercv args]")
        sys.exit(1)

    render_args = args
    temp_template_path: Path | None = None

    try:
        template_arg_index, template_path = find_template_argument(render_args)

        if dry_run:
            temp_template_path = strip_placeholders(template_path)
        else:
            secrets = read_secrets(PLAINTEXT_SECRETS_PATH)
            if secrets:
                temp_template_path = inject_secrets_in_cv(template_path, secrets)
            else:
                temp_template_path = strip_placeholders(template_path, announce=False)

        exit_code = run_rendercv(render_args, template_arg_index, template_path, temp_template_path)
        if exit_code != 0:
            raise RuntimeError(f"rendercv exited with code {exit_code}")

    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)

    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    finally:
        if temp_template_path:
            safe_remove(temp_template_path)


if __name__ == "__main__":
    main()