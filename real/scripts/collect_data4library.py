"""운영 Phase 1 - 정보나루 인기대출 API 자동 수집.
과거 수동 다운로드 CSV(연령대별 4파일)와 같은 조건을 API로 재현한다.
  기간: 최근 12개월 (어제까지) / ISBN 부가기호: 아동(addCode=7) / 연령: 6~7, 8~9, 10~11, 12~13세 / 상위 1000건
산출: data/raw/data4library_api/{band}.json  (lib_corpus.load_all 이 CSV보다 우선해서 읽음)
안전: 4개 구간이 모두 성공했을 때만 저장한다. 하나라도 실패하거나 수량이 비정상이면 기존 파일을 유지하고 종료코드 2.
"""
import sys, json, time, datetime, urllib.request, urllib.parse
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, write_json, load_env, TODAY

BANDS = {"pre": (6, 7), "low": (8, 9), "mid1": (10, 11), "mid2": (12, 13)}
MIN_ROWS = 300
API = "http://data4library.kr/api/loanItemSrch"


def fetch_band(key, frm, to, start, end):
    params = {"authKey": key, "startDt": start, "endDt": end, "from_age": frm, "to_age": to,
              "addCode": 7, "pageNo": 1, "pageSize": 1000, "format": "json"}
    url = API + "?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MAPZ/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read().decode("utf-8"))
            resp = data.get("response", {})
            if resp.get("error") or resp.get("errCode"):
                raise RuntimeError(resp.get("error") or resp.get("errCode"))
            rows = []
            for d in resp.get("docs", []):
                doc = d.get("doc", {})
                title = (doc.get("bookname") or "").strip()
                if not title:
                    continue
                try:
                    loan = int(str(doc.get("loan_count", "0")).replace(",", ""))
                except ValueError:
                    loan = 0
                rows.append({"rank": str(doc.get("ranking", "")), "title": title,
                             "author": (doc.get("authors") or "").strip(),
                             "publisher": (doc.get("publisher") or "").strip(),
                             "pub_year": str(doc.get("publication_year") or ""),
                             "isbn": str(doc.get("isbn13") or ""),
                             "isbn_add": str(doc.get("addition_symbol") or ""),
                             "kdc": str(doc.get("class_no") or ""), "loan": loan})
            return rows
        except Exception as ex:
            last = ex
            time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"{frm}~{to}세 수집 실패: {str(last)[:120]}")


def main():
    key = load_env().get("DATA4LIBRARY_KEY")
    if not key:
        print("DATA4LIBRARY_KEY 없음")
        sys.exit(2)
    end = TODAY - datetime.timedelta(days=1)
    start = end - datetime.timedelta(days=365)
    s, e = start.isoformat(), end.isoformat()
    print(f"=== 정보나루 인기대출 API 수집 ({s} ~ {e}, 아동 부가기호) ===")
    results = {}
    for band, (frm, to) in BANDS.items():
        try:
            rows = fetch_band(key, frm, to, s, e)
        except Exception as ex:
            print(f"{band}: {ex} -> 저장 안 함")
            sys.exit(2)
        if len(rows) < MIN_ROWS:
            print(f"{band}: {len(rows)}건 (최소 {MIN_ROWS} 미달) -> 저장 안 함")
            sys.exit(2)
        results[band] = rows
        print(f"{band} ({frm}~{to}세): {len(rows)}건")
        time.sleep(1)
    for band, rows in results.items():
        write_json(rp("data", "raw", "data4library_api", f"{band}.json"),
                   {"source": "data4library:loanItemSrch", "period": [s, e], "age": list(BANDS[band]),
                    "addCode": 7, "fetched": TODAY.isoformat(), "rows": rows})
    total = sum(len(v) for v in results.values())
    with open(rp("state", "data4library_result.txt"), "w", encoding="utf-8") as f:
        f.write(f"period={s}~{e} rows={total} " + " ".join(f"{b}={len(v)}" for b, v in results.items()))
    print(f"저장: data/raw/data4library_api/*.json (총 {total}행)")


if __name__ == "__main__":
    main()
