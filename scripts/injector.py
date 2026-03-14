import subprocess
import sys
from pathlib import Path
import re

import yaml

"""Injector per RenderCV.

Flusso:
1) Decripta i segreti con sops in memoria.
2) Inietta i segreti nel template YAML (placeholder + fallback campi vuoti in cv).
3) Esegue rendercv con il template temporaneo.
4) Rimuove sempre i file temporanei.
"""


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ENCRYPTED_SECRETS_PATH = ROOT_DIR / "src" / "secret.enc.yaml"
GLOBAL_DESIGN_PATH = SRC_DIR / "design.yaml"
GLOBAL_SETTINGS_PATH = SRC_DIR / "settings.yaml"
LOCALE_FILE_NAME = "locale.yaml"


def yaml_scalar(value: object) -> str:
    """Serializza un valore Python in formato scalare YAML inline."""
    if isinstance(value, str):
        # Usiamo quoting singolo YAML per evitare output multi-riga con "...".
        return "'" + value.replace("'", "''") + "'"

    dumped = yaml.safe_dump(value, default_flow_style=True, allow_unicode=True).strip()
    return dumped.splitlines()[0] if dumped else "''"


def decrypt_secrets(encrypted_path: Path) -> dict:
    """Decripta il file segreti con sops e restituisce i dati in memoria."""
    if not encrypted_path.exists():
        raise FileNotFoundError(f"File segreti cifrato non trovato: {encrypted_path}")

    result = subprocess.run(
        ["sops", "--decrypt", str(encrypted_path)],
        capture_output=True,
        text=True,
        check=True,
    )

    data = yaml.safe_load(result.stdout) or {}
    if not isinstance(data, dict):
        raise ValueError("Il file segreti decriptato non contiene una mappa valida.")
    return data


def find_template_argument(render_args: list[str]) -> tuple[int, Path]:
    """Trova tra gli argomenti di rendercv il primo file YAML esistente."""
    yaml_option_flags = {
        "--design",
        "-d",
        "--locale-catalog",
        "-lc",
        "--settings",
        "-s",
    }

    skip_next = False
    for index, arg in enumerate(render_args):
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
    raise ValueError("Nessun file YAML del CV trovato negli argomenti passati a rendercv.")


def inject_secrets_in_cv(template_path: Path, secrets: dict) -> Path:
    """Inietta i segreti nel template preservando il più possibile formato/ancore.

    - Sostituisce i placeholder `${SECRET_*}` presenti nel testo usando yaml_scalar()
      per quotare correttamente i valori (sicuro contro : # newline ecc.).
    - Fa fallback sui campi top-level della sezione `cv` che sono vuoti.
    """
    template_content = template_path.read_text(encoding="utf-8")
    placeholder_pattern = re.compile(r"\$\{(SECRET_[A-Z0-9_]+)\}")
    found_placeholders = sorted(set(placeholder_pattern.findall(template_content)))

    replacement_count = 0
    missing_keys = []

    for placeholder in found_placeholders:
        secret_key = placeholder.replace("SECRET_", "").lower()
        if secret_key in secrets:
            # Sostituzione sicura: yaml_scalar() quota il valore per evitare
            # che caratteri speciali (: # newline ...) rompano il YAML.
            template_content = template_content.replace(
                f"${{{placeholder}}}",
                yaml_scalar(secrets[secret_key]),
            )
            replacement_count += 1
        else:
            missing_keys.append(secret_key)

    lines = template_content.splitlines()
    in_cv_section = False
    fallback_injected_keys = []
    cv_line_pattern = re.compile(r"^(\s{2})([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$")

    for index, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("#") or not stripped:
            continue

        if line.startswith("cv:"):
            in_cv_section = True
            continue

        if in_cv_section and not line.startswith(" ") and ":" in line:
            in_cv_section = False

        if not in_cv_section:
            continue

        # Gestiamo solo chiavi semplici al primo livello dentro `cv:`.
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

        lines[index] = f"{indent}{field_name}: {yaml_scalar(secrets[field_name])}"
        fallback_injected_keys.append(field_name)

    template_content = "\n".join(lines)
    if template_path.read_text(encoding="utf-8").endswith("\n"):
        template_content += "\n"

    temp_path = template_path.with_name(f"{template_path.stem}.injected.tmp{template_path.suffix}")
    temp_path.write_text(template_content, encoding="utf-8")

    if replacement_count:
        print(f"Placeholder sostituiti: {replacement_count}")
    else:
        print("Nessun placeholder SECRET trovato nel template.")

    if fallback_injected_keys:
        print(f"Campi cv vuoti valorizzati: {', '.join(sorted(set(fallback_injected_keys)))}")

    if missing_keys:
        print(f"Chiavi segrete mancanti: {', '.join(sorted(set(missing_keys)))}")

    return temp_path


