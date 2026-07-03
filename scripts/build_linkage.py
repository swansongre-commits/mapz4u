"""Phase 3 - 연계방안 결정 (자동).
EMBED_TIER=3: TF-IDF(char 2-4gram)+코사인. 행동엣지 미생성(API 미활성) -> 의미 엣지만(RRF 미적용).
산출: db/vectors.pkl(벡터+id), data/clean/linkage.json(편성/인접/발견피드), DECISION_LOG 갱신.
"""
import sys, json, pickle
sys.path.insert(0, ".")
from common import p, read_json, write_json, TOPICS, TOPIC_IDS, TODAY
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

exp = read_json(p("data","clean","experiences.json"),[])
books = read_json(p("data","clean","books.json"),[])
people = read_json(p("data","clean","people.json"),[])
jobs = read_json(p("data","clean","jobs.json"),[])

def topic_text(tid):
    t=TOPICS[tid]; return t["name"]+" "+" ".join(t["synonyms"])
def exp_text(x):
    return " ".join([x["name"]," ".join(TOPICS[t]["name"] for t in x["topic_tags"]),
                     " ".join(x.get("verb_tags",[])), x.get("region","")])
def book_text(b):
    return " ".join([b["title"],b.get("author",""),
                     " ".join(TOPICS[t]["name"] for t in b["topic_tags"])])
def person_text(pe):
    return " ".join([pe["name"],pe["verb_desc"]," ".join(pe.get("job_lineage",[]))])
def job_text(j):
    return " ".join([j["name"],j["verb_desc"]," ".join(TOPICS[t]["name"] for t in j["topic_tags"])])

# 노드 코퍼스
nodes=[]  # (kind, id, text)
for t in TOPIC_IDS: nodes.append(("topic",t,topic_text(t)))
for x in exp: nodes.append(("exp",x["id"],exp_text(x)))
for b in books: nodes.append(("book",b["isbn"],book_text(b)))
for pe in people: nodes.append(("person",pe["id"],person_text(pe)))
for j in jobs: nodes.append(("job",j["id"],job_text(j)))

texts=[n[2] for n in nodes]
vec=TfidfVectorizer(analyzer="char_wb",ngram_range=(2,4),min_df=1)
X=vec.fit_transform(texts)
idx={ (n[0],n[1]):i for i,n in enumerate(nodes)}

def sim(a_kind,a_id,b_kind,b_id):
    return float(cosine_similarity(X[idx[(a_kind,a_id)]],X[idx[(b_kind,b_id)]])[0,0])

TODAY_ISO=TODAY.isoformat()
def is_live(x):
    if x.get("status")!="운영중": return False
    pe=x.get("period_end")
    if pe and pe<TODAY_ISO: return False
    return True

# ── 주제별 편성 ───────────────────────────────────────────
linkage={"generated":TODAY_ISO,"embed":"tfidf-char24","topics":{}}
for tid in TOPIC_IDS:
    # 체험: 해당 주제 + 운영중, 상설 우선 -> 상위 8
    cand=[x for x in exp if tid in x["topic_tags"] and is_live(x)]
    def exp_key(x):
        return (0 if x["type"]=="상설시설" else 1, -sim("topic",tid,"exp",x["id"]))
    cand.sort(key=exp_key)
    top_exp=[{"id":x["id"],"name":x["name"],"type":x["type"],
              "score":round(sim("topic",tid,"exp",x["id"]),4)} for x in cand[:8]]
    # 도서 상위 5
    bcand=[b for b in books if tid in b["topic_tags"]]
    bcand.sort(key=lambda b:-sim("topic",tid,"book",b["isbn"]))
    top_books=[{"isbn":b["isbn"],"title":b["title"],
                "score":round(sim("topic",tid,"book",b["isbn"]),4)} for b in bcand[:5]]
    # 인물 1
    pcand=[pe for pe in people if tid in pe["topic_tags"]]
    person=None
    if pcand:
        pcand.sort(key=lambda pe:-sim("topic",tid,"person",pe["id"]))
        person={"id":pcand[0]["id"],"name":pcand[0]["name"],
                "anti_stereotype":pcand[0].get("anti_stereotype",0)}
    # 직업 3~5, Layer B 카드 1
    jcand=[j for j in jobs if tid in j["topic_tags"]]
    jb=[j for j in jcand if j["layer"]=="B"]
    others=[j for j in jcand if j["layer"]!="B"]
    others.sort(key=lambda j:-sim("topic",tid,"job",j["id"]))
    chosen_jobs=(jb+others)[:5]
    layerB=jb[0]["id"] if jb else (chosen_jobs[0]["id"] if chosen_jobs else None)
    linkage["topics"][tid]={
        "name":TOPICS[tid]["name"],
        "experiences":top_exp,"books":top_books,"person":person,
        "jobs":[{"id":j["id"],"name":j["name"],"layer":j["layer"]} for j in chosen_jobs],
        "layerB_card":layerB}

