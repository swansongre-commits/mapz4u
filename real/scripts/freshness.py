"""운영 §3.3 - 신선도 감시. last_verified 90일 초과 -> recheck_queue 등록. 대시보드 리포트 산출.
"만료 정보 노출 0건"이 품질 제1지표 (기획서 H2)."""
import sys, sqlite3, datetime
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, TODAY

DB = rp("db", "mapz_real.db")
STALE_DAYS = 90

def main():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; cur = con.cursor()
    cur.execute("DELETE FROM recheck_queue")
    today = TODAY
    # 신선도 통계
    total = cur.execute("SELECT COUNT(*) FROM experience").fetchone()[0]
    operating = cur.execute("SELECT COUNT(*) FROM experience WHERE status='운영중'").fetchone()[0]
    # 만료 노출 위험: period_end < today 인데 status='운영중'
    expired_live = cur.execute(
        "SELECT COUNT(*) FROM experience WHERE status='운영중' AND period_end IS NOT NULL AND period_end!='' AND period_end < ?",
        (today.isoformat(),)).fetchone()[0]
    # 재확인 큐: last_verified 90일 초과
    stale = 0
    for r in cur.execute("SELECT id,name,last_verified FROM experience").fetchall():
        try:
            lv = datetime.date.fromisoformat(r["last_verified"])
        except Exception:
            continue
        over = (today - lv).days
        if over > STALE_DAYS:
            cur.execute("INSERT INTO recheck_queue VALUES(?,?,?,?,?,?)",
                        (r["id"], "experience", r["name"], r["last_verified"], over, today.isoformat()))
            stale += 1
    con.commit()
    # 소스 구성
    src = cur.execute("SELECT source,COUNT(*) c FROM experience GROUP BY source ORDER BY c DESC").fetchall()
    con.close()

    md = ["# 신선도 대시보드 (운영 §3.3)\n", f"- 기준일: {today.isoformat()}\n",
          "| 지표 | 값 |", "|---|---|",
          f"| 전체 체험 | {total} |",
          f"| 운영중 | {operating} |",
          f"| **만료 노출 위험(운영중인데 종료일 지남)** | **{expired_live}** (0이어야 정상) |",
          f"| 재확인 필요(최종확인 {STALE_DAYS}일 초과) | {stale} |",
          "\n## 소스 구성",""]
    for s in src:
        md.append(f"- {s['source']}: {s['c']}건")
    md.append(f"\n## 판정")
    md.append(f"- 만료 노출 0건: {'PASS' if expired_live==0 else 'FAIL(' + str(expired_live) + ')'}")
    md.append(f"- 재확인 큐 {stale}건 등록 (다음 배치 우선 재수집 대상)")
    open(rp("reports", "freshness_dashboard.md"), "w", encoding="utf-8").write("\n".join(md))
    print(f"신선도: 전체 {total} / 운영중 {operating} / 만료노출위험 {expired_live} / 재확인큐 {stale}")

if __name__ == "__main__":
    main()
