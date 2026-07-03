import sys, json
sys.path.insert(0, ".")
from common import p
exp = json.load(open(p("data","raw","experiences.json"), encoding="utf-8"))
books = json.load(open(p("data","raw","books.json"), encoding="utf-8"))
ppl = json.load(open(p("data","raw","people.json"), encoding="utf-8"))
jobs = json.load(open(p("data","raw","jobs.json"), encoding="utf-8"))
from collections import Counter
lb = [j["name"] for j in jobs if j["layer"] == "B"]
print("체험=%d(>=60:%s) 도서=%d(>=50:%s) 인물=%d(==5:%s) 직업=%d(>=25:%s)" % (
    len(exp), len(exp)>=60, len(books), len(books)>=50, len(ppl), len(ppl)==5, len(jobs), len(jobs)>=25))
print("Layer B 카드:", lb)
g1 = len(exp)>=60 and len(books)>=50 and len(ppl)==5 and len(jobs)>=25
print("G1", "PASS" if g1 else "FAIL")
