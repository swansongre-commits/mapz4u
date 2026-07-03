"""Phase 2 - 데이터 품질 게이트.
- 필수 필드 존재, 스키마 적합률 >=95%
- 좌표 유효성(한국 bbox), 위반 제외
- 중복 제거: (명칭 정규화 + 좌표 반올림 3자리)
- 주제 태그: 관리 사전 매핑, 미매핑 재분류 1회 후 제외
- 주제당 상설 체험 >=8 유지
산출: data/clean/*.json, reports/data_quality.md
"""
import sys, json
sys.path.insert(0, ".")
from common import p, read_json, write_json, norm_name, in_kr, TOPICS, TOPIC_IDS, TODAY
from collections import Counter, defaultdict

report = []
def log(s): report.append(s);

EXP_REQUIRED = ["id", "name", "lat", "lng", "topic_tags", "last_verified", "status", "source", "is_seed"]
BOOK_REQUIRED = ["isbn", "title", "topic_tags", "last_verified", "source", "is_seed"]
PERSON_REQUIRED = ["id", "name", "topic_tags", "verb_desc"]
JOB_REQUIRED = ["id", "name", "verb_desc", "topic_tags", "layer", "source_asset"]

def valid_topics(tags):
    return [t for t in (tags or []) if t in TOPICS]

def validate_experiences():
    raw = read_json(p("data","raw","experiences.json"), [])
    total = len(raw)
    kept, dropped = [], Counter()
    seen = set()
    schema_ok = 0
    for r in raw:
        # 스키마 적합
        missing = [f for f in EXP_REQUIRED if f not in r or r[f] in (None, "") and f not in ("lat","lng")]
        # lat/lng None 은 좌표검사에서 처리
        has_core = all(f in r for f in EXP_REQUIRED)
        if has_core:
            schema_ok += 1
        # 좌표 유효
        if not in_kr(r.get("lat"), r.get("lng")):
            dropped["좌표범위밖"] += 1; continue
        # 주제 매핑 (미매핑 재분류 1회: 이름으로 재추론)
        vt = valid_topics(r.get("topic_tags"))
        if not vt:
            from common import topic_of_text
            vt = topic_of_text(r.get("name",""))
            if not vt:
                dropped["주제미매핑"] += 1; continue
            r["topic_tags"] = vt
        else:
            r["topic_tags"] = vt
        # 중복
        key = (norm_name(r["name"]), round(float(r["lat"]),3), round(float(r["lng"]),3))
        if key in seen:
            dropped["중복"] += 1; continue
        seen.add(key)
        kept.append(r)
    rate = schema_ok/total*100 if total else 0
    write_json(p("data","clean","experiences.json"), kept)
    return dict(total=total, kept=len(kept), dropped=dict(dropped), schema_rate=rate)

def validate_books():
    raw = read_json(p("data","raw","books.json"), [])
    total=len(raw); kept=[]; dropped=Counter(); seen=set(); schema_ok=0
    for r in raw:
        if all(f in r and r[f] not in (None,"") for f in BOOK_REQUIRED):
            schema_ok+=1
        else:
            dropped["스키마미달"]+=1; continue
        vt=valid_topics(r.get("topic_tags"))
        if not vt: dropped["주제미매핑"]+=1; continue
        r["topic_tags"]=vt
        if r["isbn"] in seen: dropped["중복ISBN"]+=1; continue
        seen.add(r["isbn"]); kept.append(r)
    rate=schema_ok/total*100 if total else 0
    write_json(p("data","clean","books.json"), kept)
    return dict(total=total,kept=len(kept),dropped=dict(dropped),schema_rate=rate)

def validate_people():
    raw=read_json(p("data","raw","people.json"),[])
    total=len(raw); kept=[]; schema_ok=0; dropped=Counter()
    for r in raw:
        if all(f in r and r[f] for f in PERSON_REQUIRED): schema_ok+=1
        else: dropped["스키마미달"]+=1; continue
        r["topic_tags"]=valid_topics(r.get("topic_tags")); kept.append(r)
    rate=schema_ok/total*100 if total else 0
    write_json(p("data","clean","people.json"), kept)
    return dict(total=total,kept=len(kept),dropped=dict(dropped),schema_rate=rate)

