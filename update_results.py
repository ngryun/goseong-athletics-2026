"""강원체육대회 운영지원포털의 육상 공식 기록을 official.json에 반영합니다.

사용법:  python update_results.py [--all]

index.html의 일정 데이터(고성 학생)와 포털의 경기를 학교·이름·종목·라운드로 맞춰
학생(계주는 팀)별 순위·기록과 예선 통과 여부를 적습니다. 결과가 바뀔 때만 파일을 고칩니다.
예선 통과 여부는 같은 종목 결승 명단에 이름이 있는지로 판단합니다. 표준 라이브러리만 씁니다.

포털에 부담을 덜 주려고 이미 결과를 받은 학생의 경기는 다시 읽지 않습니다.
공식 기록이 나중에 고쳐졌을 때처럼 전부 다시 읽으려면 --all 을 붙입니다.
"""
import datetime as dt
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

LIST_URL = "https://gwe.go.kr/sports/race/view.do?key=2501060067&spcpSeCd=004&raceClsCd=001"
POPUP_URL = "https://gwe.go.kr/sports/race/getPopupList.do"
HERE = Path(__file__).parent
HTML = HERE / "index.html"
OUT = HERE / "official.json"
UA = {"User-Agent": "Mozilla/5.0 (goseong-athletics-2026 results)"}
KST = dt.timezone(dt.timedelta(hours=9))
REGION = "고성"  # 계주는 지역 선발팀(예: '고성선발', 참가 지역 '고성')으로 나옵니다.
STATUS = {"DNS": "불참", "DNF": "기권", "DQ": "실격", "DSQ": "실격", "NM": "기록 없음"}

ROW = re.compile(
    r'<td class="c1_0">([^<]*)</td>\s*<td class="c2_0">([^<]*)</td>\s*<td class="c3_0">([^<]*)</td>\s*'
    r'<td class="cursor">\s*<a[^>]*openPop\(\'(\d+)\'\)[^>]*>\s*([^<]*?)\s*</a>\s*</td>\s*'
    r'<td class="cursor">\s*<span class="[^"]*">([^<]*)</span>')


def fetch(url, data=None):
    body = urllib.parse.urlencode(data).encode() if data else None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, body, UA), timeout=30) as res:
                return res.read().decode("utf-8", "replace")
        except OSError:
            if attempt == 2:
                raise
            time.sleep(3)


def norm_school(s):
    return s.replace(" ", "").replace("초등학교", "초").replace("중학교", "중").replace("고등학교", "고")


def norm_event(s):
    """'트랙 80m' → '80m', '트랙 4X100mR'·'400mR' → '4×100mR' 처럼 일정표 표기로 맞춥니다."""
    s = re.sub(r"^(트랙|필드|도로)\s*", "", s.strip()).replace(" ", "")
    if re.search(r"4[x×X]100|^400mR$|400m계주", s):
        return "4×100mR"
    if re.search(r"4[x×X]400|^1600mR$|1600m계주", s):
        return "4×400mR"
    return s


def is_relay(event):
    return event.endswith("R")


def res_key(r, stage):
    # index.html의 resKey와 똑같이 만들어야 합니다.
    if is_relay(r["event"]):
        return "|".join([r["school"], r["gender"], r["event"], stage])
    return "|".join([r["school"], str(r["grade"]), r["name"], r["event"], stage])


def read_schedule():
    html = HTML.read_text(encoding="utf-8")
    m = re.search(r'<script id="schedule-data" type="application/json">(.*?)</script>', html, re.S)
    rows = []
    for school, grade, gender, name, event, _date, _time, round_, _note in json.loads(m.group(1).replace("<\\/", "</"))["rows"]:
        rows.append({
            "school": school, "grade": int(grade), "gender": gender, "name": str(name).replace(" ", ""),
            "event": event, "stage": "예선" if str(round_).startswith("예선") else "결승",
            "level": "중등부" if school.endswith("중") else "초등부",
        })
    return rows


