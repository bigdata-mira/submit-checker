from __future__ import annotations

import csv
from io import StringIO


def export_results_to_csv(rows: list[dict[str, str]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["상태", "대상", "제출파일명", "파일개수", "제출시간", "비고"],
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
