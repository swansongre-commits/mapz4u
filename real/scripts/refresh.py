"""운영 §3 - 데이터 갱신 배치 (Tier1 공공API 일1회 상정). 멱등 재수집 -> 검토 -> 연계 -> DB 재구축.
cron 예: 0 5 * * *  cd /app && python scripts/refresh.py  (매일 05:00)
"""
import sys, subprocess, os
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, TODAY

STEPS = [
    ("TourAPI 재수집", "scripts/collect_tourapi.py"),
    ("체험 태깅", "scripts/collect_experiences.py"),
    ("도서(정보나루 파일)", "scripts/collect_books.py"),
    ("인물", "scripts/collect_people.py"),
    ("직업", "scripts/collect_jobs.py"),
    ("검토", "scripts/validate.py"),
    ("연계", "scripts/build_linkage.py"),
    ("DB 재구축", "scripts/build_db.py"),
    ("신선도 갱신", "scripts/freshness.py"),
]

def main():
    py = sys.executable
    log = [f"# 갱신 배치 {TODAY.isoformat()}"]
    for name, script in STEPS:
        r = subprocess.run([py, script], cwd=rp(), capture_output=True, text=True,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        status = "OK" if r.returncode == 0 else f"FAIL({r.returncode})"
        tail = (r.stdout.strip().splitlines() or [""])[-1]
        log.append(f"- [{status}] {name}: {tail}")
        if r.returncode != 0:
            log.append(f"    stderr: {r.stderr.strip()[:200]}")
    open(rp("state", "refresh_log.md"), "w", encoding="utf-8").write("\n".join(log))
    print("\n".join(log))

if __name__ == "__main__":
    main()
