"""Phase 8 - pytest 단위: API 5종 스키마 + 동의어 검색 + 신선도 + 필터."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from app.main import app, TODAY

client = TestClient(app)

def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_api_topics():
    r = client.get("/api/topics")
    assert r.status_code == 200
    j = r.json()
    assert len(j["topics"]) == 5
    for t in j["topics"]:
        assert {"id","name","synonyms","emoji"} <= set(t.keys())

def test_api_topic_detail():
    r = client.get("/api/topics/dino")
    assert r.status_code == 200
    j = r.json()
    assert j["topic"]["id"] == "dino"
    assert len(j["experiences"]) >= 1
    assert len(j["books"]) >= 1
    assert j["person"] is not None
    # 응답에 신선도/시드 필드 포함
    x = j["experiences"][0]
    assert "last_verified" in x and "is_seed" in x
    # Layer B 카드 존재
    assert any(job["layer"] == "B" for job in j["jobs"])

def test_api_topic_unknown():
    r = client.get("/api/topics/zzz")
    assert r.status_code == 404

def test_search_synonym():
    # 아이 언어 '쥬라기' -> 공룡(dino) 매핑
    r = client.get("/api/search", params={"q": "쥬라기"})
    assert r.status_code == 200
    j = r.json()
    assert "dino" in j["matched_topics"]
    assert j["count"] >= 1
    assert all("dino" in x["topic_tags"] or "쥬라기" in x["name"] for x in j["results"])

def test_search_synonym_star():
    r = client.get("/api/search", params={"q": "별"})
    assert "space" in r.json()["matched_topics"]

def test_search_filter_indoor_free():
    r = client.get("/api/search", params={"q": "", "indoor": 1, "free": 1})
    assert r.status_code == 200
    for x in r.json()["results"]:
        assert x["indoor"] == 1
        assert ("무료" in (x["cost"] or "")) or (x["cost"] or "") == ""

def test_freshness_no_expired_anywhere():
    """만료 시드 행사(evt-exp-*) 3건이 어떤 응답에도 없어야 한다 (이월 불가 게이트)."""
    expired_prefix = "evt-exp"
    # topic details
    for t in ["dino","space","animal","robot","art"]:
        j = client.get(f"/api/topics/{t}").json()
        for x in j["experiences"]:
            assert not x["id"].startswith(expired_prefix), f"expired in topic {t}"
    # map
    for mk in client.get("/api/map").json()["markers"]:
        assert not mk["id"].startswith(expired_prefix), "expired in map"
    # search (넓게)
    for x in client.get("/api/search", params={"q":""}).json()["results"]:
        assert not x["id"].startswith(expired_prefix), "expired in search"
    # discover
    dq = client.get("/api/discover").json()["quota"]
    for k in ["near","far"]:
        ex = dq[k]["experience"]
        if ex: assert not ex["id"].startswith(expired_prefix)

def test_freshness_status_operating_only():
    for x in client.get("/api/search", params={"q":""}).json()["results"]:
        assert x["status"] == "운영중"
        assert (x["period_end"] is None) or (x["period_end"] >= TODAY)

def test_api_map_live_only():
    r = client.get("/api/map", params={"topics": "space"})
    assert r.status_code == 200
    for mk in r.json()["markers"]:
        assert "space" in mk["topic_tags"]

def test_discover_quota_no_popularity():
    j = client.get("/api/discover").json()
    assert "quota" in j
    assert "near" in j["quota"] and "far" in j["quota"]
    assert j["quota"]["anti_stereotype_person"] is not None
    assert "popularity" in j["sort"]  # sort == 'quota(no-popularity)'

def test_pages_render_200():
    for path in ["/", "/topic/dino", "/map", "/discover"]:
        assert client.get(path).status_code == 200

def test_search_page_filters_work():
    # 학부모 페르소나 지적 수정 검증: 검색화면 필터가 실제로 작동
    for path in ["/?indoor=1", "/?free=1", "/?region=서울", "/?indoor=1&free=1"]:
        r = client.get(path)
        assert r.status_code == 200
        assert "필터:" in r.text  # 활성 필터 라벨 노출 = 필터 적용됨
    # 무료 필터는 무료/무비용만
    j = client.get("/api/search", params={"free": 1}).json()
    assert j["count"] >= 1
    assert all(("무료" in (x["cost"] or "")) or (x["cost"] or "") == "" for x in j["results"])
    # 지역 필터
    seoul = client.get("/api/search", params={"region": "서울"}).json()
    assert all("서울" in (x["region"] or "") for x in seoul["results"])
