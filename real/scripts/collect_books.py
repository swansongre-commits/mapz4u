"""운영 Phase 1 - 도서 수집 (정보나루 인기대출 실데이터). 주제별 상위 대출 도서 태깅.
연령밴드 = 대출 age_band. 대출가능/소장은 표기 자리(availability). 행동엣지는 미생성(API 미활성)."""
import sys, re
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, write_json, topics_dict, TODAY
from lib_corpus import load_all
from collections import defaultdict

TOPICS = topics_dict(); TIDS = list(TOPICS.keys())
LV = TODAY.isoformat()
BAND_LABEL = {"pre":"6-7","low":"8-9","mid1":"10-11","mid2":"12-13"}
PER_TOPIC = 8

def kdc_match(kdc, prefixes): return any(kdc.startswith(p) for p in prefixes) if kdc else False
def title_match(title, syns): return any(s in title for s in syns)

def norm_title(t):
    # 부제(: 이후) 제거 + 권차/숫자 제거 -> 시리즈 권 중복 접기
    base = t.split(":")[0].split("(")[0]
    base = re.sub(r"[0-9]+", "", base)
    return re.sub(r"\s+", "", base).strip()

def main():
    corpus = load_all(rp("data","raw","data4library"))
    # 제목(정규화) 기준 집계 -> 시리즈 권 중복 접기. 대표 ISBN/저자는 최다대출 권 채택.
    by_isbn = {}
    for band, rows in corpus.items():
        for r in rows:
            key = norm_title(r["title"]) + "|" + (r["author"][:10] if r["author"] else "")
            rec = by_isbn.get(key)
            if rec is None:
                rec = {**r, "isbn": r["isbn"] or key, "band_loans": {}, "_best": r["loan"]}
                by_isbn[key] = rec
            rec["band_loans"][band] = rec["band_loans"].get(band, 0) + r["loan"]
            if r["loan"] > rec.get("_best", 0):  # 대표 표기는 최다대출 권 기준
                rec.update({"title": r["title"], "isbn": r["isbn"] or key,
                            "kdc": r["kdc"], "pub_year": r["pub_year"], "_best": r["loan"]})
    # 주제 태깅 + 주제별 상위 선정
    topic_books = defaultdict(list)
    for isbn, r in by_isbn.items():
        tids = [tid for tid in TIDS
                if title_match(r["title"], TOPICS[tid]["synonyms"]) or kdc_match(r["kdc"], TOPICS[tid].get("kdc",[]))]
        if not tids: continue
        total_loan = sum(r["band_loans"].values())
        peak = max(r["band_loans"], key=r["band_loans"].get)
        for tid in tids:
            topic_books[tid].append((total_loan, r, peak))
    books, seen = [], set()
    for tid in TIDS:
        ranked = sorted(topic_books.get(tid, []), key=lambda z: -z[0])[:PER_TOPIC]
        for total_loan, r, peak in ranked:
            if r["isbn"] in seen:
                # 이미 다른 주제로 추가됨 - 주제만 병합
                for b in books:
                    if b["isbn"] == r["isbn"] and tid not in b["topic_tags"]:
                        b["topic_tags"].append(tid)
                continue
            seen.add(r["isbn"])
            books.append(dict(isbn=r["isbn"], title=r["title"], author=r["author"],
                publisher=r["publisher"], pub_year=r["pub_year"] or "", kdc=r["kdc"],
                topic_tags=[tid], age_band=BAND_LABEL.get(peak,""),
                loan_count=total_loan, availability="대출가능여부 조회 필요",
                source="data4library:인기대출(실데이터)", is_seed=0, last_verified=LV))
    write_json(rp("data","raw","books.json"), books)
    from collections import Counter
    c = Counter(t for b in books for t in b["topic_tags"])
    print(f"도서 {len(books)}권 (실데이터), 주제별:", {tid:c.get(tid,0) for tid in TIDS})
    open(rp("state","collect_books.txt"),"w",encoding="utf-8").write(
        f"books={len(books)} per_topic={dict(c)}")

if __name__ == "__main__":
    main()
