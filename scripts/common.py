"""MAPZ 공용 유틸: env 로딩, 경로, 주제 사전, 신선도 상수."""
import os, json, datetime, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def p(*a): return os.path.join(ROOT, *a)

# 실행일 (무인 파이프라인 기준일). 재현성을 위해 env 오버라이드 허용.
RUN_DATE = os.environ.get("MAPZ_RUN_DATE", "2026-07-04")
TODAY = datetime.date.fromisoformat(RUN_DATE)

# 5개 주제 + 동의어 관리 사전 (기획서 §4.4 / AUTOPILOT Phase2)
TOPICS = {
    "dino":   {"name": "공룡", "emoji": "🦕", "synonyms": ["공룡", "화석", "쥬라기", "고생물", "티라노", "암모나이트", "자연사", "지질"]},
    "space":  {"name": "우주", "emoji": "🚀", "synonyms": ["우주", "천문", "별", "행성", "은하", "로켓", "천체", "망원경", "달"]},
    "animal": {"name": "동물", "emoji": "🐾", "synonyms": ["동물", "생태", "곤충", "물고기", "새", "나비", "바다생물", "수족관", "생물"]},
    "robot":  {"name": "로봇", "emoji": "🤖", "synonyms": ["로봇", "코딩", "기계", "인공지능", "AI", "드론", "메카", "컴퓨터", "과학"]},
    "art":    {"name": "그림", "emoji": "🎨", "synonyms": ["그림", "미술", "만들기", "명화", "조각", "공예", "디자인", "전시", "화가"]},
}
TOPIC_IDS = list(TOPICS.keys())

def load_env():
    e = {}
    fp = p(".env")
    if os.path.exists(fp):
        for line in open(fp, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1); e[k.strip()] = v.strip()
    return e

def read_json(path, default=None):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return default

def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def norm_name(s):
    s = unicodedata.normalize("NFKC", s or "").lower()
    return re.sub(r"[\s\(\)\[\]·,.\-_/]+", "", s)

def days_from_today(n):
    return (TODAY + datetime.timedelta(days=n)).isoformat()

# 한국 bbox (검증용)
KR_BBOX = {"lat_min": 33.0, "lat_max": 39.0, "lng_min": 124.0, "lng_max": 132.0}

def in_kr(lat, lng):
    try:
        lat = float(lat); lng = float(lng)
    except (TypeError, ValueError):
        return False
    b = KR_BBOX
    return b["lat_min"] <= lat <= b["lat_max"] and b["lng_min"] <= lng <= b["lng_max"]

def topic_of_text(text):
    """텍스트에서 주제 태그 추론 (동의어 사전 매칭). 매칭 주제 id 리스트 반환."""
    text = text or ""
    hits = []
    for tid, t in TOPICS.items():
        if any(syn in text for syn in t["synonyms"]) or t["name"] in text:
            hits.append(tid)
    return hits
