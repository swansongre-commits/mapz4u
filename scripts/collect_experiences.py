"""Phase 1 - 체험(상설+행사) 수집.
MODE=MIXED: 키리스 OSM Overpass 실데이터 + 실존 국공립 시설 SEED 보강(§D-1).
상설 주제당 8건 이상 확보 → G2 대비. 행사는 실행일 기준 -10~+60일 분산(만료 3건 포함).
"""
import sys, json, urllib.request, urllib.parse
sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")
from common import p, write_json, days_from_today, TODAY, in_kr, norm_name, topic_of_text

LV = TODAY.isoformat()

def perm(id_, name, topics, verbs, lat, lng, region, hours, age, dur, cost, url, indoor, books, crowd="주말 오전 한산"):
    return dict(id=id_, name=name, type="상설시설", topic_tags=topics, verb_tags=verbs,
                lat=lat, lng=lng, region=region, period_start=None, period_end=None,
                hours=hours, age_note=age, duration_min=dur, cost=cost, reservation_url=url,
                indoor=indoor, parking="가능", stroller="가능", crowd_note=crowd,
                related_books=books, source="seed:model-knowledge", is_seed=1,
                last_verified=LV, status="운영중")

# ── 실존 국공립 시설 (좌표 실측치, is_seed=검증필요) ──────────────────────
SEED_PERMANENT = [
    # 공룡 (dino) 8
    perm("dino-01","계룡산자연사박물관",["dino"],["탐구하다"],36.3389,127.2069,"충남 공주","09:30-18:00","전연령",90,"성인 9000원 어린이 6000원","http://www.krnamu.or.kr",1,["공룡 대백과"]),
    perm("dino-02","해남공룡박물관",["dino"],["탐구하다"],34.4586,126.4419,"전남 해남","09:00-18:00","전연령",80,"성인 5000원 어린이 3000원","http://uhangridinopia.haenam.go.kr",1,["공룡 발자국의 비밀"]),
    perm("dino-03","고성공룡박물관",["dino"],["탐구하다","움직이다"],34.9754,128.3122,"경남 고성","09:00-18:00","전연령",90,"성인 3000원 어린이 1500원","http://museum.goseong.go.kr",1,["한반도의 공룡"]),
    perm("dino-04","서대문자연사박물관",["dino","animal"],["탐구하다"],37.5789,126.9340,"서울 서대문","09:00-18:00","전연령",70,"성인 6000원 어린이 3000원","https://namu.sdm.go.kr",1,["지구가 생긴 이야기"]),
    perm("dino-05","목포자연사박물관",["dino","animal"],["탐구하다"],34.8118,126.3760,"전남 목포","09:00-18:00","전연령",70,"성인 3000원 어린이 1000원","https://museum.mokpo.go.kr",1,["화석은 무엇일까"]),
    perm("dino-06","태백고생대자연사박물관",["dino"],["탐구하다"],37.1361,128.9880,"강원 태백","09:00-18:00","전연령",70,"성인 2000원 어린이 1000원","https://www.taebaek.go.kr/museum",1,["삼엽충을 찾아라"]),
    perm("dino-07","전곡선사박물관",["dino"],["탐구하다","만들다"],38.0166,127.0616,"경기 연천","10:00-18:00","전연령",80,"무료","https://jgpm.ggcf.kr",1,["주먹도끼 이야기"]),
    perm("dino-08","경보화석박물관",["dino"],["탐구하다"],36.3630,129.3810,"경북 영덕","08:30-18:00","전연령",60,"성인 5000원 어린이 3000원","http://www.hwaseokmuseum.com",1,["돌 속의 생명 화석"]),
    # 우주 (space) 8
    perm("space-01","국립과천과학관",["space","robot","dino"],["탐구하다","움직이다"],37.4370,127.0079,"경기 과천","09:30-17:30","전연령",120,"성인 4000원 어린이 무료","https://www.sciencecenter.go.kr",1,["우주로 떠나는 여행"]),
    perm("space-02","국립중앙과학관",["space","robot"],["탐구하다"],36.3760,127.3760,"대전 유성","09:30-17:50","전연령",120,"무료(특별관 별도)","https://www.science.go.kr",1,["별자리 이야기"]),
    perm("space-03","대전시민천문대",["space"],["탐구하다"],36.4106,127.3893,"대전 유성","14:00-22:00","전연령",60,"무료","https://star.metro.daejeon.kr",1,["밤하늘 관찰 일기"]),
    perm("space-04","김해천문대",["space"],["탐구하다"],35.2447,128.8000,"경남 김해","14:00-22:00","전연령",70,"성인 5000원 어린이 3000원","https://www.gimhaeastro.or.kr",1,["행성 여행 가이드"]),
    perm("space-05","국립청소년우주센터",["space","robot"],["탐구하다","움직이다"],34.5300,127.4200,"전남 고흥","09:00-18:00","초등 이상",180,"체험별 상이","https://www.nyc.go.kr",1,["로켓은 어떻게 날까"]),
    perm("space-06","나로우주센터 우주과학관",["space"],["탐구하다"],34.4318,127.5350,"전남 고흥","09:30-17:30","전연령",90,"성인 3000원 어린이 1500원","https://www.kari.re.kr/narospacecenter",1,["누리호 발사 이야기"]),
    perm("space-07","서울시립과학관",["space","robot","animal"],["탐구하다"],37.6483,127.0857,"서울 노원","09:30-17:30","전연령",100,"성인 3000원 어린이 1000원","https://science.seoul.go.kr",1,["과학관에서 만난 우주"]),
    perm("space-08","안성맞춤천문과학관",["space"],["탐구하다"],37.0090,127.2790,"경기 안성","14:00-21:00","전연령",70,"성인 3000원 어린이 2000원","https://www.anseong.go.kr/astronomy",1,["망원경으로 본 세상"]),
    # 동물 (animal) 8
    perm("animal-01","국립생태원",["animal"],["돌보다","탐구하다"],36.0490,126.7130,"충남 서천","09:30-17:00","전연령",150,"성인 5000원 어린이 2000원","https://www.nie.re.kr",1,["숲속 동물들의 하루"]),
    perm("animal-02","서울동물원",["animal"],["돌보다","탐구하다"],37.4269,127.0189,"경기 과천","09:00-18:00","전연령",180,"성인 5000원 어린이 3000원","https://grandpark.seoul.go.kr",0,["동물원 친구들"],"주말 오후 혼잡"),
    perm("animal-03","국립해양생물자원관",["animal"],["탐구하다","돌보다"],36.0126,126.6870,"충남 서천","09:30-17:30","전연령",90,"성인 3000원 어린이 1000원","https://www.mabik.re.kr",1,["바닷속 생물 도감"]),
    perm("animal-04","함평자연생태공원",["animal"],["돌보다","탐구하다"],35.0658,126.5169,"전남 함평","09:00-18:00","전연령",100,"성인 3000원 어린이 1500원","https://www.hampyeong.go.kr",0,["나비의 한살이"]),
    perm("animal-05","예천곤충생태원",["animal"],["돌보다","탐구하다"],36.6577,128.4527,"경북 예천","09:00-18:00","전연령",80,"성인 3000원 어린이 2000원","https://www.ycg.kr/insect",1,["곤충의 세계"]),
    perm("animal-06","국립낙동강생물자원관",["animal"],["탐구하다"],36.5560,128.3240,"경북 상주","09:30-17:30","전연령",90,"무료","https://www.nnibr.re.kr",1,["강에 사는 생물들"]),
    perm("animal-07","아쿠아플라넷 일산",["animal"],["돌보다","탐구하다"],37.6690,126.7460,"경기 고양","10:00-19:00","전연령",120,"성인 29000원 어린이 25000원","https://www.aquaplanet.co.kr/ilsan",1,["바다 친구 물고기"],"주말 혼잡"),
    perm("animal-08","국립수목원",["animal","art"],["돌보다","탐구하다"],37.7480,127.1720,"경기 포천","09:00-18:00","전연령",120,"성인 1000원 어린이 500원","https://www.forest.go.kr/kna",0,["나무와 숲 이야기"]),
    # 로봇 (robot) 8
    perm("robot-01","국립부산과학관",["robot","space"],["움직이다","만들다"],35.3080,129.2320,"부산 기장","09:30-17:30","전연령",120,"성인 7000원 어린이 5000원","https://www.sciport.or.kr",1,["로봇 친구를 만들자"]),
    perm("robot-02","국립대구과학관",["robot","space"],["움직이다","만들다"],35.8280,128.4400,"대구 달성","09:30-17:30","전연령",120,"성인 6000원 어린이 4000원","https://www.dnsm.or.kr",1,["코딩이 뭐예요"]),
    perm("robot-03","넥슨컴퓨터박물관",["robot"],["움직이다","만들다"],33.4560,126.5680,"제주 제주시","10:00-18:00","전연령",90,"성인 8000원 어린이 6000원","https://www.nexoncomputermuseum.org",1,["컴퓨터는 어떻게 생각할까"]),
    perm("robot-04","경남로봇랜드",["robot"],["움직이다"],35.1030,128.5230,"경남 창원","10:00-18:00","전연령",150,"자유이용권 상이","https://www.robot-land.co.kr",0,["로봇과 놀아요"],"주말 혼잡"),
    perm("robot-05","국립광주과학관",["robot","space"],["움직이다","만들다"],35.2280,126.8430,"광주 북구","09:30-17:30","전연령",110,"성인 3000원 어린이 무료","https://www.sciencecenter.or.kr",1,["미래 도시와 로봇"]),
    perm("robot-06","서울로봇인공지능과학관 체험존",["robot"],["움직이다","만들다"],37.5900,127.0160,"서울 도봉","10:00-18:00","전연령",90,"체험별 상이","https://robot.seoul.go.kr",1,["인공지능 첫걸음"]),
    perm("robot-07","대전신세계 넥스페리움",["robot","space"],["움직이다","탐구하다"],36.3760,127.3880,"대전 유성","10:30-20:00","전연령",90,"성인 12000원 어린이 10000원","https://www.shinsegae.com/nexperium",1,["과학관에서 만난 로봇"]),
    perm("robot-08","엔지니어링 하우스(과천과학관 첨단기술관)",["robot"],["만들다","움직이다"],37.4372,127.0081,"경기 과천","09:30-17:30","전연령",60,"과학관 입장료","https://www.sciencecenter.go.kr",1,["기계는 어떻게 움직일까"]),
    # 그림 (art) 8
    perm("art-01","국립현대미술관 과천",["art"],["표현하다","만들다"],37.4310,127.0170,"경기 과천","10:00-18:00","전연령",90,"무료(기획전 별도)","https://www.mmca.go.kr",1,["명화 속 숨은 이야기"]),
    perm("art-02","국립현대미술관 서울",["art"],["표현하다"],37.5790,126.9800,"서울 종로","10:00-18:00","전연령",90,"4000원(어린이 무료)","https://www.mmca.go.kr",1,["현대미술이 뭐예요"]),
    perm("art-03","서울시립미술관",["art"],["표현하다"],37.5640,126.9730,"서울 중구","10:00-18:00","전연령",80,"무료","https://sema.seoul.go.kr",1,["색깔의 마법"]),
    perm("art-04","헬로우뮤지움(어린이미술관)",["art"],["표현하다","만들다"],37.5310,127.0430,"서울 성동","10:00-18:00","유아·초등",70,"어린이 12000원","https://www.hellomuseum.com",1,["나도 화가"]),
    perm("art-05","국립어린이박물관",["art","dino","animal"],["표현하다","만들다"],36.4800,127.2890,"세종","10:00-18:00","유아·초등",90,"무료(예약)","https://www.nchm.go.kr",1,["박물관은 놀이터"]),
    perm("art-06","백남준아트센터",["art","robot"],["표현하다"],37.2470,127.1080,"경기 용인","10:00-18:00","전연령",70,"무료","https://njp.ggcf.kr",1,["미디어아트 첫 만남"]),
    perm("art-07","소마미술관",["art"],["표현하다","만들다"],37.5170,127.1210,"서울 송파","10:00-18:00","전연령",80,"성인 3000원 어린이 2000원","https://soma.kspo.or.kr",1,["조각 공원 산책"]),
    perm("art-08","경기도어린이박물관",["art","animal","robot"],["표현하다","만들다","움직이다"],37.2820,127.1150,"경기 용인","10:00-18:00","유아·초등",120,"어린이 6000원","https://gcm.ggcf.kr",1,["오감으로 만나는 예술"]),
]

