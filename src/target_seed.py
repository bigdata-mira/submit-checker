from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.paths import resource_path

TARGETS_FILE: Final[Path] = resource_path("data", "targets.json")

TARGET_TYPES: Final[tuple[str, str]] = ("부서", "내그룹")
BASIC_TARGET_TYPES: Final[tuple[str, ...]] = ("부서",)

FALLBACK_TARGETS_BY_TYPE: Final[dict[str, list[str]]] = {
    "실국": [
        "대변인",
        "119종합상황실",
        "감사담당관",
        "운영지원과",
        "기획조정관",
        "119대응국",
        "화재예방국",
        "장비기술국",
    ],
    "부서": [
        "대변인",
        "119종합상황실",
        "감사담당관",
        "운영지원과",
        "기획재정담당관",
        "혁신행정법무담당관",
        "보건안전담당관",
        "교육훈련담당관",
        "대응총괄과",
        "화재대응조사과",
        "구조과",
        "119구급과",
        "구급의료팀",
        "예방정책과",
        "예방분석제도과",
        "위험물안전과",
        "생활안전과",
        "첨단장비과",
        "소방항공과",
        "정보통신과",
        "소방산업진흥정책과",
        "인공지능융합과",
    ],
}


def _clean_unique(values: object) -> list[str]:
    if not isinstance(values, list):
        return []

    cleaned: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        candidate = value.strip()
        if candidate and candidate not in cleaned:
            cleaned.append(candidate)
    return cleaned


def load_default_targets_by_type() -> dict[str, list[str]]:
    if not TARGETS_FILE.exists():
        return {name: list(values) for name, values in FALLBACK_TARGETS_BY_TYPE.items()}

    try:
        payload = json.loads(TARGETS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {name: list(values) for name, values in FALLBACK_TARGETS_BY_TYPE.items()}

    if not isinstance(payload, dict):
        return {name: list(values) for name, values in FALLBACK_TARGETS_BY_TYPE.items()}

    resolved: dict[str, list[str]] = {}
    for target_type in BASIC_TARGET_TYPES:
        cleaned_targets = _clean_unique(payload.get(target_type))
        resolved[target_type] = cleaned_targets or list(FALLBACK_TARGETS_BY_TYPE[target_type])
    return resolved


DEFAULT_TARGETS_BY_TYPE: Final[dict[str, list[str]]] = load_default_targets_by_type()
