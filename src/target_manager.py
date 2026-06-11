from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Final, Iterable, Sequence

from src.paths import ensure_writable_data_file
from src.target_seed import BASIC_TARGET_TYPES, DEFAULT_TARGETS_BY_TYPE, TARGET_TYPES

CUSTOM_GROUPS_FILE: Final[Path] = ensure_writable_data_file("custom_groups.json", '{\n  "groups": []\n}')


@dataclass(frozen=True, slots=True)
class FolderScanError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class CustomGroup:
    name: str
    targets: list[str]


@dataclass(frozen=True, slots=True)
class TargetStoreData:
    basic_targets_by_type: dict[str, list[str]]
    custom_groups: list[CustomGroup]


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        candidate = value.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        unique_values.append(candidate)
    return unique_values


def _load_json_payload(file_path: Path, default: object) -> object:
    if not file_path.exists():
        return default

    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _save_json_payload(file_path: Path, payload: object) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(file_path)


def _custom_groups_to_payload(groups: Sequence[CustomGroup]) -> dict[str, list[dict[str, object]]]:
    return {
        "groups": [
            {
                "name": group.name,
                "targets": group.targets,
            }
            for group in groups
        ]
    }


def _payload_to_custom_groups(payload: object) -> list[CustomGroup]:
    if not isinstance(payload, dict):
        return []

    raw_groups = payload.get("groups", [])
    if not isinstance(raw_groups, list):
        return []

    groups: list[CustomGroup] = []
    for item in raw_groups:
        if not isinstance(item, dict):
            continue
        group_name = _clean_text(item.get("name"))
        if not group_name:
            continue
        raw_targets = item.get("targets", [])
        if isinstance(raw_targets, list):
            cleaned_targets = [_clean_text(target) for target in raw_targets]
            targets = _unique_preserve_order(target for target in cleaned_targets if target)
        else:
            targets = []
        groups.append(CustomGroup(name=group_name, targets=targets))

    groups.sort(key=lambda group: group.name.casefold())
    return groups


def load_target_store() -> TargetStoreData:
    basic_targets_by_type = {
        target_type: list(DEFAULT_TARGETS_BY_TYPE.get(target_type, []))
        for target_type in BASIC_TARGET_TYPES
    }
    custom_groups = _payload_to_custom_groups(_load_json_payload(CUSTOM_GROUPS_FILE, {"groups": []}))
    return TargetStoreData(
        basic_targets_by_type=basic_targets_by_type,
        custom_groups=custom_groups,
    )


def save_custom_groups(custom_groups: Sequence[CustomGroup]) -> None:
    _save_json_payload(CUSTOM_GROUPS_FILE, _custom_groups_to_payload(custom_groups))


def get_custom_group_names(store: TargetStoreData) -> list[str]:
    return [group.name for group in store.custom_groups]


def resolve_active_target_type(requested_target_type: str | None) -> str:
    if requested_target_type == "사용자지정":
        return "내그룹"
    if requested_target_type in TARGET_TYPES:
        return requested_target_type
    return TARGET_TYPES[0]


def resolve_active_custom_group(
    store: TargetStoreData,
    requested_group_name: str | None,
) -> str:
    group_names = get_custom_group_names(store)
    if requested_group_name in group_names:
        return requested_group_name
    return ""


def get_targets_for_view(
    *,
    store: TargetStoreData,
    target_type: str,
    custom_group_name: str,
) -> list[str]:
    if target_type == "내그룹":
        for group in store.custom_groups:
            if group.name == custom_group_name:
                return list(group.targets)
        return []
    return list(store.basic_targets_by_type.get(target_type, []))
