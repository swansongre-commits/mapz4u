"""Phase 4 - 임베딩·DB 구축. SQLite db/mapz.db 생성 + 벡터 인덱스(sklearn 폴백).
DDL은 AUTOPILOT Phase4 요지 준수. 리스트 필드는 JSON 문자열로 저장.
"""
import sys, json, sqlite3, pickle, os
sys.path.insert(0, ".")
from common import p, read_json, TOPICS, TOPIC_IDS

DB=p("db","mapz.db")
if os.path.exists(DB): os.remove(DB)
con=sqlite3.connect(DB); cur=con.cursor()

cur.executescript("""
CREATE TABLE topic(id TEXT PRIMARY KEY, name TEXT, synonyms TEXT, emoji TEXT);
CREATE TABLE experience(id TEXT PRIMARY KEY, name TEXT, type TEXT, topic_tags TEXT,
  verb_tags TEXT, lat REAL, lng REAL, region TEXT, period_start TEXT, period_end TEXT,
  hours TEXT, age_note TEXT, duration_min INT, cost TEXT, reservation_url TEXT,
  indoor INT, parking TEXT, stroller TEXT, crowd_note TEXT, related_books TEXT,
  source TEXT, is_seed INT, last_verified TEXT, status TEXT);
CREATE TABLE book(isbn TEXT PRIMARY KEY, title TEXT, author TEXT, publisher TEXT,
  pub_year INT, kdc TEXT, topic_tags TEXT, age_band TEXT, availability TEXT,
  source TEXT, is_seed INT, last_verified TEXT);
CREATE TABLE person(id TEXT PRIMARY KEY, name TEXT, era TEXT, verb_desc TEXT,
  story_trial TEXT, sites TEXT, job_lineage TEXT, anti_stereotype INT, topic_tags TEXT);
CREATE TABLE job(id TEXT PRIMARY KEY, name TEXT, verb_desc TEXT, layer TEXT, topic_tags TEXT,
  source_asset TEXT, emoji TEXT);
CREATE TABLE edge(src_type TEXT, src_id TEXT, dst_type TEXT, dst_id TEXT,
  edge_type TEXT, score REAL, source TEXT);
CREATE INDEX idx_exp_status ON experience(status);
CREATE INDEX idx_exp_period ON experience(period_end);
CREATE INDEX idx_exp_topic ON experience(topic_tags);
CREATE INDEX idx_book_topic ON book(topic_tags);
CREATE INDEX idx_edge_src ON edge(src_type,src_id);
""")

def js(v): return json.dumps(v,ensure_ascii=False)

# topic
for tid in TOPIC_IDS:
    t=TOPICS[tid]
    cur.execute("INSERT INTO topic VALUES(?,?,?,?)",(tid,t["name"],js(t["synonyms"]),t["emoji"]))

exp=read_json(p("data","clean","experiences.json"),[])
for x in exp:
    cur.execute("INSERT INTO experience VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(
        x["id"],x["name"],x["type"],js(x["topic_tags"]),js(x.get("verb_tags",[])),
        x["lat"],x["lng"],x.get("region",""),x.get("period_start"),x.get("period_end"),
        x.get("hours",""),x.get("age_note",""),x.get("duration_min"),x.get("cost",""),
        x.get("reservation_url",""),x.get("indoor",1),x.get("parking",""),x.get("stroller",""),
        x.get("crowd_note",""),js(x.get("related_books",[])),x["source"],x.get("is_seed",0),
        x["last_verified"],x["status"]))

books=read_json(p("data","clean","books.json"),[])
for b in books:
    cur.execute("INSERT INTO book VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(
        b["isbn"],b["title"],b.get("author",""),b.get("publisher",""),b.get("pub_year"),
        b.get("kdc",""),js(b["topic_tags"]),b.get("age_band",""),b.get("availability",""),
        b["source"],b.get("is_seed",0),b["last_verified"]))