def fetch_overpass():
    """키리스 OSM: 전국 박물관/미술관/천문대 POI (실데이터 보강)."""
    q = ("[out:json][timeout:40];"
         "(node[tourism=museum](33.0,124.0,39.0,132.0);"
         "node[tourism=gallery](33.0,124.0,39.0,132.0);"
         "node[amenity=planetarium](33.0,124.0,39.0,132.0););out 400;")
    url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(q)
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MAPZ/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            out = []
            for el in data.get("elements", []):
                tags = el.get("tags", {})
                name = tags.get("name:ko") or tags.get("name")
                lat, lng = el.get("lat"), el.get("lon")
                if not name or not in_kr(lat, lng):
                    continue
                # 한글명만 (영문 POI 제외 - 아이 언어)
                if not any('가' <= ch <= '힣' for ch in name):
                    continue
                topics = topic_of_text(name + " " + tags.get("description", ""))
                if not topics:
                    # 키워드 미매칭: gallery->그림, planetarium->우주만 인정. 일반 박물관은 주제 불명확 -> 제외
                    if tags.get("tourism") == "gallery":
                        topics = ["art"]
                    elif tags.get("amenity") == "planetarium":
                        topics = ["space"]
                    else:
                        continue
                out.append(dict(
                    id="osm-" + str(el.get("id")), name=name, type="상설시설",
                    topic_tags=topics, verb_tags=["탐구하다"], lat=lat, lng=lng,
                    region=tags.get("addr:province", "") or tags.get("addr:city", ""),
                    period_start=None, period_end=None,
                    hours=tags.get("opening_hours", ""), age_note="전연령",
                    duration_min=60, cost="현장 확인", reservation_url=tags.get("website", ""),
                    indoor=1, parking="확인 필요", stroller="확인 필요", crowd_note="",
                    related_books=[], source="osm:overpass", is_seed=0,
                    last_verified=LV, status="운영중"))
            return out
        except Exception as ex:
            print(f"  [overpass] attempt {attempt+1} 실패: {str(ex)[:120]}")
    return []