def validate_jobs():
    raw=read_json(p("data","raw","jobs.json"),[])
    total=len(raw); kept=[]; schema_ok=0; dropped=Counter()
    for r in raw:
        if all(f in r and r[f] not in (None,"") for f in JOB_REQUIRED): schema_ok+=1
        else: dropped["스키마미달"]+=1; continue
        r["topic_tags"]=valid_topics(r.get("topic_tags")); kept.append(r)
    rate=schema_ok/total*100 if total else 0
    write_json(p("data","clean","jobs.json"), kept)
    return dict(total=total,kept=len(kept),dropped=dict(dropped),schema_rate=rate)

def main():
    e=validate_experiences(); b=validate_books(); pe=validate_people(); j=validate_jobs()
    # 주제당 상설 카운트
    exp=read_json(p("data","clean","experiences.json"),[])
    perm_by_topic=Counter()
    for x in exp:
        if x["type"]=="상설시설":
            for t in x["topic_tags"]: perm_by_topic[t]+=1
    min_perm=min(perm_by_topic.get(t,0) for t in TOPIC_IDS)
    # 소스 구성비
    src=Counter(x["source"].split(":")[0] for x in exp)
    seedcnt=sum(1 for x in exp if x.get("is_seed"))
    overall_rate=min(e["schema_rate"],b["schema_rate"],pe["schema_rate"],j["schema_rate"])
    g2 = overall_rate>=95 and min_perm>=8

    md=[]
    md.append("# Phase 2 — 데이터 품질 리포트 (data_quality.md)\n")
    md.append(f"- 실행일: {TODAY.isoformat()} · MODE: MIXED · EMBED_TIER: 3\n")
    md.append("## 건수·제외 통계\n")
    md.append("| 데이터 | 원본 | 정제 | 스키마적합률 | 제외 사유 |")
    md.append("|---|---|---|---|---|")
    md.append(f"| 체험 | {e['total']} | {e['kept']} | {e['schema_rate']:.1f}% | {e['dropped']} |")
    md.append(f"| 도서 | {b['total']} | {b['kept']} | {b['schema_rate']:.1f}% | {b['dropped']} |")
    md.append(f"| 인물 | {pe['total']} | {pe['kept']} | {pe['schema_rate']:.1f}% | {pe['dropped']} |")
    md.append(f"| 직업 | {j['total']} | {j['kept']} | {j['schema_rate']:.1f}% | {j['dropped']} |")
    md.append("\n## 주제별 상설 체험 (>=8 필요)\n")
    md.append("| 주제 | 상설 수 |")
    md.append("|---|---|")
    for t in TOPIC_IDS:
        md.append(f"| {TOPICS[t]['name']}({t}) | {perm_by_topic.get(t,0)} |")
    md.append(f"\n- 최소 주제 상설 수: **{min_perm}**")
    md.append(f"\n## MODE·소스 구성비 (체험)\n")
    md.append(f"- 소스: {dict(src)}")
    md.append(f"- is_seed(표본) 건수: {seedcnt} / {len(exp)} ({seedcnt/len(exp)*100:.0f}%)")
    md.append(f"- 실데이터(OSM 등): {len(exp)-seedcnt}건\n")
    md.append(f"## 게이트 G2\n")
    md.append(f"- 스키마 적합률(최저) {overall_rate:.1f}% (>=95%: {overall_rate>=95})")
    md.append(f"- 주제당 상설 >=8: {min_perm>=8}")
    md.append(f"- **G2: {'PASS' if g2 else 'FAIL'}**")
    open(p("reports","data_quality.md"),"w",encoding="utf-8").write("\n".join(md))

    out=[f"체험 {e['kept']}/{e['total']} 적합{e['schema_rate']:.1f}%",
         f"도서 {b['kept']}/{b['total']}",f"인물 {pe['kept']}",f"직업 {j['kept']}",
         f"주제별상설 {dict(perm_by_topic)} min={min_perm}",
         f"G2 {'PASS' if g2 else 'FAIL'} (rate={overall_rate:.1f})"]
    open(p("state","g2_result.txt"),"w",encoding="utf-8").write("\n".join(out))
    print("\n".join(out))

if __name__=="__main__":
    main()
