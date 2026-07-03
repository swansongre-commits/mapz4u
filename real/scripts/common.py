"""MAPZ 운영버전 공용 유틸. mapz/real/ 하위 전용 — MVP(mapz/scripts/common.py)와 완전 분리.
하드코딩 주제 딕셔너리를 두지 않는다. Phase 0.5 산출물(topics_v1.json)이 유일한 주제 소스.
"""
import os, json, datetime, re, unicodedata

REAL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # mapz/real/
def rp(*a): return os.path.join(REAL_ROOT, *a)

RUN_DATE = os.environ.get("MAPZ_RUN_DATE", "2026-07-04")
TODAY = datetime.date.fromisoformat(RUN_DATE)

def load_topics():
    """Phase 0.5 산출물을 유일한 주제 소스로 로드. 하드코딩 폴백 없음."""
    path = rp("data", "topics", "topics_v1.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    ref = rp("data", "topics", "mvp_reference.json")
    if os.path.exists(ref):
        return json.load(open(ref, encoding="utf-8"))
    raise RuntimeError("Phase 0.5가 완료되지 않았고 MVP 참고셋도 없음 — 주제 사전 확정 불가")

def topics_dict():
    """{tid: {name, synonyms, emoji, ...}} 형태로 반환."""
    data = load_topics()
    if isinstance(data, dict) and "topics" in data:
        data = data["topics"]
    return {t["id"]: t for t in data}

def load_env():
    e = {}
    fp = rp("..", ".env")  # 상위 mapz/.env를 참조하되 값만 읽음(코드 import 아님). real/.env 우선.
    real_env = rp(".env")
    src = real_env if os.path.exists(real_env) else fp
    if os.path.exists(src):
        for line in open(src, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1); e[k.strip()] = v.strip()
    return e

def read_json(path, default=None):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default

def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def norm_name(s):
    s = unicodedata.normalize("NFKC", s or "").lower()
    return re.sub(r"[\s\(\)\[\]·,.\-_/]+", "", s)

def days_from_today(n):
    return (TODAY + datetime.timedelta(days=n)).isoformat()

KR_BBOX = {"lat_min": 33.0, "lat_max": 39.0, "lng_min": 124.0, "lng_max": 132.0}
def in_kr(lat, lng):
    try: lat, lng = float(lat), float(lng)
    except (TypeError, ValueError): return False
    b = KR_BBOX
    return b["lat_min"] <= lat <= b["lat_max"] and b["lng_min"] <= lng <= b["lng_max"]