def run_rendercv(render_args: list[str], template_arg_index: int, temp_template_path: Path) -> int:
    """Esegue rendercv sostituendo il template originale con quello temporaneo."""
    command_args = list(render_args)
    command_args[template_arg_index] = str(temp_template_path)

    output_dir = temp_template_path.parent / "rendercv_output"
    if not has_cli_option(command_args, "--output-folder", "-o"):
        command_args.extend(["--output-folder", str(output_dir)])

    if not has_cli_option(command_args, "--design", "-d") and GLOBAL_DESIGN_PATH.exists():
        command_args.extend(["--design", str(GLOBAL_DESIGN_PATH)])

    if not has_cli_option(command_args, "--settings", "-s") and GLOBAL_SETTINGS_PATH.exists():
        command_args.extend(["--settings", str(GLOBAL_SETTINGS_PATH)])

    locale_path = temp_template_path.parent / LOCALE_FILE_NAME
    if not has_cli_option(command_args, "--locale-catalog", "-lc") and locale_path.exists():
        command_args.extend(["--locale-catalog", str(locale_path)])

    command = ["rendercv", *command_args]
    print(f"Eseguo: {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT_DIR)
    return result.returncode


def has_cli_option(args: list[str], long_option: str, short_option: str) -> bool:
    """Verifica se un'opzione CLI è già presente negli argomenti."""
    for arg in args:
        if arg in {long_option, short_option}:
            return True
        if arg.startswith(f"{long_option}=") or arg.startswith(f"{short_option}="):
            return True
    return False


def safe_remove(path: Path) -> None:
    """Rimuove un file se esiste, senza interrompere il flusso in caso di errore."""
    try:
        if path.exists():
            path.unlink()
            print(f"Rimosso file temporaneo: {path}")
    except Exception as error:
        print(f"Impossibile rimuovere {path}: {error}")


def strip_placeholders(template_path: Path) -> Path:
    """Modalità dry-run: rimuove i placeholder ${SECRET_*} lasciando i campi vuoti."""
    content = template_path.read_text(encoding="utf-8")
    content = re.sub(r"\$\{SECRET_[A-Z0-9_]+\}", "", content)
    temp_path = template_path.with_name(f"{template_path.stem}.injected.tmp{template_path.suffix}")
    temp_path.write_text(content, encoding="utf-8")
    print("Dry-run: placeholder rimossi, nessun segreto iniettato.")
    return temp_path


def main() -> None:
    """Entry point: orchestrazione decrypt -> inject -> render -> cleanup.

    Flags:
      --dry-run   Rimuove i placeholder senza decrittare i segreti.
    """
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    if dry_run:
        args = [a for a in args if a != "--dry-run"]

    if len(args) < 2:
        print("Utilizzo: python scripts/injector.py [--dry-run] render <cv.yaml> [altri argomenti rendercv]")
        sys.exit(1)

    render_args = args
    temp_template_path = None

    try:
        template_arg_index, template_path = find_template_argument(render_args)
        if dry_run:
            temp_template_path = strip_placeholders(template_path)
        else:
            secrets = decrypt_secrets(ENCRYPTED_SECRETS_PATH)
            temp_template_path = inject_secrets_in_cv(template_path, secrets)
        exit_code = run_rendercv(render_args, template_arg_index, temp_template_path)
        if exit_code != 0:
            raise RuntimeError(f"rendercv ha terminato con codice {exit_code}")
    except KeyboardInterrupt:
        # Ctrl+C: cleanup garantito dal finally, uscita con codice standard 130.
        print("\nInterrotto dall'utente.")
        sys.exit(130)
    except subprocess.CalledProcessError as error:
        print(error.stderr or str(error))
        sys.exit(error.returncode)
    except Exception as error:
        print(f"Errore: {error}")
        sys.exit(1)
    finally:
        # Cleanup sempre eseguito, anche se rendercv, sops o l'utente interrompono.
        if temp_template_path:
            safe_remove(temp_template_path)


if __name__ == "__main__":
    main()