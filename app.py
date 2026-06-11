from __future__ import annotations

import json
import os
import subprocess
import threading
import webbrowser
from typing import Final

from flask import Flask, Response, flash, jsonify, redirect, render_template, request, url_for

from src.checker import FolderScanError, scan_submissions
from src.custom_group_routes import custom_group_bp
from src.exporter import export_results_to_csv
from src.page_state import IndexViewModel, build_view_model
from src.paths import is_frozen_app, resource_path
from src.target_manager import get_custom_group_names, load_target_store, resolve_active_custom_group, resolve_active_target_type
from src.target_seed import TARGET_TYPES

APP_TITLE: Final[str] = "취합체커"
APP_HOST: Final[str] = "127.0.0.1"
APP_PORT: Final[int] = 5000
BROWSER_OPEN_DELAY_SECONDS: Final[float] = 1.0

app = Flask(
    __name__,
    template_folder=str(resource_path("templates")),
    static_folder=str(resource_path("static")),
)
app.config["SECRET_KEY"] = "collection-checker-local-secret-key"
app.register_blueprint(custom_group_bp)


def parse_field_list(field_name: str) -> list[str]:
    return [value.strip() for value in request.form.getlist(field_name) if value.strip()]


def parse_json_list(field_name: str) -> list[str]:
    raw_value = request.form.get(field_name, "").strip()
    if not raw_value:
        return []
    try:
        decoded = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(decoded, list):
        return []
    return [str(value).strip() for value in decoded if str(value).strip()]


def scan_from_request(folder_path: str, file_names: list[str], file_list_mode: bool, targets: list[str]):
    if file_list_mode:
        from src.checker import scan_submissions_from_file_names

        return scan_submissions_from_file_names(file_names=file_names, targets=targets)
    return scan_submissions(folder_path=folder_path, targets=targets)


