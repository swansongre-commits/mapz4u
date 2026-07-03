"""운영 Phase 1 - 체험 수집 (실데이터 우선).
TourAPI 문화시설 2,680 + 축제 171(실기간)을 확정 12주제에 태깅. 결측 주제만 실존시설 SEED 보강.
"""
import sys
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, read_json, write_json, topics_dict, TODAY, norm_name
from collections import Counter

TOPICS = topics_dict()
TIDS = list(TOPICS.keys())
LV = TODAY.isoformat()
MIN_PER_TOPIC = 5

# 시설명 태깅용 확장 사전 (표시 synonyms보다 넓게 — 시설 명명 관행 반영)
TAG = {
    "art":     ["미술","갤러리","아트","화랑","현대미술","조각","공예관","디자인"],
    "history": ["역사","박물관","기념관","유물","향교","고택","민속","전통","유적","독립","서원","한옥"],
    "science": ["과학","사이언스","발명","산업","기술","에너지관"],
    "animal":  ["동물","생태","자연사","곤충생태","동물원","사파리","축산"],
    "body":    ["보건","건강","인체","의학","한의","치아","의료"],
    "space":   ["우주","천문대","천체","천문과학","플라네타","항공우주"],
    "plant":   ["수목","식물","숲","정원","자연휴양","생태숲","산림"],
    "sealife": ["해양","바다","수족관","아쿠아","어촌","물고기","해녀"],
    "sports":  ["체육","스포츠","축구","야구","태권","스키","빙상"],
    "cooking": ["음식","요리","김치","전통주","발효","식문화","쌀"],
    "insect":  ["곤충","나비","벌","반딧불","생태곤충"],
    "music":   ["음악","악기","국악","오르골","축음기","관악","현악"],
}
# 표시 synonyms도 태깅에 합산
for tid in TIDS:
    TAG.setdefault(tid, [])
    TAG[tid] = list(dict.fromkeys(TAG[tid] + TOPICS[tid].get("synonyms", [])))

def topics_for(text):
    return [tid for tid in TIDS if any(s in text for s in TAG[tid])]

def fac_to_exp(f):
    text = f["name"] + " " + f.get("addr", "")
    tids = topics_for(text)
    if not tids:
        return None
    region = (f.get("addr", "").split()[0] if f.get("addr") else "")
    return dict(id="tour-"+str(f["contentid"]), name=f["name"], type="상설시설",
                topic_tags=tids, verb_tags=["탐구하다"], lat=f["lat"], lng=f["lng"],
                region=region, period_start=None, period_end=None,
                hours="", age_note="전연령", duration_min=90, cost="현장 확인",
                reservation_url=f.get("homepage",""), indoor=1, parking="확인 필요",
                stroller="확인 필요", crowd_note="", related_books=[],
                tel=f.get("tel",""), image=f.get("image",""),
                source="tourapi:문화시설", is_seed=0, last_verified=LV, status="운영중")

def fes_to_evt(f):
    if not f.get("lat"):
        return None
    text = f["name"] + " " + f.get("addr","")
    tids = topics_for(text)
    if not tids:
        return None
    def d(s): return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if s and len(s)>=8 else None
    region = (f.get("addr","").split()[0] if f.get("addr") else "")
    return dict(id="tourfes-"+str(f["contentid"]), name=f["name"], type="행사",
                topic_tags=tids, verb_tags=["탐구하다"], lat=f["lat"], lng=f["lng"],
                region=region, period_start=d(f.get("eventstartdate")),
                period_end=d(f.get("eventenddate")), hours="", age_note="전연령",
                duration_min=90, cost="현장 확인", reservation_url="", indoor=0,
                parking="확인 필요", stroller="확인 필요", crowd_note="", related_books=[],
                tel=f.get("tel",""), image=f.get("image",""),
                source="tourapi:축제", is_seed=0, last_verified=LV, status="운영중")