# ── 주제 인접도 행렬 (옆으로 한 칸) ───────────────────────
# 주제 벡터 = 주제텍스트 벡터 + 해당 주제 상설체험 평균
def topic_vec(tid):
    ids=[idx[("topic",tid)]]
    ids+=[idx[("exp",x["id"])] for x in exp if tid in x["topic_tags"] and x["type"]=="상설시설"]
    return np.asarray(X[ids].mean(axis=0))
TV={t:topic_vec(t) for t in TOPIC_IDS}
adj={}
adj_matrix={}
for a in TOPIC_IDS:
    sims=[]
    for b in TOPIC_IDS:
        if a==b: continue
        s=float(cosine_similarity(TV[a],TV[b])[0,0]); sims.append((b,s))
    adj_matrix[a]={b:round(s,4) for b,s in sims}
    sims.sort(key=lambda z:-z[1])
    adj[a]=[{"topic":b,"name":TOPICS[b]["name"],"score":round(s,4)} for b,s in sims[:2]]
linkage["adjacency"]=adj
linkage["adjacency_matrix"]=adj_matrix

# ── 발견 피드 쿼터 ────────────────────────────────────────
# 최근 주제(기준=dino) 인접 1 + 먼 주제(인접도 최하) 1 + 반고정관념 인물 1
recent="dino"
near=adj[recent][0]["topic"]
far=min(adj_matrix[recent].items(),key=lambda z:z[1])[0]
anti=[pe for pe in people if pe.get("anti_stereotype")]
anti_pick=anti[0] if anti else people[0]
linkage["discover_quota"]={
    "recent_topic":recent,
    "near":{"topic":near,"name":TOPICS[near]["name"],
            "sample_exp":linkage["topics"][near]["experiences"][0] if linkage["topics"][near]["experiences"] else None},
    "far":{"topic":far,"name":TOPICS[far]["name"],
           "sample_exp":linkage["topics"][far]["experiences"][0] if linkage["topics"][far]["experiences"] else None},
    "anti_stereotype_person":{"id":anti_pick["id"],"name":anti_pick["name"]},
    "rule":"인기순 정렬 금지 - 쿼터 편성(인접1+먼주제1+반고정관념인물1)"}

write_json(p("data","clean","linkage.json"), linkage)
# 벡터 저장 (Phase 4 재사용, faiss 폴백=sklearn)
pickle.dump({"vectorizer":vec,"matrix":X,"nodes":nodes},
            open(p("db","vectors.pkl"),"wb"))

# G3: 빈 슬롯 검사
empties=[]
for tid in TOPIC_IDS:
    T=linkage["topics"][tid]
    if len(T["experiences"])==0: empties.append(f"{tid}:exp")
    if len(T["books"])==0: empties.append(f"{tid}:book")
    if T["person"] is None: empties.append(f"{tid}:person")
    if len(T["jobs"])==0: empties.append(f"{tid}:job")
g3 = len(empties)==0

# DECISION_LOG 갱신
dl=["\n## Phase 3 — 연계방안 결정 (자동)\n",
    f"- 임베딩: TF-IDF char_wb 2-4gram (EMBED_TIER=3). 행동엣지 미생성 → RRF 미적용, 의미(코사인) 엣지만.",
    f"- 연결 스코어 = topic↔node 코사인 유사도.\n",
    "### 주제별 편성 (체험8·도서5·인물1·직업≤5, Layer B 1)\n",
    "| 주제 | 체험(상위) | 도서(상위) | 인물 | Layer B 카드 |",
    "|---|---|---|---|---|"]
for tid in TOPIC_IDS:
    T=linkage["topics"][tid]
    e0=T["experiences"][0]["name"] if T["experiences"] else "-"
    b0=T["books"][0]["title"] if T["books"] else "-"
    pn=T["person"]["name"] if T["person"] else "-"
    lb=next((j["name"] for j in jobs if j["id"]==T["layerB_card"]),"-")
    dl.append(f"| {TOPICS[tid]['name']} | {len(T['experiences'])}건({e0}…) | {len(T['books'])}권({b0}…) | {pn} | {lb} |")
dl.append("\n### 옆으로 한 칸 (주제 인접 2개)\n")
for tid in TOPIC_IDS:
    nn=", ".join(f"{a['name']}({a['score']})" for a in adj[tid])
    dl.append(f"- {TOPICS[tid]['name']} → {nn}")
dl.append("\n### 발견 피드 쿼터\n")
dq=linkage["discover_quota"]
dl.append(f"- 기준 주제 {TOPICS[recent]['name']} / 인접 {dq['near']['name']} / 먼 주제 {dq['far']['name']} / 반고정관념 인물 {dq['anti_stereotype_person']['name']}")
dl.append(f"- 규칙: {dq['rule']}")
dl.append(f"\n**G3: {'PASS' if g3 else 'FAIL'}** (빈 슬롯: {empties or '없음'})")
open(p("reports","DECISION_LOG.md"),"a",encoding="utf-8").write("\n".join(dl)+"\n")

open(p("state","g3_result.txt"),"w",encoding="utf-8").write(
    f"G3 {'PASS' if g3 else 'FAIL'} empties={empties}\nadj_dino={adj['dino']}\n")
print("G3", "PASS" if g3 else "FAIL", "empties=", empties)
