"""Phase 9 - 성능 스모크(p95) + 렌더 HTML 스냅샷(페르소나 증빙용)."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from app.main import app
from common import p

client = TestClient(app)
endpoints = ["/api/topics", "/api/topics/dino", "/api/search?q=쥬라기",
             "/api/map?topics=space", "/api/discover", "/healthz"]

# 성능: 각 30회 측정 p95
import statistics
rows = []
for ep in endpoints:
    ts = []
    for _ in range(30):
        t0 = time.perf_counter(); client.get(ep); ts.append((time.perf_counter()-t0)*1000)
    ts.sort()
    p95 = ts[int(0.95*len(ts))-1]
    rows.append((ep, round(statistics.mean(ts),1), round(p95,1)))

# 렌더 스냅샷
os.makedirs(p("reports","rendered"), exist_ok=True)
for path, name in [("/","search"),("/topic/dino","topic"),("/map","map"),("/discover","discover")]:
    html = client.get(path).text
    open(p("reports","rendered",f"{name}.html"),"w",encoding="utf-8").write(html)

lines = ["# 성능 스모크 (로컬 TestClient, 30회, p95)\n","| API | 평균ms | p95ms |","|---|---|---|"]
allp95 = []
for ep,mean,p95 in rows:
    lines.append(f"| {ep} | {mean} | {p95} |"); allp95.append(p95)
overall = max(allp95)
lines.append(f"\n- 전체 최대 p95: **{overall}ms** (목표 <500ms: {overall<500})")
open(p("reports","perf_smoke.md"),"w",encoding="utf-8").write("\n".join(lines))
open(p("state","perf_result.txt"),"w",encoding="utf-8").write(f"max_p95={overall}ms target<500:{overall<500}")
print("\n".join(lines))
print("렌더 스냅샷 4종 -> reports/rendered/")
