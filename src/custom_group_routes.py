from __future__ import annotations

from io import BytesIO

from flask import Blueprint, Response, flash, jsonify, redirect, request, url_for
from openpyxl import Workbook

from src.checker import FolderScanError
from src.custom_groups import (
    add_custom_group,
    add_target_to_custom_group,
    add_targets_to_custom_group,
    delete_custom_group,
    delete_target_from_custom_group,
    delete_targets_from_custom_group,
    import_targets_from_excel,
    load_target_store,
    rename_custom_group,
)
from src.target_manager import get_custom_group_names

custom_group_bp = Blueprint("custom_groups", __name__)


def _is_ajax_request() -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _selection_url(group_name: str) -> str:
    if group_name:
        return url_for("index", target_type="내그룹", custom_group=group_name)
    return url_for("index", target_type="내그룹")


def _group_state_payload(group_name: str) -> dict[str, object]:
    store = load_target_store()
    group_names = get_custom_group_names(store)
    active_group = group_name if group_name in group_names else ""
    targets = []
    if active_group:
        for group in store.custom_groups:
            if group.name == active_group:
                targets = list(group.targets)
                break

    return {
        "active_target_type": "내그룹",
        "active_custom_group": active_group,
        "custom_group_names": group_names,
        "available_targets": targets,
        "registered_count": len(targets),
        "selected_count": 0,
    }


def _ajax_state_response(group_name: str, message: str, category: str = "success") -> Response:
    payload = _group_state_payload(group_name)
    payload["message"] = message
    payload["message_category"] = category
    return jsonify(payload)


@custom_group_bp.get("/custom-groups/state")
def group_state_route() -> Response:
    group_name = request.args.get("custom_group", "").strip()
    return jsonify(_group_state_payload(group_name))


@custom_group_bp.route("/custom-groups/add", methods=["POST"])
def add_custom_group_route() -> Response:
    current_group = request.form.get("custom_group", "").strip()
    group_name = request.form.get("group_name", "").strip()
    try:
        add_custom_group(group_name)
    except FolderScanError as error:
        if _is_ajax_request():
            return _ajax_state_response(current_group, str(error), "danger")
        flash(str(error), "danger")
    else:
        current_group = group_name
        if _is_ajax_request():
            return _ajax_state_response(current_group, f"그룹 '{group_name}'을(를) 추가했습니다.")
        flash(f"그룹 '{group_name}'을(를) 추가했습니다.", "success")
    return redirect(_selection_url(current_group))


@custom_group_bp.route("/custom-groups/rename", methods=["POST"])
def rename_custom_group_route() -> Response:
    current_group = request.form.get("custom_group", "").strip()
    new_group_name = request.form.get("new_group_name", "").strip()
    try:
        rename_custom_group(current_group, new_group_name)
    except FolderScanError as error:
        if _is_ajax_request():
            return _ajax_state_response(current_group, str(error), "danger")
        flash(str(error), "danger")
        return redirect(_selection_url(current_group))
    if _is_ajax_request():
        return _ajax_state_response(new_group_name, f"그룹명을 '{new_group_name}'(으)로 변경했습니다.")
    flash(f"그룹명을 '{new_group_name}'(으)로 변경했습니다.", "success")
    return redirect(_selection_url(new_group_name))


@custom_group_bp.route("/custom-groups/delete", methods=["POST"])
def delete_custom_group_route() -> Response:
    group_name = request.form.get("delete_group_name", request.form.get("group_name", "")).strip()
    try:
        delete_custom_group(group_name)
    except FolderScanError as error:
        if _is_ajax_request():
            return _ajax_state_response("", str(error), "danger")
        flash(str(error), "danger")
    else:
        if _is_ajax_request():
            return _ajax_state_response("", f"그룹 '{group_name}'을(를) 삭제했습니다.")
        flash(f"그룹 '{group_name}'을(를) 삭제했습니다.", "success")
    return redirect(_selection_url(""))


