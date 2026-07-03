"""MAPZ 운영버전 FastAPI 앱. 동적 12주제(Phase 0.5 산출). 실데이터(TourAPI/정보나루).
MVP(mapz/app)를 import하지 않고 복사·적응. 추가: §5 rate limiting, §7 출처표시 footer."""
import os, json, sqlite3, datetime, time, threading
from collections import deque, defaultdict
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # real/
DB = os.path.join(ROOT, "db", "mapz_real.db")
RUN_DATE = os.environ.get("MAPZ_RUN_DATE", "2026-07-04")
TODAY = RUN_DATE

app = FastAPI(title="MAPZ 운영 — 어린이 체험지도")
app.mount("/static", StaticFiles(directory=os.path.join(ROOT, "app", "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(ROOT, "app", "templates"))

# ── §5 rate limiting (IP 기준, 인메모리 슬라이딩 윈도우) ──
RATE_LIMIT = int(os.environ.get("MAPZ_RATE_LIMIT", "180"))  # req/min/IP
_hits = defaultdict(deque); _lock = threading.Lock()
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith("/static"):
        return await call_next(request)
    ip = request.client.host if request.client else "?"
    now = time.time()
    with _lock:
        dq = _hits[ip]
        while dq and dq[0] < now - 60: dq.popleft()
        if len(dq) >= RATE_LIMIT:
            return PlainTextResponse("요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.", status_code=429)
        dq.append(now)
    return await call_next(request)

TOPICS = {}
# 12색 팔레트 (주제당 포인트 1색)
PALETTE = ["#5B8C5A","#3A5BA0","#C77D3E","#5A5AA0","#B0507A","#2C8C8C","#8C6D3A","#7A4FA0",
           "#3E8C6B","#A0503E","#6B8C3A","#8C3A6B"]

def db():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; return con
def jl(s):
    try: return json.loads(s) if s else []
    except Exception: return []

def load_topics():
    con = db()
    for i, r in enumerate(con.execute("SELECT * FROM topic ORDER BY connection_score DESC")):
        TOPICS[r["id"]] = {"id": r["id"], "name": r["name"], "synonyms": jl(r["synonyms"]),
                           "emoji": r["emoji"], "color": PALETTE[i % len(PALETTE)],
                           "demand": r["demand_score"], "connection": r["connection_score"]}
    con.close()
load_topics()

FRESH = "status='운영중' AND (period_end IS NULL OR period_end='' OR period_end >= ?)"
def _plus_days(n): return (datetime.date.fromisoformat(TODAY) + datetime.timedelta(days=n)).isoformat()

def exp_row(r):
    return {"id": r["id"], "name": r["name"], "type": r["type"], "topic_tags": jl(r["topic_tags"]),
            "lat": r["lat"], "lng": r["lng"], "region": r["region"], "period_start": r["period_start"],
            "period_end": r["period_end"], "hours": r["hours"], "age_note": r["age_note"], "cost": r["cost"],
            "indoor": r["indoor"], "reservation_url": r["reservation_url"], "tel": r["tel"], "image": r["image"],
            "source": r["source"], "is_seed": r["is_seed"], "last_verified": r["last_verified"], "status": r["status"],
            "maplink": f'https://www.openstreetmap.org/?mlat={r["lat"]}&mlon={r["lng"]}#map=16/{r["lat"]}/{r["lng"]}'}
def book_row(r):
    return {"isbn": r["isbn"], "title": r["title"], "author": r["author"], "publisher": r["publisher"],
            "age_band": r["age_band"], "topic_tags": jl(r["topic_tags"]), "loan_count": r["loan_count"],
            "availability": r["availability"], "source": r["source"], "is_seed": r["is_seed"], "last_verified": r["last_verified"]}
def person_row(r):
    return {"id": r["id"], "name": r["name"], "era": r["era"], "verb_desc": r["verb_desc"],
            "story_trial": r["story_trial"], "job_lineage": jl(r["job_lineage"]),
            "anti_stereotype": r["anti_stereotype"], "topic_tags": jl(r["topic_tags"])}
def linkage(): return json.load(open(os.path.join(ROOT, "data", "clean", "linkage.json"), encoding="utf-8"))

@app.get("/healthz")
def healthz(): return {"status": "ok", "today": TODAY, "topics": len(TOPICS), "track": "real"}

@app.get("/api/topics")
def api_topics(): return {"today": TODAY, "topics": [TOPICS[t] for t in TOPICS]}

@app.get("/api/topics/{tid}")
def api_topic_detail(tid: str):
    if tid not in TOPICS: return JSONResponse({"error": "unknown topic"}, status_code=404)
    L = linkage()["topics"].get(tid, {}); con = db(); exps = []
    for e in L.get("experiences", []):
        r = con.execute(f"SELECT * FROM experience WHERE id=? AND {FRESH}", (e["id"], TODAY)).fetchone()
        if r: exps.append(exp_row(r))
    bks = [book_row(con.execute("SELECT * FROM book WHERE isbn=?", (b["isbn"],)).fetchone()) for b in L.get("books", []) if con.execute("SELECT 1 FROM book WHERE isbn=?", (b["isbn"],)).fetchone()]
    person = None
    if L.get("person"):
        r = con.execute("SELECT * FROM person WHERE id=?", (L["person"]["id"],)).fetchone()
        if r: person = person_row(r)
    jobs = []
    for j in L.get("jobs", []):
        r = con.execute("SELECT * FROM job WHERE id=?", (j["id"],)).fetchone()
        if r: jobs.append({"id": r["id"], "name": r["name"], "verb_desc": r["verb_desc"], "layer": r["layer"], "emoji": r["emoji"]})
    adj = linkage()["adjacency"].get(tid, []); con.close()
    return {"today": TODAY, "topic": TOPICS[tid], "experiences": exps, "books": bks,
            "person": person, "jobs": jobs, "layerB_card": L.get("layerB_card"), "adjacency": adj}

@app.get("/api/search")
def api_search(q: str = "", indoor: int = 0, free: int = 0, region: str = ""):
    con = db(); rows = [exp_row(r) for r in con.execute(f"SELECT * FROM experience WHERE {FRESH}", (TODAY,))]; con.close()
    mt = [tid for tid, t in TOPICS.items() if q and (q in t["name"] or any(s in q or q in s for s in t["synonyms"]))] if q else []
    def ok(x):
        if q and not (any(t in mt for t in x["topic_tags"]) or q in x["name"] or q in (x["region"] or "")): return False
        if indoor and not x["indoor"]: return False
        if free and not (("무료" in (x["cost"] or "")) or (x["cost"] or "") == ""): return False
        if region and region not in (x["region"] or ""): return False
        return True
    res = [x for x in rows if ok(x)]
    return {"today": TODAY, "query": q, "matched_topics": mt, "count": len(res), "results": res[:60]}

@app.get("/api/map")
def api_map(bbox: str = "", topics: str = ""):
    con = db(); rows = [exp_row(r) for r in con.execute(f"SELECT * FROM experience WHERE {FRESH}", (TODAY,))]; con.close()
    want = [t for t in topics.split(",") if t] if topics else []; markers = []
    for x in rows:
        if want and not any(t in want for t in x["topic_tags"]): continue
        if bbox:
            try:
                s, w, n, e = [float(v) for v in bbox.split(",")]
                if not (s <= x["lat"] <= n and w <= x["lng"] <= e): continue
            except Exception: pass
        markers.append({"id": x["id"], "name": x["name"], "lat": x["lat"], "lng": x["lng"], "topic_tags": x["topic_tags"],
                        "region": x["region"], "type": x["type"], "last_verified": x["last_verified"], "is_seed": x["is_seed"], "maplink": x["maplink"]})
    return {"today": TODAY, "count": len(markers), "markers": markers}

@app.get("/api/discover")
def api_discover():
    L = linkage(); dq = L["discover_quota"]; con = db()
    def one(eid):
        if not eid: return None
        r = con.execute(f"SELECT * FROM experience WHERE id=? AND {FRESH}", (eid, TODAY)).fetchone()
        return exp_row(r) if r else None
    near, far = dq["near"], dq["far"]
    ne = one(near["sample_exp"]["id"] if near.get("sample_exp") else None)
    fe = one(far["sample_exp"]["id"] if far.get("sample_exp") else None)
    pr = con.execute("SELECT * FROM person WHERE id=?", (dq["anti_stereotype_person"]["id"],)).fetchone(); con.close()
    return {"today": TODAY, "sort": "quota(no-popularity)",
            "quota": {"near": {"topic": near["topic"], "name": near["name"], "experience": ne},
                      "far": {"topic": far["topic"], "name": far["name"], "experience": fe},
                      "anti_stereotype_person": person_row(pr) if pr else None}, "rule": dq["rule"]}

@app.get("/", response_class=HTMLResponse)
def page_search(request: Request, q: str = "", indoor: int = 0, free: int = 0, region: str = "", week: int = 0):
    af = bool(q or indoor or free or region or week)
    if af:
        d = api_search(q=q, indoor=indoor, free=free, region=region); results = d["results"]
        if week: results = [x for x in results if x["type"] == "상설시설" or (x["period_start"] and x["period_start"] <= _plus_days(7))]
    else: results = []
    con = db(); preview = [exp_row(r) for r in con.execute(f"SELECT * FROM experience WHERE {FRESH} AND type='상설시설' LIMIT 6", (TODAY,))]; con.close()
    return templates.TemplateResponse(request, "search.html", {"topics": [TOPICS[t] for t in TOPICS], "results": results,
        "query": q, "f": {"indoor": indoor, "free": free, "region": region, "week": week}, "active_filter": af,
        "preview": preview, "today": TODAY, "active": "search"})

@app.get("/topic/{tid}", response_class=HTMLResponse)
def page_topic(request: Request, tid: str):
    if tid not in TOPICS: return HTMLResponse("<h1>알 수 없는 주제</h1>", status_code=404)
    return templates.TemplateResponse(request, "topic.html", {"d": api_topic_detail(tid), "topic": TOPICS[tid],
        "topics_all": TOPICS, "today": TODAY, "active": "topic"})

@app.get("/map", response_class=HTMLResponse)
def page_map(request: Request):
    return templates.TemplateResponse(request, "map.html", {"markers": api_map()["markers"],
        "topics": [TOPICS[t] for t in TOPICS], "topic_colors": {t: TOPICS[t]["color"] for t in TOPICS},
        "today": TODAY, "active": "map"})

@app.get("/discover", response_class=HTMLResponse)
def page_discover(request: Request):
    d = api_discover()
    return templates.TemplateResponse(request, "discover.html", {"q": d["quota"], "topics_all": TOPICS,
        "rule": d["rule"], "today": TODAY, "active": "discover"})