def choose_folder_path() -> str:
    powershell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    script = r"""
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = '취합폴더를 선택하세요'
$dialog.ShowNewFolderButton = $true
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    Write-Output $dialog.SelectedPath
}
"""
    try:
        completed = subprocess.run(
            [powershell, "-NoProfile", "-STA", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ""

    selected_path = completed.stdout.strip().splitlines()
    return selected_path[-1].strip() if selected_path else ""


def render_index(page: IndexViewModel) -> str:
    return render_template(
        "index.html",
        app_title=APP_TITLE,
        target_types=TARGET_TYPES,
        custom_group_names=get_custom_group_names(page.store_data),
        page=page,
    )


def current_selection_url(active_target_type: str, active_custom_group: str) -> str:
    params: dict[str, str] = {"target_type": active_target_type}
    if active_target_type == "내그룹" and active_custom_group:
        params["custom_group"] = active_custom_group
    return url_for("index", **params)


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    store = load_target_store()
    active_target_type = resolve_active_target_type(request.values.get("target_type"))
    active_custom_group = resolve_active_custom_group(store, request.values.get("custom_group"))

    if request.method == "GET":
        return render_index(
            build_view_model(
                store_data=store,
                active_target_type=active_target_type,
                active_custom_group=active_custom_group,
            )
        )

    action = request.form.get("action", "scan")
    folder_path = request.form.get("folder_path", "").strip()
    folder_files_raw = request.form.get("folder_files_json", "").strip()
    folder_files = parse_json_list("folder_files_json")
    folder_files_json = folder_files_raw if folder_files_raw else ""
    candidate_targets = parse_field_list("candidate_targets")
    applied_targets = parse_field_list("applied_targets")

    if action == "apply":
        page = build_view_model(
            store_data=store,
            active_target_type=active_target_type,
            active_custom_group=active_custom_group,
            folder_path=folder_path,
            folder_files_json=folder_files_json,
            selected_targets=candidate_targets,
        )
        if not page.selected_targets:
            flash("선택된 대상이 없습니다. 왼쪽 목록에서 하나 이상 선택해 주세요.", "warning")
        else:
            flash(f"{page.selected_target_count}개 대상이 검사대상으로 적용되었습니다.", "success")
        return render_index(page)

    page = build_view_model(
        store_data=store,
        active_target_type=active_target_type,
        active_custom_group=active_custom_group,
        folder_path=folder_path,
        folder_files_json=folder_files_json,
        selected_targets=applied_targets,
    )

    if not page.selected_targets:
        flash("검사대상이 아직 적용되지 않았습니다. 먼저 [선택대상 적용]을 눌러 주세요.", "warning")
        return render_index(page)

    if not page.folder_is_selected:
        flash("취합폴더 경로를 입력하거나 폴더 선택 버튼으로 지정해 주세요.", "danger")
        return render_index(page)

    try:
        scan_result = scan_from_request(
            folder_path=page.folder_path,
            file_names=folder_files,
            file_list_mode=bool(folder_files_raw),
            targets=page.selected_targets,
        )
    except FolderScanError as error:
        flash(str(error), "danger")
        return render_index(page)

    result_page = build_view_model(
        store_data=store,
        active_target_type=active_target_type,
        active_custom_group=active_custom_group,
        folder_path=page.folder_path,
        folder_files_json=folder_files_json,
        selected_targets=page.selected_targets,
        scan_result=scan_result,
    )
    flash("제출여부 확인이 완료되었습니다.", "success")
    return render_index(result_page)


@app.route("/download", methods=["POST"])
def download_csv() -> Response:
    store = load_target_store()
    active_target_type = resolve_active_target_type(request.form.get("target_type"))
    active_custom_group = resolve_active_custom_group(store, request.form.get("custom_group"))
    folder_path = request.form.get("folder_path", "").strip()
    folder_files_raw = request.form.get("folder_files_json", "").strip()
    folder_files = parse_json_list("folder_files_json")
    folder_files_json = folder_files_raw if folder_files_raw else ""
    applied_targets = parse_field_list("applied_targets")

    page = build_view_model(
        store_data=store,
        active_target_type=active_target_type,
        active_custom_group=active_custom_group,
        folder_path=folder_path,
        folder_files_json=folder_files_json,
        selected_targets=applied_targets,
    )

    if not page.selected_targets:
        flash("CSV를 내려받으려면 먼저 검사대상을 적용해 주세요.", "warning")
        return redirect(current_selection_url(active_target_type, active_custom_group))

    if not page.folder_is_selected:
        flash("CSV를 내려받으려면 취합폴더 경로를 입력해 주세요.", "warning")
        return redirect(current_selection_url(active_target_type, active_custom_group))

    try:
        scan_result = scan_from_request(
            folder_path=page.folder_path,
            file_names=folder_files,
            file_list_mode=bool(folder_files_raw),
            targets=page.selected_targets,
        )
    except FolderScanError as error:
        flash(str(error), "danger")
        return redirect(current_selection_url(active_target_type, active_custom_group))

    csv_content = export_results_to_csv(scan_result.rows)
    file_name = f"{APP_TITLE}_{active_target_type}_검사결과.csv"
    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )


@app.route("/select-folder", methods=["POST"])
def select_folder() -> Response:
    return jsonify({"folder_path": choose_folder_path()})


def should_open_browser() -> bool:
    if os.environ.get("CHWIHAPCHECKER_NO_BROWSER") == "1":
        return False
    if is_frozen_app():
        return True
    return os.environ.get("WERKZEUG_RUN_MAIN") == "true"


def open_browser_later() -> None:
    if not should_open_browser():
        return

    url = f"http://{APP_HOST}:{APP_PORT}"
    timer = threading.Timer(BROWSER_OPEN_DELAY_SECONDS, lambda: webbrowser.open(url))
    timer.daemon = True
    timer.start()


if __name__ == "__main__":
    open_browser_later()
    app.run(
        debug=not is_frozen_app(),
        host=APP_HOST,
        port=APP_PORT,
        use_reloader=not is_frozen_app(),
    )
