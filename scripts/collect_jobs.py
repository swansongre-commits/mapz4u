"""Phase 1 - 직업 수집. MAPS_ASSETS=TRUE -> junior_jobs.json에서 로드(§4.3 Layer B).
Layer B 변환 규칙: 유지(하는 일=blurb) / 제거(연봉·전망·요구학력·학과명) / 변환(직업명->동사 서술).
주제당 5건=25건, 주제당 Layer B 카드 1건 지정. source_asset로 반입/생성 추적.
"""
import sys
sys.path.insert(0, ".")
from common import p, write_json, read_json, TOPICS, TOPIC_IDS

jj = read_json(p("data", "maps_assets", "kid_lexicon", "junior_jobs.json"), {})

def match_topics(name, blurb):
    text = name + " " + blurb
    hits = []
    for tid, t in TOPICS.items():
        if any(syn in text for syn in t["synonyms"]) or t["name"] in text:
            hits.append(tid)
    return hits

# 자산에서 주제별 후보 수집
buckets = {tid: [] for tid in TOPIC_IDS}
for name, info in jj.items():
    blurb = info.get("blurb", "")
    for tid in match_topics(name, blurb):
        buckets[tid].append((name, blurb, info.get("emoji", "")))

# 자산 부족분 보강용 생성(동사 서술) — 헌장: 명사보다 동사 강조
GEN = {
    "dino": [("화석을 연구하는 사람","땅속에 묻힌 옛 생물의 흔적을 찾아 무슨 동물이었는지 밝혀내요","🦴"),
             ("자연사박물관에서 일하는 사람","오래된 뼈와 화석을 잘 보관하고 사람들에게 이야기로 풀어줘요","🏛️")],
    "space": [("별을 관측하는 사람","밤하늘의 별과 행성을 망원경으로 지켜보며 기록해요","🔭"),
              ("로켓을 만드는 사람","우주로 날아가는 로켓을 설계하고 시험해요","🚀")],
    "animal": [("동물을 돌보는 사람","아프거나 힘든 동물을 살펴보고 건강하게 돌봐줘요","🐾"),
               ("바다생물을 연구하는 사람","바닷속 생물이 어떻게 사는지 잠수해서 관찰해요","🐠")],
    "robot": [("로봇을 만드는 사람","스스로 움직이는 기계를 조립하고 움직이게 프로그래밍해요","🤖"),
              ("코딩하는 사람","컴퓨터에게 할 일을 차근차근 글로 알려줘요","💻")],
    "art": [("그림 그리는 사람","머릿속 상상을 색과 선으로 종이에 표현해요","🎨"),
            ("만드는 것을 디자인하는 사람","우리가 쓰는 물건을 예쁘고 편하게 모양을 만들어요","✏️")],
}

VERB_HINT = {"dino":["탐구하다"],"space":["탐구하다"],"animal":["돌보다","탐구하다"],
             "robot":["만들다","움직이다"],"art":["표현하다","만들다"]}

def clean_verb(blurb, name):
    # Layer B 변환: 직업명 명사를 뒤로 빼고 동사 서술 유지. blurb가 이미 '~해요' 체면 그대로.
    b = blurb.strip()
    if not b.endswith(("요.", "요", "다.", ".")):
        b += "해요"
    return b

def main():
    jobs = []
    for tid in TOPIC_IDS:
        cand = buckets[tid][:]
        # Layer B 노출 카드(index0)는 명확히 주제-정합한 생성 직업으로 고정(어린이 대면 품질)
        g0 = GEN[tid][0]
        picked = [(g0[0], g0[1], g0[2], "generated")]
        used_names = {g0[0]}
        # 나머지 4건(hidden 엣지용)은 MAPS 자산 우선, 부족 시 생성 보강
        for name, blurb, emoji in cand:
            if name in used_names:
                continue
            used_names.add(name)
            picked.append((name, blurb, emoji, "maps_assets"))
            if len(picked) >= 5:
                break
        # GEN 나머지로 보강
        for g in GEN[tid][1:]:
            if len(picked) >= 5:
                break
            if g[0] not in used_names:
                picked.append((g[0], g[1], g[2], "generated")); used_names.add(g[0])
        # 그래도 부족하면 주제 이름 기반 일반 직업으로 패딩(무한루프 방지)
        pad = 1
        while len(picked) < 5:
            nm = f"{TOPICS[tid]['name']} 분야에서 일하는 사람 {pad}"
            picked.append((nm, f"{TOPICS[tid]['name']}을(를) 좋아하는 마음으로 여러 가지 일을 해요",
                           TOPICS[tid]['emoji'], "generated")); pad += 1
        for i, (name, blurb, emoji, src) in enumerate(picked):
            jobs.append(dict(
                id=f"job-{tid}-{i+1:02d}", name=name,
                verb_desc=clean_verb(blurb, name),
                layer="B" if i == 0 else "hidden",   # 주제당 첫 건을 Layer B 노출 카드로 지정
                topic_tags=[tid], verb_tags=VERB_HINT[tid], emoji=emoji,
                source_asset=src))
    write_json(p("data", "raw", "jobs.json"), jobs)
    from collections import Counter
    c = Counter(t for j in jobs for t in j["topic_tags"])
    srcc = Counter(j["source_asset"] for j in jobs)
    print(f"직업 저장: {len(jobs)}건 → data/raw/jobs.json")
    print("주제별:", dict(c), "| 출처:", dict(srcc))
    print("Layer B 카드:", [j["name"] for j in jobs if j["layer"] == "B"])

if __name__ == "__main__":
    main()
