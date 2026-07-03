"""운영 Phase 2 - 검토. 스키마·좌표·중복·주제매핑. 실데이터 위주라 최소건수 완화."""
import sys
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, read_json, write_json, norm_name, in_kr, topics_dict, TODAY
from collections import Counter

TOPICS = topics_dict(); TIDS = list(TOPICS.keys())
def vt(tags): return [t for t in (tags or []) if t in TOPICS]

def v_exp():
    raw = read_json(rp("data","raw","experiences.json"), [])
    kept, seen, dropped, ok = [], set(), Counter(), 0
    for r in raw:
        if all(k in r for k in ("id","name","lat","lng","topic_tags","last_verified","status")): ok += 1
        if not in_kr(r.get("lat"), r.get("lng")): dropped["좌표"] += 1; continue
        r["topic_tags"] = vt(r.get("topic_tags"))
        if not r["topic_tags"]: dropped["주제미매핑"] += 1; continue
        k = (norm_name(r["name"]), round(float(r["lat"]),3), round(float(r["lng"]),3))
        if k in seen: dropped["중복"] += 1; continue
        seen.add(k); kept.append(r)
    write_json(rp("data","clean","experiences.json"), kept)
    return len(raw), len(kept), dict(dropped), ok/len(raw)*100 if raw else 0

def v_simple(name, req, key=None):
    raw = read_json(rp("data","raw",name+".json"), [])
    kept, seen, ok = [], set(), 0
    for r in raw:
        if all(k in r and r[k] not in (None,"") for k in req): ok += 1
        else: continue
        r["topic_tags"] = vt(r.get("topic_tags"))
        if "topic_tags" in req and not r["topic_tags"]: continue
        if key:
            if r[key] in seen: continue
            seen.add(r[key])
        kept.append(r)
    write_json(rp("data","clean",name+".json"), kept)
    return len(raw), len(kept), ok/len(raw)*100 if raw else 100

def main():
    e = v_exp()
    b = v_simple("books", ["isbn","title","topic_tags","last_verified"], "isbn")
    p = v_simple("people", ["id","name","topic_tags","verb_desc"], "id")
    j = v_simple("jobs", ["id","name","verb_desc","topic_tags","layer"], "id")
    exp = read_json(rp("data","clean","experiences.json"), [])
    perm = Counter(t for x in exp if x["type"]=="상설시설" for t in x["topic_tags"])
    minperm = min(perm.get(t,0) for t in TIDS)
    rate = min(e[3], b[2], p[2], j[2])
    g2 = rate >= 95 and minperm >= 3   # 실데이터 트랙: 주제당 상설 >=3
    md = ["# 운영 Phase 2 — 데이터 품질 리포트\n",
          f"- 실행일 {TODAY.isoformat()} · 주제 {len(TIDS)}개\n",
          "| 데이터 | 원본 | 정제 | 적합률 |","|---|---|---|---|",
          f"| 체험 | {e[0]} | {e[1]} | {e[3]:.1f}% (제외 {e[2]}) |",
          f"| 도서 | {b[0]} | {b[1]} | {b[2]:.1f}% |",
          f"| 인물 | {p[0]} | {p[1]} | {p[2]:.1f}% |",
          f"| 직업 | {j[0]} | {j[1]} | {j[2]:.1f}% |",
          f"\n주제별 상설: {dict(perm)}", f"최소 상설 {minperm} (>=3)",
          f"\n실데이터 비율(체험): {sum(1 for x in exp if not x.get('is_seed'))}/{len(exp)}",
          f"\n**G2: {'PASS' if g2 else 'FAIL'}** (적합률 {rate:.1f}%, 최소상설 {minperm})"]
    open(rp("reports","data_quality.md"),"w",encoding="utf-8").write("\n".join(md))
    r = f"체험{e[1]} 도서{b[1]} 인물{p[1]} 직업{j[1]} minperm={minperm} G2={'PASS' if g2 else 'FAIL'}"
    open(rp("state","g2_result.txt"),"w",encoding="utf-8").write(r)
    print(r)

if __name__ == "__main__":
    main()