@custom_group_bp.route("/custom-targets/add", methods=["POST"])
def add_custom_target_route() -> Response:
    group_name = request.form.get("custom_group", "").strip()
    target_name = request.form.get("target_name", "").strip()
    if not group_name:
        if _is_ajax_request():
            return _ajax_state_response("", "먼저 그룹을 선택해 주세요.", "warning")
        flash("먼저 그룹을 선택해 주세요.", "warning")
        return redirect(_selection_url(""))
    try:
        add_target_to_custom_group(group_name, target_name)
    except FolderScanError as error:
        if _is_ajax_request():
            return _ajax_state_response(group_name, str(error), "danger")
        flash(str(error), "danger")
    else:
        if _is_ajax_request():
            return _ajax_state_response(group_name, f"'{target_name}'을(를) 그룹에 추가했습니다.")
        flash(f"'{target_name}'을(를) 그룹에 추가했습니다.", "success")
    return redirect(_selection_url(group_name))


@custom_group_bp.route("/custom-targets/import", methods=["POST"])
def import_custom_targets_route() -> Response:
    group_name = request.form.get("custom_group", "").strip()
    excel_file = request.files.get("targets_excel")
    skip_header = request.form.get("skip_header") == "on"

    if not group_name:
        if _is_ajax_request():
            return _ajax_state_response("", "먼저 그룹을 선택해 주세요.", "warning")
        flash("먼저 그룹을 선택해 주세요.", "warning")
        return redirect(_selection_url(""))

    if excel_file is None or not excel_file.filename:
        if _is_ajax_request():
            return _ajax_state_response(group_name, "업로드할 엑셀 파일을 선택해 주세요.", "warning")
        flash("업로드할 엑셀 파일을 선택해 주세요.", "warning")
        return redirect(_selection_url(group_name))

    try:
        imported_targets = import_targets_from_excel(excel_file, skip_header=skip_header)
        added_count = add_targets_to_custom_group(group_name, imported_targets)
    except FolderScanError as error:
        if _is_ajax_request():
            return _ajax_state_response(group_name, str(error), "danger")
        flash(str(error), "danger")
    else:
        if _is_ajax_request():
            return _ajax_state_response(group_name, f"엑셀에서 {len(imported_targets)}개를 읽고 {added_count}개를 추가했습니다.")
        flash(f"엑셀에서 {len(imported_targets)}개를 읽고 {added_count}개를 추가했습니다.", "success")
    return redirect(_selection_url(group_name))


@custom_group_bp.route("/custom-targets/template", methods=["GET"])
def download_custom_targets_template() -> Response:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "내그룹대상"
    worksheet["A1"] = "대상명"
    worksheet["A2"] = "홍길동"
    worksheet["A3"] = "김철수"

    guide = workbook.create_sheet("사용방법")
    guide["A1"] = "내그룹 대상 업로드 서식"
    guide["A2"] = "1. 첫 번째 열에 대상명을 한 줄씩 입력합니다."
    guide["A3"] = "2. 첫 행이 제목이면 업로드 화면에서 헤더 제외를 선택합니다."
    guide["A4"] = "3. 빈 값과 중복은 자동으로 제외됩니다."

    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    buffer.seek(0)

    return Response(
        buffer.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="custom_targets_template.xlsx"'},
    )


@custom_group_bp.route("/custom-targets/delete", methods=["POST"])
def delete_custom_target_route() -> Response:
    group_name = request.form.get("custom_group", "").strip()
    target_names = request.form.getlist("delete_target_name")
    if not target_names:
        target_names = request.form.getlist("delete_target_names")
    target_name = request.form.get("delete_target_name", request.form.get("target_name", "")).strip()
    if not group_name:
        if _is_ajax_request():
            return _ajax_state_response("", "먼저 그룹을 선택해 주세요.", "warning")
        flash("먼저 그룹을 선택해 주세요.", "warning")
        return redirect(_selection_url(""))
    try:
        if len(target_names) > 1:
            removed_count = delete_targets_from_custom_group(group_name, target_names)
            if _is_ajax_request():
                return _ajax_state_response(group_name, f"선택한 대상 {removed_count}개를 그룹에서 삭제했습니다.")
            flash(f"선택한 대상 {removed_count}개를 그룹에서 삭제했습니다.", "success")
        else:
            delete_target_from_custom_group(group_name, target_name)
            if _is_ajax_request():
                return _ajax_state_response(group_name, f"'{target_name}'을(를) 그룹에서 삭제했습니다.")
            flash(f"'{target_name}'을(를) 그룹에서 삭제했습니다.", "success")
    except FolderScanError as error:
        if _is_ajax_request():
            return _ajax_state_response(group_name, str(error), "danger")
        flash(str(error), "danger")
    return redirect(_selection_url(group_name))
