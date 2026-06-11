from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Final

from src.target_manager import FolderScanError

SUPPORTED_EXTENSIONS: Final[frozenset[str]] = frozenset({".hwp", ".hwpx", ".xls", ".xlsx", ".docx", ".pdf"})
TEMP_FILE_PREFIX: Final[str] = "~$"
TEMP_FILE_EXTENSION: Final[str] = ".tmp"
NORMALIZE_PATTERN: Final[re.Pattern[str]] = re.compile(r"[\s()_\-]+")
SUBMITTED_STATUS: Final[str] = "제출"
MISSING_STATUS: Final[str] = "미제출"


@dataclass(frozen=True, slots=True)
class ScanResult:
    rows: list[dict[str, str]]
    summary: dict[str, int | float]


def normalize_text(raw_text: str) -> str:
    return NORMALIZE_PATTERN.sub("", raw_text).casefold()


def is_supported_file(file_path: Path) -> bool:
    if not file_path.is_file():
        return False
    if file_path.name.startswith(TEMP_FILE_PREFIX):
        return False
    if file_path.suffix.casefold() == TEMP_FILE_EXTENSION:
        return False
    return file_path.suffix.casefold() in SUPPORTED_EXTENSIONS


def is_supported_file_name(file_name: str) -> bool:
    file_path = Path(file_name)
    if file_path.name.startswith(TEMP_FILE_PREFIX):
        return False
    if file_path.suffix.casefold() == TEMP_FILE_EXTENSION:
        return False
    return file_path.suffix.casefold() in SUPPORTED_EXTENSIONS


def validate_folder_path(folder_path: str) -> Path:
    target_path = Path(folder_path)
    if not target_path.exists():
        raise FolderScanError("입력한 폴더 경로가 존재하지 않습니다.")
    if not target_path.is_dir():
        raise FolderScanError("입력한 경로가 폴더가 아닙니다.")
    return target_path


def find_matching_files(target_name: str, files: list[Path]) -> list[Path]:
    normalized_target = normalize_text(target_name)
    matched_files: list[Path] = []
    for file_path in files:
        normalized_filename = normalize_text(file_path.stem)
        if normalized_target in normalized_filename:
            matched_files.append(file_path)
    return sorted(matched_files, key=lambda path: path.name.casefold())


def find_matching_file_names(target_name: str, file_names: list[str]) -> list[str]:
    normalized_target = normalize_text(target_name)
    matched_file_names: list[str] = []
    for file_name in file_names:
        file_path = Path(file_name)
        normalized_filename = normalize_text(file_path.stem)
        if normalized_target in normalized_filename:
            matched_file_names.append(file_name)
    return sorted(matched_file_names, key=lambda name: Path(name).name.casefold())


def format_latest_modified_time(files: list[Path]) -> str:
    if not files:
        return "-"
    latest_timestamp = max(file_path.stat().st_mtime for file_path in files)
    return datetime.fromtimestamp(latest_timestamp).strftime("%Y-%m-%d %H:%M")


def build_row(target_name: str, matched_files: list[Path]) -> dict[str, str]:
    file_count = len(matched_files)
    is_submitted = file_count > 0
    filenames = [file_path.name for file_path in matched_files]

    return {
        "상태": SUBMITTED_STATUS if is_submitted else MISSING_STATUS,
        "대상": target_name,
        "제출파일명": ", ".join(filenames) if filenames else "-",
        "파일 개수": str(file_count),
        "제출 시간": format_latest_modified_time(matched_files),
        "비고": "중복 제출 파일 확인" if file_count > 1 else "-",
    }


def build_row_from_file_names(target_name: str, matched_file_names: list[str]) -> dict[str, str]:
    file_count = len(matched_file_names)
    is_submitted = file_count > 0
    filenames = [Path(file_name).name for file_name in matched_file_names]

    return {
        "상태": SUBMITTED_STATUS if is_submitted else MISSING_STATUS,
        "대상": target_name,
        "제출파일명": ", ".join(filenames) if filenames else "-",
        "파일 개수": str(file_count),
        "제출 시간": "-",
        "비고": "중복 제출 파일 확인" if file_count > 1 else "-",
    }


def build_summary(rows: list[dict[str, str]]) -> dict[str, int | float]:
    submitted_count = sum(1 for row in rows if row["상태"] == SUBMITTED_STATUS)
    total_targets = len(rows)
    submission_rate = round((submitted_count / total_targets) * 100, 1) if total_targets else 0.0
    return {
        "total_targets": total_targets,
        "submitted_count": submitted_count,
        "missing_count": total_targets - submitted_count,
        "submission_rate": submission_rate,
    }


def scan_submissions(folder_path: str, targets: list[str]) -> ScanResult:
    scan_folder = validate_folder_path(folder_path)
    supported_files = sorted(
        [path for path in scan_folder.iterdir() if is_supported_file(path)],
        key=lambda path: path.name.casefold(),
    )
    rows = [build_row(target, find_matching_files(target, supported_files)) for target in targets]
    return ScanResult(rows=rows, summary=build_summary(rows))


def scan_submissions_from_file_names(file_names: list[str], targets: list[str]) -> ScanResult:
    supported_file_names = sorted(
        [file_name for file_name in file_names if is_supported_file_name(file_name)],
        key=lambda name: Path(name).name.casefold(),
    )
    rows = [
        build_row_from_file_names(target, find_matching_file_names(target, supported_file_names))
        for target in targets
    ]
    return ScanResult(rows=rows, summary=build_summary(rows))
