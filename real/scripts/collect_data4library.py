"""운영 Phase 1 - 정보나루 인기대출 API 자동 수집.
과거 수동 다운로드 CSV(연령대별 4파일)와 같은 조건을 API로 재현한다.
  기간: 최근 12개월 (어제까지) / ISBN 부가기호: 아동(addCode=7) / 연령: 6~7, 8~9, 10~11, 12~13세 / 상위 1000건
산출: data/raw/data4library_api/{band}.json  (lib_corpus.load_all 이 CSV보다 우선해서 읽음)
안전: 4개 구간이 모두 성공했을 때만 저장한다. 하나라도 실패하거나 수량이 비정상이면 기존 파일을 유지하고 종료코드 2.
"""
import sys, json, time, datetime, urllib.request, urllib.parse, urllib.error
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from common import rp, write_json, load_env, TODAY

BANDS = {"pre": (6, 7), "low": (8, 9), "mid1": (10, 11), "mid2": (12, 13)}
MIN_ROWS = 300
API = "http://data4library.kr/api/loanItemSrch"
RETRY_DELAYS = (15, 30, 60)
TRANSIENT_HTTP = {408, 429, 500, 502, 503, 504}


def failure_info(ex):
    """요청 URL·키·서버 응답 본문을 포함하지 않는 오류 분류."""
    if isinstance(ex, urllib.error.HTTPError):
        return f"HTTP_{ex.code}", ex.code in TRANSIENT_HTTP
    # 일시적인 빈 응답·HTML·잘린 JSON도 기존 횟수/대기 한도 안에서만 재시도.
    # 유효한 JSON의 API 오류나 스키마 오류까지 재시도하지는 않는다.
    if isinstance(ex, json.JSONDecodeError):
        return "JSONDecodeError", True
    if isinstance(ex, (urllib.error.URLError, TimeoutError, ConnectionError)):
        return type(ex).__name__, True
    return type(ex).__name__, False


def fetch_band(key, frm, to, start, end):
    params = {"authKey": key, "startDt": start, "endDt": end, "from_age": frm, "to_age": to,
              "addCode": 7, "pageNo": 1, "pageSize": 1000, "format": "json"}
    url = API + "?" + urllib.parse.urlencode(params)
    attempts = len(RETRY_DELAYS) + 1
    for attempt in range(1, attempts + 1):
        started = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MAPZ/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read().decode("utf-8"))
            resp = data.get("response", {})
            if resp.get("error") or resp.get("errCode"):
                # 응답 본문에 키나 URL이 포함될 수 있으므로 그대로 로그에 남기지 않는다.
                raise RuntimeError("API response error")
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
            print(f"[data4library] age={frm}-{to} attempt={attempt}/{attempts} "
                  f"elapsed={time.monotonic() - started:.1f}s status=OK rows={len(rows)}",
                  file=sys.stderr, flush=True)
            return rows
        except Exception as ex:
            status, transient = failure_info(ex)
            delay = RETRY_DELAYS[attempt - 1] if transient and attempt < attempts else 0
            print(f"[data4library] age={frm}-{to} attempt={attempt}/{attempts} "
                  f"elapsed={time.monotonic() - started:.1f}s status={status} retry_in={delay}s",
                  file=sys.stderr, flush=True)
            if not delay:
                raise RuntimeError(f"{frm}~{to}세 수집 실패: {status} "
                                   f"(시도 {attempt}/{attempts})") from None
            time.sleep(delay)


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
