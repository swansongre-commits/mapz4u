"""운영 Phase 4 - SQLite db/mapz_real.db. 실데이터. experience에 tel/image 컬럼 추가."""
import sys, json, sqlite3, os, pickle
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, read_json, topics_dict

TOPICS = topics_dict()
DB = rp("db","mapz_real.db")
if os.path.exists(DB): os.remove(DB)
con = sqlite3.connect(DB); cur = con.cursor()
cur.executescript("""
CREATE TABLE topic(id TEXT PRIMARY KEY, name TEXT, synonyms TEXT, emoji TEXT,
  demand_score REAL, connection_score REAL, age_profile TEXT);
CREATE TABLE experience(id TEXT PRIMARY KEY, name TEXT, type TEXT, topic_tags TEXT,
  verb_tags TEXT, lat REAL, lng REAL, region TEXT, period_start TEXT, period_end TEXT,
  hours TEXT, age_note TEXT, duration_min INT, cost TEXT, reservation_url TEXT,
  indoor INT, parking TEXT, stroller TEXT, crowd_note TEXT, related_books TEXT,
  tel TEXT, image TEXT, source TEXT, is_seed INT, last_verified TEXT, status TEXT);
CREATE TABLE book(isbn TEXT PRIMARY KEY, title TEXT, author TEXT, publisher TEXT,
  pub_year TEXT, kdc TEXT, topic_tags TEXT, age_band TEXT, availability TEXT,
  loan_count INT, source TEXT, is_seed INT, last_verified TEXT);
CREATE TABLE person(id TEXT PRIMARY KEY, name TEXT, era TEXT, verb_desc TEXT,
  story_trial TEXT, sites TEXT, job_lineage TEXT, anti_stereotype INT, topic_tags TEXT);
CREATE TABLE job(id TEXT PRIMARY KEY, name TEXT, verb_desc TEXT, layer TEXT, topic_tags TEXT,
  source_asset TEXT, emoji TEXT);
CREATE TABLE edge(src_type TEXT, src_id TEXT, dst_type TEXT, dst_id TEXT, edge_type TEXT, score REAL, source TEXT);
CREATE TABLE recheck_queue(id TEXT, kind TEXT, name TEXT, last_verified TEXT, days_over INT, added TEXT);
CREATE INDEX idx_exp_status ON experience(status);
CREATE INDEX idx_exp_period ON experience(period_end);
CREATE INDEX idx_exp_topic ON experience(topic_tags);
CREATE INDEX idx_book_topic ON book(topic_tags);
CREATE INDEX idx_edge_src ON edge(src_type,src_id);
""")
def js(v): return json.dumps(v, ensure_ascii=False)

tmeta = read_json(rp("data","topics","topics_v1.json"),{}).get("topics",[])
tm = {t["id"]:t for t in tmeta}
for tid,t in TOPICS.items():
    m = tm.get(tid,{})
    cur.execute("INSERT INTO topic VALUES(?,?,?,?,?,?,?)",(tid,t["name"],js(t.get("synonyms",[])),
        t.get("emoji",""),m.get("demand_score"),m.get("connection_score"),js(m.get("age_profile",{}))))

exp=read_json(rp("data","clean","experiences.json"),[])
for x in exp:
    cur.execute("INSERT INTO experience VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(
        x["id"],x["name"],x["type"],js(x["topic_tags"]),js(x.get("verb_tags",[])),x["lat"],x["lng"],
        x.get("region",""),x.get("period_start"),x.get("period_end"),x.get("hours",""),x.get("age_note",""),
        x.get("duration_min"),x.get("cost",""),x.get("reservation_url",""),x.get("indoor",1),x.get("parking",""),
        x.get("stroller",""),x.get("crowd_note",""),js(x.get("related_books",[])),x.get("tel",""),x.get("image",""),
        x["source"],x.get("is_seed",0),x["last_verified"],x["status"]))

