"""엑셀 경기일정을 index.html에 반영합니다.

사용법:  python update_data.py [엑셀 파일 경로]

경로를 생략하면 DEFAULT_XLSX를 읽습니다. 첫 번째 시트('학생별 일정')에서
'학교' 머리글 아래 행을 학교·학년·성별·성명·종목·일자·시간·라운드·비고 순서로 읽고,
'※'로 시작하는 안내 문구도 함께 가져옵니다.
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

import openpyxl

DEFAULT_XLSX = r"D:\2026 문화체육특수_남궁\1. 체육\16. 교육감기 학년별 육상대회\2026 교육감기 학년별 육상대회 학생별 경기일정.xlsx"
HTML = Path(__file__).with_name("index.html")
BLOCK = re.compile(r'(<script id="schedule-data" type="application/json">)(.*?)(</script>)', re.S)
DOW = "월화수목금토일"


def cell(v):
    if v is None:
        return ""
    if isinstance(v, dt.datetime):
        return f"{v.month}. {v.day}.({DOW[v.weekday()]})"
    if isinstance(v, dt.time):
        return v.strftime("%H:%M")
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v.strip() if isinstance(v, str) else v


def read_schedule(path):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    note, rows, in_table = "", [], False
    for raw in ws.iter_rows(values_only=True):
        r = [cell(v) for v in raw[:9]]
        r += [""] * (9 - len(r))
        if not in_table:
            if r[0] == "학교":
                in_table = True
            elif isinstance(r[0], str) and r[0].startswith("※"):
                note = r[0].lstrip("※ ").strip()
            continue
        if r[0] and r[3]:
            rows.append(r)
    return {"note": note, "rows": rows}


def main():
    xlsx = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_XLSX
    data = read_schedule(xlsx)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = HTML.read_text(encoding="utf-8")
    if not BLOCK.search(html):
        sys.exit("index.html에서 데이터 블록을 찾지 못했습니다.")
    HTML.write_text(BLOCK.sub(lambda m: m.group(1) + payload + m.group(3), html, count=1), encoding="utf-8")
    students = {(r[0], r[1], r[3]) for r in data["rows"]}
    print(f"반영 완료: 학생 {len(students)}명, 일정 {len(data['rows'])}건")


if __name__ == "__main__":
    main()