def list_races():
    """포털에 올라온 날짜별 경기 목록. 아직 안 올라온 날은 '조회된 내용이 없습니다'라서 건너뜁니다."""
    first = fetch(LIST_URL)
    today = dt.datetime.now(KST).strftime("%Y%m%d")
    days = sorted(set(re.findall(r'<option value="(20\d{6})"', first)))
    races = []
    for ymd in days:
        if ymd > today:
            continue
        page = fetch(f"{LIST_URL}&raceYmd={ymd}")
        for group, cat, typ, sn, label, state in ROW.findall(page):
            m = re.match(r"(남|여)자\s*(초등부|중등부)\s*(?:(\d)학년)?", cat.strip())
            if not m or not re.match(r"(예선|결승)", label):
                continue
            races.append({
                "sn": sn, "group": group.strip(), "cat": cat.strip(), "typ": typ.strip(),
                "gender": m.group(1), "level": m.group(2), "grade": int(m.group(3)) if m.group(3) else None,
                "event": norm_event(typ), "stage": "예선" if label.startswith("예선") else "결승",
                "state": state.strip(),
            })
    return races


def entries(sn):
    item = json.loads(fetch(POPUP_URL, {"raceSn": sn}))[0]
    out = []
    for x in item.get("iemList") or []:
        out.append({
            "school": norm_school(x.get("schlNm") or ""), "name": (x.get("plyrNm") or "").replace(" ", ""),
            "region": (x.get("ptcpRgnNm") or "").strip(),
            "rnk": str(x.get("rnk") or "").strip(), "rcd": str(x.get("rcd") or "").strip(),
        })
    return out


def value(e):
    v = {}
    if e["rnk"].isdigit() and int(e["rnk"]) > 0:
        v["rank"] = int(e["rnk"])
    if e["rcd"].upper() in STATUS:
        v["status"] = STATUS[e["rcd"].upper()]
    elif e["rcd"]:
        v["record"] = e["rcd"]
    return v


def fits(race, r):
    if race["gender"] != r["gender"] or race["level"] != r["level"] or race["event"] != r["event"]:
        return False
    # 초등부 계주도 학년별로 따로 뛰므로 학년까지 맞춥니다. 학년이 섞인 팀은 팀원 중 한 명만 맞으면 됩니다.
    return race["grade"] is None or race["grade"] == r["grade"]


def find(es, r):
    for e in es:
        if is_relay(r["event"]):
            # 학교 팀이거나 고성 선발팀(여러 학교 학생이 한 팀). 선발팀이면 팀원 학교마다 같은 결과가 들어갑니다.
            if e["school"] == r["school"] or e["region"] == REGION or e["school"].startswith(REGION + "선발"):
                return e
        elif e["school"] == r["school"] and e["name"] == r["name"]:
            return e
    return None


def done(r, old):
    """이 학생의 이 라운드 결과를 이미 다 받았는지. 예선은 통과 여부까지, 결승은 예선 탈락이면 끝."""
    v = old.get(res_key(r, r["stage"]), {})
    has = any(k in v for k in ("rank", "record", "status"))
    if r["stage"] == "예선":
        return has and "adv" in v
    return has or old.get(res_key(r, "예선"), {}).get("adv") is False


def wanted(race, rows, old):
    # 예정인 예선은 아직 볼 게 없습니다. 결승은 명단만 있어도 예선 통과 여부를 알 수 있어 읽습니다.
    if race["stage"] == "예선" and race["state"] == "예정":
        return False
    return any(fits(race, r) and not done(r, old) and (r["stage"] == race["stage"] or race["stage"] == "결승")
               for r in rows)


def main():
    refresh = "--all" in sys.argv[1:]
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    known = {} if refresh else old.get("r", {})
    rows = read_schedule()
    races = [x for x in list_races() if any(fits(x, r) for r in rows)]
    got = {}
    for race in races:
        if wanted(race, rows, known):
            got[race["sn"]] = entries(race["sn"])
            time.sleep(0.3)

    results = dict(known)
    for r in rows:
        mine = [x for x in races if x["sn"] in got and x["stage"] == r["stage"] and fits(x, r)]
        for race in mine:
            e = find(got[race["sn"]], r)
            if not e:
                continue
            v = value(e)
            if r["stage"] == "예선":
                finals = [x for x in races if x["stage"] == "결승" and x["cat"] == race["cat"]
                          and x["typ"] == race["typ"] and got.get(x["sn"])]
                if finals and (v or race["state"] == "종료"):
                    v["adv"] = any(find(got[x["sn"]], r) for x in finals)
            if v:
                results[res_key(r, r["stage"])] = v
            break

    print(f"공식 결과 {len(results)}건 (관련 경기 {len(races)}개, 이번에 읽은 경기 {len(got)}개)")
    if old.get("r") == results:
        print("바뀐 내용 없음")
        return
    data = {"updatedAt": dt.datetime.now(KST).isoformat(timespec="seconds"), "source": LIST_URL, "r": results}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("official.json 갱신")


if __name__ == "__main__":
    sys.exit(main())