for b in read_json(rp("data","clean","books.json"),[]):
    cur.execute("INSERT INTO book VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(b["isbn"],b["title"],b.get("author",""),
        b.get("publisher",""),str(b.get("pub_year","")),b.get("kdc",""),js(b["topic_tags"]),b.get("age_band",""),
        b.get("availability",""),b.get("loan_count",0),b["source"],b.get("is_seed",0),b["last_verified"]))

for p in read_json(rp("data","clean","people.json"),[]):
    cur.execute("INSERT INTO person VALUES(?,?,?,?,?,?,?,?,?)",(p["id"],p["name"],p.get("era",""),p["verb_desc"],
        p.get("story_trial",""),js(p.get("sites",[])),js(p.get("job_lineage",[])),p.get("anti_stereotype",0),js(p["topic_tags"])))

for j in read_json(rp("data","clean","jobs.json"),[]):
    cur.execute("INSERT INTO job VALUES(?,?,?,?,?,?,?)",(j["id"],j["name"],j["verb_desc"],j["layer"],
        js(j["topic_tags"]),j.get("source_asset",""),j.get("emoji","")))

link=read_json(rp("data","clean","linkage.json"),{}); ne=0
for tid,T in link.get("topics",{}).items():
    for e in T["experiences"]: cur.execute("INSERT INTO edge VALUES('topic',?,'exp',?,'semantic',?,'tfidf')",(tid,e["id"],e["score"])); ne+=1
    for b in T["books"]: cur.execute("INSERT INTO edge VALUES('topic',?,'book',?,'semantic',?,'tfidf')",(tid,b["isbn"],b["score"])); ne+=1
    if T["person"]: cur.execute("INSERT INTO edge VALUES('topic',?,'person',?,'semantic',1.0,'tfidf')",(tid,T["person"]["id"])); ne+=1
    for j in T["jobs"]: cur.execute("INSERT INTO edge VALUES('topic',?,'job',?,'lineage',1.0,'maps')",(tid,j["id"])); ne+=1
for a,lst in link.get("adjacency",{}).items():
    for x in lst: cur.execute("INSERT INTO edge VALUES('topic',?,'topic',?,'adjacent',?,'tfidf')",(a,x["topic"],x["score"])); ne+=1
for p in read_json(rp("data","clean","people.json"),[]):
    for jn in p.get("job_lineage",[]): cur.execute("INSERT INTO edge VALUES('person',?,'jobname',?,'lineage',1.0,'seed')",(p["id"],jn)); ne+=1
con.commit()

vd=pickle.load(open(rp("db","vectors.pkl"),"rb"))
from sklearn.neighbors import NearestNeighbors
X=vd["matrix"]; nn=NearestNeighbors(n_neighbors=min(10,X.shape[0]),metric="cosine").fit(X)
pickle.dump({"nn":nn,"nodes":vd["nodes"],"vectorizer":vd["vectorizer"],"matrix":X},open(rp("db","index.pkl"),"wb"))

counts={}
for tbl,expect in [("experience",len(exp)),("book",len(read_json(rp('data','clean','books.json'),[]))),
                   ("person",len(read_json(rp('data','clean','people.json'),[]))),
                   ("job",len(read_json(rp('data','clean','jobs.json'),[]))),("topic",len(TOPICS))]:
    got=cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]; counts[tbl]=(got,expect,got==expect)
orphan=cur.execute("SELECT COUNT(*) FROM edge WHERE dst_type='exp' AND dst_id NOT IN (SELECT id FROM experience)").fetchone()[0]
g4=all(v[2] for v in counts.values()) and orphan==0
con.close()
r="\n".join([f"{k}:{v}" for k,v in counts.items()]+[f"edges={ne} orphan={orphan}",f"G4 {'PASS' if g4 else 'FAIL'}"])
open(rp("state","g4_result.txt"),"w",encoding="utf-8").write(r); print(r)
