"""
config_loader.py - Load settings from config/settings.yaml and .env.

Usage (from any script in src/):
    from src.config_loader import load_settings, get_logger

    settings = load_settings()
    logger = get_logger("validate_dataset")

The settings dict mirrors the YAML structure:
    settings["schema"]["required_columns"]  ->  ["date", "entity", ...]
    settings["correlation"]["default_window_days"]  ->  3
    settings["paths"]["log_dir"]  ->  "logs"
"""

import logging
import os
from pathlib import Path

import yaml


# Project root is one level up from this file (src/ -> project root).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CONFIG = _PROJECT_ROOT / "config" / "settings.yaml"
_DEFAULT_ENV = _PROJECT_ROOT / ".env"


def _load_dotenv(env_path=None):
    """Parse a .env file into os.environ (simple key=value, no shell expansion)."""
    path = Path(env_path) if env_path else _DEFAULT_ENV
    if not path.exists():
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Only set if the variable has a value (don't overwrite real env vars).
            if value and key not in os.environ:
                os.environ[key] = value


def load_settings(config_path=None):
    """
    Load the YAML config and merge with environment variable overrides.

    Returns a dict with the full settings tree.
    """
    path = Path(config_path) if config_path else _DEFAULT_CONFIG

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        settings = yaml.safe_load(f)

    # Load .env file (if present) into os.environ.
    _load_dotenv()

    # Allow env-var overrides for specific settings.
    env_log_level = os.environ.get("LOG_LEVEL")
    if env_log_level:
        settings["logging"]["level"] = env_log_level.upper()

    return settings


def get_logger(name, settings=None):
    """
    Create a configured logger that writes to both console and logs/ file.

    The log file is named after the logger (e.g., logs/validate_dataset.log).
    """
    if settings is None:
        settings = load_settings()

    log_cfg = settings.get("logging", {})
    level = getattr(logging, log_cfg.get("level", "INFO").upper(), logging.INFO)
    fmt = log_cfg.get("format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(fmt)

    # Console handler.
    if log_cfg.get("log_to_console", True):
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(formatter)
        logger.addHandler(console)

    # File handler.
    if log_cfg.get("log_to_file", True):
        log_dir = _PROJECT_ROOT / log_cfg.get("log_dir", settings.get("paths", {}).get("log_dir", "logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / f"{name}.log")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