people=read_json(p("data","clean","people.json"),[])
for pe in people:
    cur.execute("INSERT INTO person VALUES(?,?,?,?,?,?,?,?,?)",(
        pe["id"],pe["name"],pe.get("era",""),pe["verb_desc"],pe.get("story_trial",""),
        js(pe.get("sites",[])),js(pe.get("job_lineage",[])),pe.get("anti_stereotype",0),
        js(pe["topic_tags"])))

jobs=read_json(p("data","clean","jobs.json"),[])
for j in jobs:
    cur.execute("INSERT INTO job VALUES(?,?,?,?,?,?,?)",(
        j["id"],j["name"],j["verb_desc"],j["layer"],js(j["topic_tags"]),
        j.get("source_asset",""),j.get("emoji","")))

# edges from linkage
link=read_json(p("data","clean","linkage.json"),{})
ne=0
for tid,T in link.get("topics",{}).items():
    for e in T["experiences"]:
        cur.execute("INSERT INTO edge VALUES(?,?,?,?,?,?,?)",("topic",tid,"exp",e["id"],"semantic",e["score"],"tfidf")); ne+=1
    for b in T["books"]:
        cur.execute("INSERT INTO edge VALUES(?,?,?,?,?,?,?)",("topic",tid,"book",b["isbn"],"semantic",b["score"],"tfidf")); ne+=1
    if T["person"]:
        cur.execute("INSERT INTO edge VALUES(?,?,?,?,?,?,?)",("topic",tid,"person",T["person"]["id"],"semantic",1.0,"tfidf")); ne+=1
    for j in T["jobs"]:
        cur.execute("INSERT INTO edge VALUES(?,?,?,?,?,?,?)",("topic",tid,"job",j["id"],"lineage",1.0,"maps")); ne+=1
for a,lst in link.get("adjacency",{}).items():
    for adj in lst:
        cur.execute("INSERT INTO edge VALUES(?,?,?,?,?,?,?)",("topic",a,"topic",adj["topic"],"adjacent",adj["score"],"tfidf")); ne+=1
# person-job lineage (one-to-many)
for pe in people:
    for jobname in pe.get("job_lineage",[]):
        cur.execute("INSERT INTO edge VALUES(?,?,?,?,?,?,?)",("person",pe["id"],"jobname",jobname,"lineage",1.0,"seed")); ne+=1

con.commit()

# 벡터 인덱스: FAISS 미설치 -> sklearn NearestNeighbors 폴백 저장
vd=pickle.load(open(p("db","vectors.pkl"),"rb"))
try:
    import faiss  # noqa
    faiss_ok=True
except Exception:
    faiss_ok=False
from sklearn.neighbors import NearestNeighbors
X=vd["matrix"]
nn=NearestNeighbors(n_neighbors=min(10,X.shape[0]),metric="cosine").fit(X)
pickle.dump({"nn":nn,"nodes":vd["nodes"],"vectorizer":vd["vectorizer"],"matrix":X},
            open(p("db","index.pkl"),"wb"))

# G4: 행수 일치 + 조인 무결성
counts={}
for tbl,expect in [("experience",len(exp)),("book",len(books)),("person",len(people)),("job",len(jobs)),("topic",5)]:
    got=cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    counts[tbl]=(got,expect,got==expect)
# 조인 무결성: 모든 edge의 exp dst가 experience에 존재
orphan=cur.execute("""SELECT COUNT(*) FROM edge WHERE dst_type='exp' AND dst_id NOT IN (SELECT id FROM experience)""").fetchone()[0]
orphan_b=cur.execute("""SELECT COUNT(*) FROM edge WHERE dst_type='book' AND dst_id NOT IN (SELECT isbn FROM book)""").fetchone()[0]
g4 = all(v[2] for v in counts.values()) and orphan==0 and orphan_b==0
con.close()

res=[f"{k}: got={v[0]} expect={v[1]} ok={v[2]}" for k,v in counts.items()]
res.append(f"edges={ne} orphan_exp={orphan} orphan_book={orphan_b}")
res.append(f"faiss={faiss_ok} (폴백=sklearn NearestNeighbors)")
res.append(f"G4 {'PASS' if g4 else 'FAIL'}")
open(p("state","g4_result.txt"),"w",encoding="utf-8").write("\n".join(res))
print("\n".join(res))
