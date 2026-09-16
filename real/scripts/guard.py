"""갱신 배치 품질 가드.
하나라도 어기면 종료코드 1을 반환한다. 자동화(GitHub Actions)는 이때 커밋·배포하지 않으므로
서비스는 직전의 정상 데이터를 그대로 유지한다.
"""
import sys, os, sqlite3
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, read_json, TODAY

MIN = {"facilities": 1500, "experience": 1000, "book": 40, "topic": 12, "person": 12}


def gate(name):
    fp = rp("state", f"{name}_result.txt")
    if not os.path.exists(fp):
        return False
    with open(fp, encoding="utf-8") as f:
        t = f.read()
    return "PASS" in t and "FAIL" not in t


def main():
    errs = []
    fac = read_json(rp("data", "raw", "tourapi_facilities.json"), [])
    if len(fac) < MIN["facilities"]:
        errs.append(f"TourAPI 문화시설 {len(fac)} < {MIN['facilities']}")
    for g in ("g2", "g3", "g4"):
        if not gate(g):
            errs.append(f"{g.upper()} 게이트 미통과")
    con = sqlite3.connect(rp("db", "mapz_real.db"))
    cnt = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
           for t in ("experience", "book", "topic", "person")}
    expired = con.execute(
        "SELECT COUNT(*) FROM experience WHERE status='운영중' AND period_end IS NOT NULL "
        "AND period_end!='' AND period_end < ?", (TODAY.isoformat(),)).fetchone()[0]
    con.close()
    for t, v in cnt.items():
        if v < MIN[t]:
            errs.append(f"{t} {v} < {MIN[t]}")
    if expired:
        errs.append(f"만료 행사 노출 위험 {expired}건")
    summary = f"기준일 {TODAY.isoformat()} | 문화시설 {len(fac)} | " + " ".join(f"{k}={v}" for k, v in cnt.items())
    if errs:
        print("GUARD FAIL: " + " / ".join(errs))
        print(summary)
        sys.exit(1)
    print("GUARD PASS | " + summary)


if __name__ == "__main__":
    main()
