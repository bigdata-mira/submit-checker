from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from src.checker import ScanResult
from src.target_manager import TargetStoreData, get_targets_for_view

DEFAULT_FOLDER_PATH: Final[str] = ""
PREVIEW_LIMIT: Final[int] = 5


@dataclass(frozen=True, slots=True)
class IndexViewModel:
    folder_path: str
    folder_files_json: str
    active_target_type: str
    active_custom_group: str
    store_data: TargetStoreData
    available_targets: list[str]
    selected_targets: list[str]
    selected_target_count: int
    applied_summary: str
    preview_targets: list[str]
    extra_target_count: int
    folder_is_selected: bool
    can_scan: bool
    results: list[dict[str, str]]
    summary: dict[str, int | float]
    can_download: bool


def create_empty_scan_result() -> ScanResult:
    return ScanResult(
        rows=[],
        summary={
            "total_targets": 0,
            "submitted_count": 0,
            "missing_count": 0,
            "submission_rate": 0.0,
        },
    )


def build_applied_summary(
    *,
    active_target_type: str,
    selected_targets: list[str],
    available_targets: list[str],
) -> str:
    if not selected_targets:
        return "선택된 대상이 없습니다."

    if available_targets and len(selected_targets) == len(available_targets):
        return f"{active_target_type} 전체 {len(selected_targets)}개"

    return f"{active_target_type} {len(selected_targets)}개 선택"


def build_view_model(
    *,
    store_data: TargetStoreData,
    active_target_type: str,
    active_custom_group: str,
    folder_path: str = DEFAULT_FOLDER_PATH,
    folder_files_json: str = "",
    selected_targets: list[str] | None = None,
    scan_result: ScanResult | None = None,
) -> IndexViewModel:
    available_targets = get_targets_for_view(
        store=store_data,
        target_type=active_target_type,
        custom_group_name=active_custom_group,
    )
    filtered_targets = [target for target in (selected_targets or []) if target in available_targets]
    resolved_scan_result = scan_result or create_empty_scan_result()
    preview_targets = filtered_targets[:PREVIEW_LIMIT]
    normalized_folder_path = folder_path.strip()

    return IndexViewModel(
        folder_path=normalized_folder_path,
        active_target_type=active_target_type,
        active_custom_group=active_custom_group,
        store_data=store_data,
        available_targets=available_targets,
        selected_targets=filtered_targets,
        selected_target_count=len(filtered_targets),
        folder_files_json=folder_files_json,
        applied_summary=build_applied_summary(
            active_target_type=active_target_type,
            selected_targets=filtered_targets,
            available_targets=available_targets,
        ),
        preview_targets=preview_targets,
        extra_target_count=max(len(filtered_targets) - len(preview_targets), 0),
        folder_is_selected=bool(normalized_folder_path),
        can_scan=bool(filtered_targets and normalized_folder_path),
        results=resolved_scan_result.rows,
        summary=resolved_scan_result.summary,
        can_download=bool(resolved_scan_result.rows),
    )
