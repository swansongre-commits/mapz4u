"""운영 Phase 1 - 직업 (MAPS junior_jobs 자산 태깅, 12주제). Layer B 변환: 동사서술·연봉전망 제거."""
import sys
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, read_json, write_json, topics_dict

TOPICS = topics_dict(); TIDS = list(TOPICS.keys())
jj = read_json(rp("data","maps_assets","junior_jobs.json"), {})

# 주제별 Layer B 대면 카드 (생성, 동사서술)
LAYERB = {
 "art":("그림 그리는 사람","머릿속 상상을 색과 선으로 표현해요","🎨"),
 "history":("옛이야기를 밝히는 사람","오래된 기록과 유물을 살펴 지난 일을 알아내요","🏯"),
 "science":("실험하는 사람","궁금한 것을 이리저리 시험해 원리를 알아내요","🔬"),
 "animal":("동물을 돌보는 사람","아프거나 힘든 동물을 살펴보고 돌봐요","🐾"),
 "body":("몸을 살피는 사람","우리 몸이 어떻게 움직이는지 살피고 건강을 도와요","🫀"),
 "space":("별을 관측하는 사람","밤하늘의 별과 행성을 지켜보며 기록해요","🔭"),
 "plant":("식물을 기르는 사람","씨앗을 심고 돌봐 잘 자라게 해요","🌱"),
 "sealife":("바다생물을 연구하는 사람","바닷속 생물이 어떻게 사는지 관찰해요","🐠"),
 "sports":("몸을 움직이는 사람","여러 방법으로 몸을 단련하고 함께 뛰어요","⚽"),
 "cooking":("음식을 만드는 사람","재료를 다듬어 맛있고 건강한 음식을 만들어요","🍳"),
 "insect":("곤충을 살피는 사람","작은 벌레들이 어떻게 사는지 자세히 들여다봐요","🐛"),
 "music":("소리를 만드는 사람","악기와 목소리로 마음을 담은 소리를 만들어요","🎵"),
}

def clean_verb(b):
    b = b.strip()
    return b if b.endswith(("요",".","다")) else b + "해요"

def main():
    # 자산 주제 태깅
    buckets = {tid: [] for tid in TIDS}
    for name, info in jj.items():
        blurb = info.get("blurb",""); text = name + " " + blurb
        for tid in TIDS:
            if any(s in text for s in TOPICS[tid]["synonyms"]):
                buckets[tid].append((name, blurb, info.get("emoji","")))
    jobs = []
    for tid in TIDS:
        lb = LAYERB.get(tid, (f"{TOPICS[tid]['name']} 분야에서 일하는 사람",
                              f"{TOPICS[tid]['name']}을(를) 좋아하는 마음으로 여러 일을 해요", TOPICS[tid]["emoji"]))
        picked = [(lb[0], lb[1], lb[2], "generated")]
        used = {lb[0]}
        for name, blurb, emoji in buckets[tid]:
            if name in used: continue
            used.add(name); picked.append((name, blurb, emoji, "maps_assets"))
            if len(picked) >= 5: break
        # 부족분 generated 패딩
        pad = 1
        while len(picked) < 4:
            nm = f"{TOPICS[tid]['name']}을(를) 살리는 일 {pad}"
            picked.append((nm, f"{TOPICS[tid]['name']}과(와) 관련된 여러 가지 일을 해요", lb[2], "generated"))
            used.add(nm); pad += 1
        for i,(name,blurb,emoji,src) in enumerate(picked):
            jobs.append(dict(id=f"job-{tid}-{i+1:02d}", name=name, verb_desc=clean_verb(blurb),
                layer="B" if i==0 else "hidden", topic_tags=[tid],
                verb_tags=["탐구하다"], emoji=emoji, source_asset=src))
    write_json(rp("data","raw","jobs.json"), jobs)
    from collections import Counter
    c = Counter(j["source_asset"] for j in jobs)
    print(f"직업 {len(jobs)}건, 출처:", dict(c))
    print("Layer B 카드:", [j["name"] for j in jobs if j["layer"]=="B"][:12])

if __name__ == "__main__":
    main()
