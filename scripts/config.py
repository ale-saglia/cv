"""Shared project paths and constants."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
SITE_DIR = ROOT_DIR / "_site"
CV_DIR = ROOT_DIR / "_cv"
TEMPLATES_DIR = Path(__file__).parent / "templates"

GLOBAL_DESIGN_PATH = SRC_DIR / "design.yaml"
PLAINTEXT_SECRETS_PATH = SRC_DIR / "secret.yaml"
LOCALE_FILE_NAME = "locale.yaml"

BASE_URL = "https://cv.ale-saglia.com"