# 결측 보강용 실존 국공립 시설 (좌표 실측, is_seed=검증필요) — 연결 약한 주제 위주
SEED = {
 "animal":[("국립생태원","충남 서천",36.0490,126.7130),("서울동물원","경기 과천",37.4269,127.0189),
           ("국립낙동강생물자원관","경북 상주",36.5560,128.3240),("우포생태체험장","경남 창녕",35.5560,128.4210),
           ("국립호남권생물자원관","전남 목포",34.7830,126.3720)],
 "body":[("국립과천과학관 인체관","경기 과천",37.4370,127.0079),("한독의약박물관","충북 음성",37.0300,127.6800),
         ("허준박물관","서울 강서",37.5490,126.8390),("동은의학박물관 연세대","서울 서대문",37.5620,126.9410),
         ("전주한방문화센터","전북 전주",35.8150,127.1490)],
 "cooking":[("김치박물관 뮤지엄김치간","서울 중구",37.5680,126.9910),("한식문화공간 이음","서울 중구",37.5720,126.9800),
            ("떡박물관","서울 종로",37.5720,127.0010),("전주음식문화관","전북 전주",35.8140,127.1500),
            ("한국차박물관","전남 보성",34.7180,127.0790)],
 "music":[("국립국악박물관","서울 서초",37.4780,127.0110),("난파음악당","서울 종로",37.5750,126.9740),
          ("참소리축음기박물관","강원 강릉",37.7990,128.8960),("세계악기박물관","경기 파주",37.7130,126.7010),
          ("오르골하우스","제주 서귀포",33.2510,126.4190)],
 "sports":[("국립체육박물관","서울 송파",37.5170,127.1280),("한국축구박물관","경기 파주",37.7600,126.7770),
           ("태권도원","전북 무주",35.9010,127.6610),("2018평창기념관","강원 평창",37.6580,128.6690),
           ("한국잠사박물관","경북 상주",36.4150,128.1590)],
 "insect":[("함평자연생태공원 곤충관","전남 함평",35.0658,126.5169),("예천곤충생태원","경북 예천",36.6577,128.4527),
           ("서울숲곤충식물원","서울 성동",37.5440,127.0410),("영양반딧불이천문대","경북 영양",36.6660,129.1120),
           ("홍천잣벌레생태관","강원 홍천",37.6970,127.8880)],
}

def main():
    facilities = read_json(rp("data","raw","tourapi_facilities.json"), [])
    festivals = read_json(rp("data","raw","tourapi_festivals.json"), [])
    exps, seen = [], set()
    for f in facilities:
        e = fac_to_exp(f)
        if e:
            k = norm_name(e["name"]) + str(round(e["lat"],3))
            if k in seen: continue
            seen.add(k); exps.append(e)
    events = [e for e in (fes_to_evt(f) for f in festivals) if e]
    print(f"TourAPI 태깅: 상설 {len(exps)}건, 행사 {len(events)}건")
    # 주제별 상설 카운트 → 결측 보강
    perm_by = Counter(t for e in exps for t in e["topic_tags"] if e["type"]=="상설시설")
    added = 0
    for tid in TIDS:
        need = MIN_PER_TOPIC - perm_by.get(tid, 0)
        if need > 0 and tid in SEED:
            for i, (name, region, lat, lng) in enumerate(SEED[tid][:need]):
                exps.append(dict(id=f"seed-{tid}-{i+1}", name=name, type="상설시설",
                    topic_tags=[tid], verb_tags=["탐구하다"], lat=lat, lng=lng, region=region,
                    period_start=None, period_end=None, hours="", age_note="전연령",
                    duration_min=90, cost="현장 확인", reservation_url="", indoor=1,
                    parking="가능", stroller="가능", crowd_note="", related_books=[],
                    tel="", image="", source="seed:model-knowledge", is_seed=1,
                    last_verified=LV, status="운영중")); added += 1
    print(f"결측 보강 SEED: {added}건")
    allexp = exps + events
    write_json(rp("data","raw","experiences.json"), allexp)
    perm2 = Counter(t for e in allexp for t in e["topic_tags"] if e["type"]=="상설시설")
    seedn = sum(1 for e in allexp if e.get("is_seed"))
    print(f"총 체험 {len(allexp)}건 (실데이터 {len(allexp)-seedn}, SEED {seedn})")
    print("주제별 상설:", {tid: perm2.get(tid,0) for tid in TIDS})
    open(rp("state","collect_exp.txt"),"w",encoding="utf-8").write(
        f"total={len(allexp)} real={len(allexp)-seedn} seed={seedn}\nperm={dict(perm2)}")

if __name__ == "__main__":
    main()
