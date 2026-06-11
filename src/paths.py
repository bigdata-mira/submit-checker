from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Final

APP_DATA_DIR_NAME: Final[str] = "취합체커"
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent


def is_frozen_app() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    if is_frozen_app():
        return Path(getattr(sys, "_MEIPASS"))
    return PROJECT_ROOT


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def app_data_dir() -> Path:
    roaming_path = os.environ.get("APPDATA")
    base_dir = Path(roaming_path) if roaming_path else Path.home() / "AppData" / "Roaming"
    data_dir = base_dir / APP_DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def writable_data_path(file_name: str) -> Path:
    if is_frozen_app():
        return app_data_dir() / file_name
    return PROJECT_ROOT / "data" / file_name


def ensure_writable_data_file(file_name: str, default_text: str) -> Path:
    target_path = writable_data_path(file_name)
    if target_path.exists():
        return target_path

    source_path = resource_path("data", file_name)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.exists():
        target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        target_path.write_text(default_text, encoding="utf-8")
    return target_path
