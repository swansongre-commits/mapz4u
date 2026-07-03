"""MAPZ FastAPI 앱 — 4 화면 + 6 API. 신선도 불변식: status='운영중' AND period_end>=today.
응답에 last_verified·is_seed 포함. 인기순 정렬 없음(발견=쿼터 편성)."""
import os, json, sqlite3, datetime
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "mapz.db")
RUN_DATE = os.environ.get("MAPZ_RUN_DATE", "2026-07-04")
TODAY = RUN_DATE

app = FastAPI(title="MAPZ — 어린이 체험지도")
app.mount("/static", StaticFiles(directory=os.path.join(ROOT, "app", "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(ROOT, "app", "templates"))

TOPICS = {}  # loaded at startup

def db():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; return con

def jl(s):
    try: return json.loads(s) if s else []
    except Exception: return []

def load_topics():
    con = db()
    for r in con.execute("SELECT * FROM topic"):
        TOPICS[r["id"]] = {"id": r["id"], "name": r["name"],
                           "synonyms": jl(r["synonyms"]), "emoji": r["emoji"]}
    con.close()
load_topics()

FRESH = "status='운영중' AND (period_end IS NULL OR period_end='' OR period_end >= ?)"

def _plus_days(n):
    return (datetime.date.fromisoformat(TODAY) + datetime.timedelta(days=n)).isoformat()

def exp_row(r):
    return {"id": r["id"], "name": r["name"], "type": r["type"],
            "topic_tags": jl(r["topic_tags"]), "verb_tags": jl(r["verb_tags"]),
            "lat": r["lat"], "lng": r["lng"], "region": r["region"],
            "period_start": r["period_start"], "period_end": r["period_end"],
            "hours": r["hours"], "age_note": r["age_note"], "cost": r["cost"],
            "indoor": r["indoor"], "reservation_url": r["reservation_url"],
            "related_books": jl(r["related_books"]),
            "source": r["source"], "is_seed": r["is_seed"],
            "last_verified": r["last_verified"], "status": r["status"],
            "maplink": f'https://www.openstreetmap.org/?mlat={r["lat"]}&mlon={r["lng"]}#map=17/{r["lat"]}/{r["lng"]}'}

def book_row(r):
    return {"isbn": r["isbn"], "title": r["title"], "author": r["author"],
            "publisher": r["publisher"], "age_band": r["age_band"], "kdc": r["kdc"],
            "topic_tags": jl(r["topic_tags"]), "availability": r["availability"],
            "source": r["source"], "is_seed": r["is_seed"], "last_verified": r["last_verified"]}

def person_row(r):
    return {"id": r["id"], "name": r["name"], "era": r["era"], "verb_desc": r["verb_desc"],
            "story_trial": r["story_trial"], "job_lineage": jl(r["job_lineage"]),
            "anti_stereotype": r["anti_stereotype"], "topic_tags": jl(r["topic_tags"])}

def linkage():
    return json.load(open(os.path.join(ROOT, "data", "clean", "linkage.json"), encoding="utf-8"))

# ─────────────── API ───────────────
@app.get("/healthz")
def healthz():
    return {"status": "ok", "today": TODAY}

@app.get("/api/topics")
def api_topics():
    return {"today": TODAY, "topics": [TOPICS[t] for t in TOPICS]}

@app.get("/api/topics/{tid}")
def api_topic_detail(tid: str):
    if tid not in TOPICS:
        return JSONResponse({"error": "unknown topic"}, status_code=404)
    L = linkage()["topics"].get(tid, {})
    con = db()
    # 편성된 체험 중 신선도 통과만
    exps = []
    for e in L.get("experiences", []):
        r = con.execute(f"SELECT * FROM experience WHERE id=? AND {FRESH}", (e["id"], TODAY)).fetchone()
        if r: exps.append(exp_row(r))
    bks = []
    for b in L.get("books", []):
        r = con.execute("SELECT * FROM book WHERE isbn=?", (b["isbn"],)).fetchone()
        if r: bks.append(book_row(r))
    person = None
    if L.get("person"):
        r = con.execute("SELECT * FROM person WHERE id=?", (L["person"]["id"],)).fetchone()
        if r: person = person_row(r)
    jobs = []
    for j in L.get("jobs", []):
        r = con.execute("SELECT * FROM job WHERE id=?", (j["id"],)).fetchone()
        if r: jobs.append({"id": r["id"], "name": r["name"], "verb_desc": r["verb_desc"],
                           "layer": r["layer"], "emoji": r["emoji"], "source_asset": r["source_asset"]})
    adj = linkage()["adjacency"].get(tid, [])
    con.close()
    return {"today": TODAY, "topic": TOPICS[tid], "experiences": exps, "books": bks,
            "person": person, "jobs": jobs, "layerB_card": L.get("layerB_card"), "adjacency": adj}

@app.get("/api/search")
def api_search(q: str = "", indoor: int = 0, free: int = 0, region: str = ""):
    con = db()
    rows = [exp_row(r) for r in con.execute(f"SELECT * FROM experience WHERE {FRESH}", (TODAY,))]
    con.close()
    matched_topics = []
    if q:
        for tid, t in TOPICS.items():
            if q in t["name"] or any(s in q or q in s for s in t["synonyms"]):
                matched_topics.append(tid)
    def ok(x):
        if q:
            hit_topic = any(t in matched_topics for t in x["topic_tags"])
            hit_name = q in x["name"] or q in (x["region"] or "")
            if not (hit_topic or hit_name): return False
        if indoor and not x["indoor"]: return False
        if free and not (("무료" in (x["cost"] or "")) or (x["cost"] or "") == ""): return False
        if region and region not in (x["region"] or ""): return False
        return True
    res = [x for x in rows if ok(x)]
    return {"today": TODAY, "query": q, "matched_topics": matched_topics,
            "count": len(res), "results": res}

@app.get("/api/map")
def api_map(bbox: str = "", topics: str = ""):
    con = db()
    rows = [exp_row(r) for r in con.execute(f"SELECT * FROM experience WHERE {FRESH}", (TODAY,))]
    con.close()
    want = [t for t in topics.split(",") if t] if topics else []
    markers = []
    for x in rows:
        if want and not any(t in want for t in x["topic_tags"]): continue
        if bbox:
            try:
                s, w, n, e = [float(v) for v in bbox.split(",")]
                if not (s <= x["lat"] <= n and w <= x["lng"] <= e): continue
            except Exception: pass
        markers.append({"id": x["id"], "name": x["name"], "lat": x["lat"], "lng": x["lng"],
                        "topic_tags": x["topic_tags"], "region": x["region"], "type": x["type"],
                        "last_verified": x["last_verified"], "is_seed": x["is_seed"],
                        "maplink": x["maplink"]})
    return {"today": TODAY, "count": len(markers), "markers": markers}

@app.get("/api/discover")
def api_discover():
    L = linkage(); dq = L["discover_quota"]; con = db()
    def one(eid):
        if not eid: return None
        r = con.execute(f"SELECT * FROM experience WHERE id=? AND {FRESH}", (eid, TODAY)).fetchone()
        return exp_row(r) if r else None
    near = dq["near"]; far = dq["far"]
    near_exp = one(near["sample_exp"]["id"] if near.get("sample_exp") else None)
    far_exp = one(far["sample_exp"]["id"] if far.get("sample_exp") else None)
    pr = con.execute("SELECT * FROM person WHERE id=?", (dq["anti_stereotype_person"]["id"],)).fetchone()
    con.close()
    return {"today": TODAY, "sort": "quota(no-popularity)",
            "quota": {
                "near": {"topic": near["topic"], "name": near["name"], "experience": near_exp},
                "far": {"topic": far["topic"], "name": far["name"], "experience": far_exp},
                "anti_stereotype_person": person_row(pr) if pr else None},
            "rule": dq["rule"]}

# ─────────────── HTML 화면 ───────────────
@app.get("/", response_class=HTMLResponse)
def page_search(request: Request, q: str = "", indoor: int = 0, free: int = 0, region: str = "", week: int = 0):
    active_filter = bool(q or indoor or free or region or week)
    if active_filter:
        data = api_search(q=q, indoor=indoor, free=free, region=region)
        results = data["results"]
        if week:  # '이번 주' = 7일 내 시작/진행 행사 우선(상설은 상시 유효)
            results = [x for x in results if x["type"] == "상설시설"
                       or (x["period_start"] and x["period_start"] <= _plus_days(7))]
    else:
        results = []
    con = db()
    preview = [exp_row(r) for r in con.execute(f"SELECT * FROM experience WHERE {FRESH} AND type='상설시설' LIMIT 4", (TODAY,))]
    con.close()
    return templates.TemplateResponse(request, "search.html", {"topics": [TOPICS[t] for t in TOPICS],
                                                       "results": results, "query": q,
                                                       "f": {"indoor": indoor, "free": free, "region": region, "week": week},
                                                       "active_filter": active_filter,
                                                       "preview": preview, "today": TODAY, "active": "search"})

@app.get("/topic/{tid}", response_class=HTMLResponse)
def page_topic(request: Request, tid: str):
    if tid not in TOPICS:
        return HTMLResponse("<h1>알 수 없는 주제</h1>", status_code=404)
    d = api_topic_detail(tid)
    return templates.TemplateResponse(request, "topic.html", {"d": d, "topic": TOPICS[tid],
                                                      "topics_all": TOPICS, "today": TODAY, "active": "topic"})

@app.get("/map", response_class=HTMLResponse)
def page_map(request: Request):
    d = api_map()
    return templates.TemplateResponse(request, "map.html", {"markers": d["markers"],
                                                    "topics": [TOPICS[t] for t in TOPICS],
                                                    "today": TODAY, "active": "map"})

@app.get("/discover", response_class=HTMLResponse)
def page_discover(request: Request):
    d = api_discover()
    return templates.TemplateResponse(request, "discover.html", {"q": d["quota"],
                                                        "topics_all": TOPICS, "rule": d["rule"],
                                                        "today": TODAY, "active": "discover"})
