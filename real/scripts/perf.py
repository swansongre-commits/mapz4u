import sys, os, time, statistics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from app.main import app
from common import rp
c = TestClient(app)
eps = ["/api/topics","/api/topics/art","/api/search?q=우주","/api/map?topics=history","/api/discover","/healthz"]
rows = []
for ep in eps:
    ts = []
    for _ in range(30):
        t0 = time.perf_counter(); c.get(ep); ts.append((time.perf_counter()-t0)*1000)
    ts.sort(); rows.append((ep, round(statistics.mean(ts),1), round(ts[int(0.95*len(ts))-1],1)))
mx = max(p for _,_,p in rows)
md = ["# 운영 성능 스모크 (TestClient, 30회, p95)\n","| API | 평균ms | p95ms |","|---|---|---|"]
md += [f"| {e} | {m} | {p} |" for e,m,p in rows]
md.append(f"\n- 최대 p95: **{mx}ms** (목표 <500ms: {mx<500}) · 실데이터 1568체험 기준")
open(rp("reports","perf_smoke.md"),"w",encoding="utf-8").write("\n".join(md))
print(f"max p95={mx}ms (<500: {mx<500})")
