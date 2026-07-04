"""Phase 0.5 - 관심사 추출 (실데이터판). 기획서 §7 / PRODUCTION §2.
수요 = 정보나루 인기대출 실데이터(연령대별 대출건수). 연결 = TourAPI 문화시설 2,680건 실데이터.
관리형 후보 사전(스프롤 방지, 기획서 §6)에 실데이터를 붙여 2x2 -> 상위 N(>=12) 자동 채택.
산출: topics_v1.json, mvp_reference.json, topic_extraction_report.md
"""
import sys, re
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, write_json, read_json, TODAY
from lib_corpus import load_all

# 관리형 관심사 후보 사전: (name, synonyms(제목매칭), emoji, kdc_prefixes)
CANDIDATES = [
    ("공룡",    ["공룡","화석","쥬라기","티라노","공룡뼈"], "🦕", ["456","457","45"]),
    ("우주",    ["우주","천문","행성","로켓","은하","블랙홀","태양계"], "🚀", ["440","44"]),
    ("동물",    ["동물","포유류","야생동물","반려동물","강아지","고양이","사파리"], "🐾", ["490","49"]),
    ("곤충",    ["곤충","벌레","나비","개미","딱정벌레","사슴벌레"], "🐛", ["496"]),
    ("바다생물",["바다","물고기","해양","상어","고래","펭귄","수족관"], "🐠", ["491","49"]),
    ("로봇",    ["로봇","코딩","인공지능","AI","드론","프로그래밍","기계"], "🤖", ["550","004","005","55"]),
    ("자동차",  ["자동차","자동차","기차","비행기","포크레인","중장비","탈것"], "🚗", ["556","557"]),
    ("공룡시대의땅",["지구","화산","지진","암석","광물","동굴"], "🌋", ["450","45"]),
    ("그림",    ["그림","미술","명화","화가","색칠","드로잉","만화"], "🎨", ["650","653","65"]),
    ("만들기",  ["만들기","공예","점토","종이접기","블록","레고","슬라임"], "🧩", ["630","63"]),
    ("과학실험",["과학","실험","발명","원리","호기심"], "🔬", ["400","404","42","43"]),
    ("몸과건강",["몸","인체","건강","뼈","이빨","감염","바이러스"], "🫀", ["510","51"]),
    ("역사와위인",["역사","위인","한국사","세계사","이순신","세종","위인전"], "🏯", ["900","990","910","99","91"]),
    ("식물",    ["식물","꽃","나무","숲","씨앗","텃밭"], "🌱", ["480","48"]),
    ("날씨와환경",["날씨","기후","환경","계절","오염","에너지"], "🌍", ["451","539"]),
    ("음악",    ["음악","악기","피아노","노래","오케스트라"], "🎵", ["670","67"]),
    ("운동",    ["운동","축구","야구","태권도","수영","스포츠"], "⚽", ["690","692","69"]),
    ("요리",    ["요리","음식","베이킹","쿠킹","레시피","빵"], "🍳", ["594","59"]),
]

BANDS = ["pre", "low", "mid1", "mid2"]

def kdc_match(kdc, prefixes):
    return any(kdc.startswith(p) for p in prefixes) if kdc else False

def title_match(title, syns):
    return any(s in title for s in syns)

