"""운영 Phase 8 - pytest. 실데이터·동적주제 대응."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from app.main import app, TOPICS, TODAY
client = TestClient(app)

def test_healthz():
    j = client.get("/healthz").json()
    assert j["status"] == "ok" and j["track"] == "real" and j["topics"] >= 8

def test_topics_dynamic():
    j = client.get("/api/topics").json()
    assert len(j["topics"]) >= 8
    for t in j["topics"]:
        assert {"id","name","synonyms","emoji","color"} <= set(t.keys())

def test_topic_detail_realdata():
    tid = list(TOPICS)[0]
    j = client.get(f"/api/topics/{tid}").json()
    assert len(j["experiences"]) >= 1
    # 실데이터 비율 검증: 최소 1건은 TourAPI 실데이터
    assert any(not x["is_seed"] for x in j["experiences"])
    assert any(job["layer"] == "B" for job in j["jobs"])

def test_search_synonym():
    r = client.get("/api/search", params={"q": "우주"}).json()
    assert "space" in r["matched_topics"]

def test_search_filters():
    for p in [{"indoor":1},{"free":1},{"region":"서울"}]:
        r = client.get("/api/search", params=p)
        assert r.status_code == 200
    j = client.get("/api/search", params={"free":1}).json()
    assert all(("무료" in (x["cost"] or "")) or (x["cost"] or "")=="" for x in j["results"])

def test_freshness_operating_only():
    for x in client.get("/api/search", params={"q":""}).json()["results"]:
        assert x["status"] == "운영중"
        assert (x["period_end"] is None) or (x["period_end"] == "") or (x["period_end"] >= TODAY)

def test_map_topic_filter():
    tid = list(TOPICS)[0]
    for mk in client.get("/api/map", params={"topics": tid}).json()["markers"]:
        assert tid in mk["topic_tags"]

def test_discover_quota():
    j = client.get("/api/discover").json()
    assert "near" in j["quota"] and "far" in j["quota"]
    assert "popularity" in j["sort"]

def test_pages_200():
    assert client.get("/").status_code == 200
    assert client.get("/map").status_code == 200
    assert client.get("/discover").status_code == 200
    for tid in list(TOPICS)[:3]:
        assert client.get(f"/topic/{tid}").status_code == 200

def test_rate_limit_headers_ok():
    # 정상 요청은 429 아님
    assert client.get("/healthz").status_code == 200

def test_book_realdata_loan_count():
    tid = list(TOPICS)[0]
    j = client.get(f"/api/topics/{tid}").json()
    if j["books"]:
        assert any(b.get("loan_count", 0) > 0 for b in j["books"])  # 실대출 데이터