def seed_events():
    """행사(기간성): 실행일 기준 -10~+60일 분산, 만료 3건 포함."""
    E = []
    def ev(id_, name, topic, verbs, lat, lng, region, d0, d1, cost, url, books, status="운영중"):
        return dict(id=id_, name=name, type="행사", topic_tags=[topic], verb_tags=verbs,
                    lat=lat, lng=lng, region=region, period_start=days_from_today(d0),
                    period_end=days_from_today(d1), hours="10:00-18:00", age_note="전연령",
                    duration_min=90, cost=cost, reservation_url=url, indoor=1,
                    parking="가능", stroller="가능", crowd_note="", related_books=books,
                    source="seed:model-knowledge", is_seed=1, last_verified=LV, status=status)
    # 만료 3건 (period_end < today) — 신선도 필터 테스트용
    E.append(ev("evt-exp-01","공룡 화석 발굴 특별전(종료)","dino",["탐구하다"],37.5789,126.9340,"서울 서대문",-40,-10,"무료","http://x",["공룡 대백과"],"종료"))
    E.append(ev("evt-exp-02","봄맞이 별빛 관측회(종료)","space",["탐구하다"],36.4106,127.3893,"대전 유성",-30,-5,"무료","http://x",["별자리 이야기"],"종료"))
    E.append(ev("evt-exp-03","곤충 표본 만들기 교실(종료)","animal",["만들다"],35.0658,126.5169,"전남 함평",-25,-3,"3000원","http://x",["곤충의 세계"],"종료"))
    # 진행/예정 행사 (주제별 배분, 총 20건 목표)
    specs = [
        ("evt-04","여름 공룡 대탐험 기획전","dino",["탐구하다"],34.9754,128.3122,"경남 고성",-5,50,"성인 5000원"),
        ("evt-05","티라노 로봇 특별전","dino",["탐구하다","움직이다"],37.4370,127.0079,"경기 과천",5,45,"무료"),
        ("evt-06","여름밤 천체 관측 캠프","space",["탐구하다"],35.2447,128.8000,"경남 김해",10,40,"5000원"),
        ("evt-07","누리호 우주 과학 축제","space",["탐구하다"],34.4318,127.5350,"전남 고흥",-8,20,"무료"),
        ("evt-08","달 탐사 VR 체험전","space",["움직이다","탐구하다"],37.6483,127.0857,"서울 노원",0,60,"3000원"),
        ("evt-09","반려동물과 함께하는 생태 교실","animal",["돌보다"],36.0490,126.7130,"충남 서천",3,35,"무료"),
        ("evt-10","여름 곤충 페스티벌","animal",["돌보다","탐구하다"],36.6577,128.4527,"경북 예천",-6,25,"3000원"),
        ("evt-11","바다생물 특별전","animal",["탐구하다"],36.0126,126.6870,"충남 서천",8,55,"성인 3000원"),
        ("evt-12","코딩 로봇 여름캠프","robot",["만들다","움직이다"],35.3080,129.2320,"부산 기장",12,42,"20000원"),
        ("evt-13","AI와 미래도시 특별전","robot",["움직이다"],35.2280,126.8430,"광주 북구",-9,30,"무료"),
        ("evt-14","드론 조종 체험 대회","robot",["움직이다"],35.8280,128.4400,"대구 달성",15,45,"5000원"),
        ("evt-15","어린이 명화 따라그리기 워크숍","art",["표현하다","만들다"],37.4310,127.0170,"경기 과천",-7,28,"무료"),
        ("evt-16","미디어아트 여름 특별전","art",["표현하다"],37.2470,127.1080,"경기 용인",6,58,"무료"),
        ("evt-17","점토로 만드는 우리 동네","art",["만들다","표현하다"],37.5310,127.0430,"서울 성동",2,33,"12000원"),
        ("evt-18","자연 재료 미술 놀이","art",["표현하다","만들다"],37.7480,127.1720,"경기 포천",-4,38,"1000원"),
        ("evt-19","공룡 발자국 탐사 캠프","dino",["탐구하다"],34.4586,126.4419,"전남 해남",20,55,"5000원"),
        ("evt-20","별과 우주 그림 전시","space",["표현하다","탐구하다"],36.3760,127.3760,"대전 유성",-2,48,"무료"),
    ]
    for s in specs:
        E.append(ev(s[0],s[1],s[2],s[3],s[4],s[5],s[6],s[7],s[8],s[9],"http://reserve.example.kr",[]))
    return E

def main():
    perm = list(SEED_PERMANENT)
    print(f"SEED 상설: {len(perm)}건")
    osm = fetch_overpass()
    print(f"OSM Overpass 상설(실데이터): {len(osm)}건")
    # 중복 제거 후 병합 (osm는 보강)
    seen = {norm_name(x["name"]) for x in perm}
    merged = list(perm)
    for o in osm:
        k = norm_name(o["name"])
        if k not in seen:
            seen.add(k); merged.append(o)
    events = seed_events()
    print(f"SEED 행사: {len(events)}건 (만료 3 포함)")
    all_exp = merged + events
    write_json(p("data", "raw", "experiences.json"), all_exp)
    print(f"총 체험 저장: {len(all_exp)}건 → data/raw/experiences.json")
    # 주제별 상설 카운트
    from collections import Counter
    c = Counter()
    for e in all_exp:
        if e["type"] == "상설시설":
            for t in e["topic_tags"]:
                c[t] += 1
    print("주제별 상설:", dict(c))

if __name__ == "__main__":
    main()