def main():
    corpus = load_all(rp("data", "raw", "data4library"))
    total_rows = sum(len(v) for v in corpus.values())
    print(f"수요 코퍼스(실대출): {total_rows}행 ({ {b:len(corpus[b]) for b in BANDS} })")

    facilities = read_json(rp("data", "raw", "tourapi_facilities.json"), [])
    print(f"연결 코퍼스(TourAPI 실시설): {len(facilities)}건")

    cands = []
    for name, syns, emoji, kdcs in CANDIDATES:
        # 수요: 매칭 도서 대출건수 합 + 연령밴드 프로파일
        band_loans = {b: 0 for b in BANDS}
        matched_books = 0
        for b in BANDS:
            for r in corpus[b]:
                if title_match(r["title"], syns) or kdc_match(r["kdc"], kdcs):
                    band_loans[b] += r["loan"]; matched_books += 1
        demand_raw = sum(band_loans.values())
        # 연결: TourAPI 시설명 매칭 수
        fac = sum(1 for f in facilities if any(s in f["name"] for s in syns))
        cands.append({"name": name, "synonyms": syns, "emoji": emoji, "kdc": kdcs,
                      "demand_raw": demand_raw, "matched_books": matched_books,
                      "band_loans": band_loans, "osm_facility_matches": fac})

    # 정규화 (0~10)
    dmax = max((c["demand_raw"] for c in cands), default=1) or 1
    cmax = max((c["osm_facility_matches"] for c in cands), default=1) or 1
    for c in cands:
        c["demand_score"] = round(10.0 * c["demand_raw"] / dmax, 2)
        c["connection_score"] = round(10.0 * c["osm_facility_matches"] / cmax, 2)
        # 연령 프로파일(밴드별 상대 비중)
        tot = sum(c["band_loans"].values()) or 1
        c["age_profile"] = {b: round(c["band_loans"][b] / tot, 3) for b in BANDS}
        c["total"] = round(c["demand_score"] + c["connection_score"], 2)

    dmed = sorted(c["demand_score"] for c in cands)[len(cands)//2]
    cmed = sorted(c["connection_score"] for c in cands)[len(cands)//2]
    for c in cands:
        c["quadrant"] = ("수요高" if c["demand_score"] >= dmed else "수요低") + "·" + \
                        ("연결高" if c["connection_score"] >= cmed else "연결低")

    ranked = sorted(cands, key=lambda c: -c["total"])
    N = 12
    chosen = ranked[:N]
    slug = {"공룡":"dino","우주":"space","동물":"animal","곤충":"insect","바다생물":"sealife",
            "로봇":"robot","자동차":"vehicle","공룡시대의땅":"earth_geo","그림":"art","만들기":"making",
            "과학실험":"science","몸과건강":"body","역사와위인":"history","식물":"plant",
            "날씨와환경":"weather","음악":"music","운동":"sports","요리":"cooking"}
    topics = []
    for c in chosen:
        topics.append({"id": slug.get(c["name"], re.sub(r"\W","",c["name"])[:8]),
                       "name": c["name"], "synonyms": c["synonyms"], "emoji": c["emoji"],
                       "kdc": c["kdc"], "demand_score": c["demand_score"],
                       "connection_score": c["connection_score"],
                       "osm_facility_matches": c["osm_facility_matches"],
                       "matched_books": c["matched_books"],
                       "age_profile": c["age_profile"], "quadrant": c["quadrant"]})
    write_json(rp("data","topics","topics_v1.json"),
               {"generated": TODAY.isoformat(), "demand_source": "data4library:file(연령대별 인기대출 실데이터)",
                "connection_source": "tourapi:문화시설 실데이터", "count": len(topics), "topics": topics})
    write_json(rp("data","topics","mvp_reference.json"), {"topics": [
        {"id":"dino","name":"공룡"},{"id":"space","name":"우주"},{"id":"animal","name":"동물"},
        {"id":"robot","name":"로봇"},{"id":"art","name":"그림"}]})

    weak = [t["id"] for t in topics if t["osm_facility_matches"] < 3]
    g05 = len(topics) >= 8

    md = ["# Phase 0.5 — 관심사 추출 리포트 (실데이터)\n",
          f"- 실행일: {TODAY.isoformat()}",
          f"- 수요 소스: **정보나루 인기대출 실데이터** (연령대별 4파일, 총 {total_rows}행)",
          f"- 연결 소스: **TourAPI 문화시설 실데이터** ({len(facilities)}건)",
          f"- 관리형 후보 {len(cands)}개 → 채택 {len(topics)}개 (2×2 상위 N={N})\n",
          "## 채택 주제\n",
          "| 순위 | 주제 | id | 수요(정규화) | 대출매칭도서 | 연결(시설수) | 사분면 | 연령피크 |",
          "|---|---|---|---|---|---|---|---|"]
    for i, t in enumerate(topics, 1):
        peak = max(t["age_profile"], key=t["age_profile"].get)
        bandname = {"pre":"유아","low":"초저","mid1":"초중","mid2":"초고"}[peak]
        md.append(f"| {i} | {t['emoji']}{t['name']} | {t['id']} | {t['demand_score']} | "
                  f"{t['matched_books']} | {t['connection_score']}({t['osm_facility_matches']}) | {t['quadrant']} | {bandname} |")
    md.append("\n## 탈락 후보\n")
    for c in ranked[N:]:
        md.append(f"- {c['emoji']}{c['name']}: 수요{c['demand_score']}/연결{c['connection_score']}({c['osm_facility_matches']}시설) {c['quadrant']}")
    md.append("\n## MVP 5개(하드코딩)와의 비교 — 실수요가 무엇을 바꿨나\n")
    mvp5 = {"공룡","우주","동물","로봇","그림"}
    names = [t["name"] for t in topics]
    md.append(f"- MVP 5개 중 운영 채택 유지: {[n for n in names if n in mvp5]}")
    dropped = [n for n in mvp5 if n not in names]
    md.append(f"- MVP였지만 실데이터 순위 밖으로 밀린 주제: {dropped or '없음'}")
    md.append(f"- 실수요로 새로 편입: {[n for n in names if n not in mvp5]}")
    md.append(f"\n## 게이트\n- 주제 수 {len(topics)} (>=8: {len(topics)>=8})")
    md.append(f"- 연결 약체(시설<3): {weak or '없음'}")
    md.append(f"- **G0.5: {'PASS' if g05 else 'FAIL'}**")
    open(rp("reports","topic_extraction_report.md"),"w",encoding="utf-8").write("\n".join(md))
    open(rp("state","g05_result.txt"),"w",encoding="utf-8").write(
        f"G0.5 {'PASS' if g05 else 'FAIL'} topics={len(topics)} weak={weak}\n채택:{names}")
    print(f"채택 {len(topics)}개:", names)
    print("MVP5 중 탈락:", dropped or "없음")
    print("G0.5", "PASS" if g05 else "FAIL")

if __name__ == "__main__":
    main()
