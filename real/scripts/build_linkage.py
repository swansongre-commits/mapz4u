"""운영 Phase 3 - 연계 결정. TF-IDF(char2-4gram) 코사인. 12주제 편성+인접+발견피드."""
import sys, pickle
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, read_json, write_json, topics_dict, TODAY
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

TOPICS = topics_dict(); TIDS = list(TOPICS.keys())
exp = read_json(rp("data","clean","experiences.json"),[])
books = read_json(rp("data","clean","books.json"),[])
people = read_json(rp("data","clean","people.json"),[])
jobs = read_json(rp("data","clean","jobs.json"),[])
EXP={x["id"]:x for x in exp}; BOOK={b["isbn"]:b for b in books}
PERSON={p["id"]:p for p in people}; JOB={j["id"]:j for j in jobs}
TODAY_ISO=TODAY.isoformat()

def ttext(t): return TOPICS[t]["name"]+" "+" ".join(TOPICS[t].get("synonyms",[]))
def etext(x): return x["name"]+" "+" ".join(TOPICS[t]["name"] for t in x["topic_tags"])+" "+x.get("region","")
def btext(b): return b["title"]+" "+b.get("author","")+" "+" ".join(TOPICS[t]["name"] for t in b["topic_tags"])
def pxt(p): return p["name"]+" "+p["verb_desc"]+" "+" ".join(p.get("job_lineage",[]))
def jtext(j): return j["name"]+" "+j["verb_desc"]

nodes=[("topic",t,ttext(t)) for t in TIDS]+[("exp",x["id"],etext(x)) for x in exp]+\
      [("book",b["isbn"],btext(b)) for b in books]+[("person",p["id"],pxt(p)) for p in people]+\
      [("job",j["id"],jtext(j)) for j in jobs]
vec=TfidfVectorizer(analyzer="char_wb",ngram_range=(2,4),min_df=1)
X=vec.fit_transform([n[2] for n in nodes])
idx={(n[0],n[1]):i for i,n in enumerate(nodes)}
def sim(ak,ai,bk,bi): return float(cosine_similarity(X[idx[(ak,ai)]],X[idx[(bk,bi)]])[0,0])
def live(x): return x.get("status")=="운영중" and not (x.get("period_end") and x["period_end"]<TODAY_ISO)

link={"generated":TODAY_ISO,"embed":"tfidf-char24","topics":{}}
for tid in TIDS:
    cand=[x for x in exp if tid in x["topic_tags"] and live(x)]
    cand.sort(key=lambda x:(0 if x["type"]=="상설시설" else 1, -sim("topic",tid,"exp",x["id"])))
    te=[{"id":x["id"],"name":x["name"],"type":x["type"],"score":round(sim("topic",tid,"exp",x["id"]),4)} for x in cand[:8]]
    bc=[b for b in books if tid in b["topic_tags"]]; bc.sort(key=lambda b:-sim("topic",tid,"book",b["isbn"]))
    tb=[{"isbn":b["isbn"],"title":b["title"],"score":round(sim("topic",tid,"book",b["isbn"]),4)} for b in bc[:5]]
    pc=[p for p in people if tid in p["topic_tags"]]
    person={"id":pc[0]["id"],"name":pc[0]["name"],"anti_stereotype":pc[0].get("anti_stereotype",0)} if pc else None
    jc=[j for j in jobs if tid in j["topic_tags"]]; jb=[j for j in jc if j["layer"]=="B"]
    others=[j for j in jc if j["layer"]!="B"]; others.sort(key=lambda j:-sim("topic",tid,"job",j["id"]))
    cj=(jb+others)[:5]
    link["topics"][tid]={"name":TOPICS[tid]["name"],"experiences":te,"books":tb,"person":person,
        "jobs":[{"id":j["id"],"name":j["name"],"layer":j["layer"]} for j in cj],
        "layerB_card":jb[0]["id"] if jb else (cj[0]["id"] if cj else None)}

def tvec(t):
    ids=[idx[("topic",t)]]+[idx[("exp",x["id"])] for x in exp if t in x["topic_tags"] and x["type"]=="상설시설"]
    return np.asarray(X[ids].mean(axis=0))
TV={t:tvec(t) for t in TIDS}; adj={}; adjm={}
for a in TIDS:
    sims=[(b,float(cosine_similarity(TV[a],TV[b])[0,0])) for b in TIDS if b!=a]
    adjm[a]={b:round(s,4) for b,s in sims}; sims.sort(key=lambda z:-z[1])
    adj[a]=[{"topic":b,"name":TOPICS[b]["name"],"score":round(s,4)} for b,s in sims[:2]]
link["adjacency"]=adj; link["adjacency_matrix"]=adjm

recent=TIDS[0]; near=adj[recent][0]["topic"]; far=min(adjm[recent].items(),key=lambda z:z[1])[0]
anti=[p for p in people if p.get("anti_stereotype")]; ap=anti[0] if anti else people[0]
link["discover_quota"]={"recent_topic":recent,
    "near":{"topic":near,"name":TOPICS[near]["name"],"sample_exp":link["topics"][near]["experiences"][0] if link["topics"][near]["experiences"] else None},
    "far":{"topic":far,"name":TOPICS[far]["name"],"sample_exp":link["topics"][far]["experiences"][0] if link["topics"][far]["experiences"] else None},
    "anti_stereotype_person":{"id":ap["id"],"name":ap["name"]},
    "rule":"인기순 정렬 금지 - 쿼터 편성(인접1+먼주제1+반고정관념인물1)"}
write_json(rp("data","clean","linkage.json"),link)
pickle.dump({"vectorizer":vec,"matrix":X,"nodes":nodes},open(rp("db","vectors.pkl"),"wb"))
empties=[f"{t}:{k}" for t in TIDS for k,v in [("exp",link["topics"][t]["experiences"]),("book",link["topics"][t]["books"]),("job",link["topics"][t]["jobs"])] if not v]+[f"{t}:person" for t in TIDS if not link["topics"][t]["person"]]
g3=len(empties)==0
open(rp("state","g3_result.txt"),"w",encoding="utf-8").write(f"G3 {'PASS' if g3 else 'FAIL'} empties={empties}")
print("G3","PASS" if g3 else "FAIL","empties=",empties)
print("인접 예시:",TIDS[0],"->",adj[TIDS[0]])
