"""운영 §3 - 데이터 자동 갱신 배치 (공공 API 일 1회).
API 수집 -> 체험·도서 가공 -> 검토 -> 연계 -> DB 재구축 -> 신선도 -> 품질 가드.
한 단계라도 실패하면 즉시 중단하고 종료코드 1 (자동화는 커밋하지 않음, 기존 데이터 유지).

제외 단계와 이유
- extract_topics.py (주제 12개 재추출): 매일 바꾸면 인물·직업 매칭과 주제 id가 흔들린다. 분기 1회 수동 실행.
- collect_people.py / collect_jobs.py: API와 무관한 정적 데이터이고, 직업 자산(maps_assets)이 저장소에 없어 CI에서 재생성 불가.

실행: cd real && python scripts/refresh.py
"""
import sys, subprocess, os
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, TODAY

STEPS = [
    ("TourAPI 수집", "scripts/collect_tourapi.py"),
    ("정보나루 API 수집", "scripts/collect_data4library.py"),
    ("체험 태깅", "scripts/collect_experiences.py"),
    ("도서 선정", "scripts/collect_books.py"),
    ("검토", "scripts/validate.py"),
    ("연계", "scripts/build_linkage.py"),
    ("DB 재구축", "scripts/build_db.py"),
    ("신선도 갱신", "scripts/freshness.py"),
    ("품질 가드", "scripts/guard.py"),
]


def main():
    # 이전 실행의 게이트 결과가 남아 가드를 잘못 통과시키지 않도록 먼저 지운다
    for g in ("g2", "g3", "g4"):
        fp = rp("state", f"{g}_result.txt")
        if os.path.exists(fp):
            os.remove(fp)
    py = sys.executable
    log = [f"# 데이터 자동 갱신 {TODAY.isoformat()}"]
    code = 0
    for name, script in STEPS:
        r = subprocess.run([py, script], cwd=rp(), capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        ok = r.returncode == 0
        tail = (r.stdout.strip().splitlines() or [""])[-1]
        status = "OK" if ok else f"FAIL({r.returncode})"
        log.append(f"- [{status}] {name}: {tail}")
        print(log[-1], flush=True)
        if not ok:
            if r.stderr.strip():
                log.append("    stderr: " + r.stderr.strip()[-400:])
                print(log[-1])
            code = 1
            break
    with open(rp("state", "refresh_log.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print("갱신 완료" if code == 0 else "갱신 중단: 기존 데이터 유지")
    sys.exit(code)


if __name__ == "__main__":
    main()
