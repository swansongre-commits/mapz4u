"""운영 트랙 - TourAPI(한국관광공사 국문관광정보 KorService2) 실데이터 수집.
승인된 DATA_GO_KR_KEY 사용. 주제 무관하게 원본 전량 수집 -> real/data/raw/tourapi_*.json.
- 문화시설(contentTypeId=14): 박물관·미술관·과학관·기념관 등 = 상설 체험
- 축제공연행사(contentTypeId=15): 축제 = 행사(기간 포함)
KorService1은 폐기(500) -> KorService2 사용.
"""
import sys, json, time, urllib.request, urllib.parse
sys.path.insert(0, ".")
from common import rp, write_json, load_env, in_kr, TODAY

env = load_env()
KEY = urllib.parse.quote(env.get("DATA_GO_KR_KEY", ""))
BASE = "http://apis.data.go.kr/B551011/KorService2"
COMMON = f"serviceKey={KEY}&MobileOS=ETC&MobileApp=MAPZ&_type=json"

def _get(op, extra, timeout=25):
    url = f"{BASE}/{op}?{COMMON}&{extra}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MAPZ/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            hdr = data.get("response", {}).get("header", {})
            if hdr.get("resultCode") not in ("0000", "00"):
                return None, hdr.get("resultMsg", "err")
            body = data.get("response", {}).get("body", {})
            items = body.get("items")
            if not items:
                return [], "empty"
            it = items.get("item", [])
            if isinstance(it, dict): it = [it]
            return it, body.get("totalCount", len(it))
        except Exception as ex:
            if attempt == 2:
                return None, str(ex)[:100]
            time.sleep(1.5)
    return None, "fail"

def fetch_paged(op, extra, max_pages=25, rows=100):
    out = []
    for pg in range(1, max_pages + 1):
        items, total = _get(op, f"{extra}&numOfRows={rows}&pageNo={pg}")
        if items is None:
            print(f"  [{op}] p{pg} 오류: {total}"); break
        if not items:
            break
        out.extend(items)
        try:
            if len(out) >= int(total): break
        except (TypeError, ValueError):
            pass
        time.sleep(0.3)
    return out

def norm_facility(it):
    lat, lng = it.get("mapy"), it.get("mapx")  # TourAPI: mapy=위도, mapx=경도
    if not in_kr(lat, lng):
        return None
    return {"contentid": it.get("contentid"), "name": (it.get("title") or "").strip(),
            "addr": (it.get("addr1") or "").strip(), "lat": float(lat), "lng": float(lng),
            "tel": it.get("tel", ""), "homepage": "", "image": it.get("firstimage", ""),
            "cat": it.get("cat3", ""), "areacode": it.get("areacode", ""),
            "contenttypeid": it.get("contenttypeid", "")}

def norm_festival(it):
    lat, lng = it.get("mapy"), it.get("mapx")
    return {"contentid": it.get("contentid"), "name": (it.get("title") or "").strip(),
            "addr": (it.get("addr1") or "").strip(),
            "lat": float(lat) if in_kr(lat, lng) else None,
            "lng": float(lng) if in_kr(lat, lng) else None,
            "eventstartdate": it.get("eventstartdate", ""), "eventenddate": it.get("eventenddate", ""),
            "tel": it.get("tel", ""), "image": it.get("firstimage", ""),
            "contenttypeid": it.get("contenttypeid", "")}

def main():
    if not env.get("DATA_GO_KR_KEY"):
        print("DATA_GO_KR_KEY 없음"); return
    print("=== TourAPI KorService2 실데이터 수집 ===")
    # 1) 문화시설 전국 (contentTypeId=14)
    fac_raw = fetch_paged("areaBasedList2", "contentTypeId=14&arrange=C", max_pages=30, rows=100)
    facilities = [f for f in (norm_facility(x) for x in fac_raw) if f]
    print(f"문화시설(14): 원본 {len(fac_raw)} -> 좌표유효 {len(facilities)}건")
    write_json(rp("data", "raw", "tourapi_facilities.json"), facilities)
    # 2) 축제 (contentTypeId=15), 실행일 이후 시작/진행 (신선도)
    start = TODAY.strftime("%Y%m%d")
    fes_raw = fetch_paged("searchFestival2", f"eventStartDate=20260101&arrange=C", max_pages=30, rows=100)
    festivals = [norm_festival(x) for x in fes_raw]
    # 진행/예정만 (종료일 >= 오늘) — 신선도
    today = TODAY.strftime("%Y%m%d")
    live_fes = [f for f in festivals if (f["eventenddate"] or "99999999") >= today]
    print(f"축제(15): 원본 {len(fes_raw)} -> 진행/예정 {len(live_fes)}건 (종료 {len(festivals)-len(live_fes)} 제외)")
    write_json(rp("data", "raw", "tourapi_festivals.json"), live_fes)
    open(rp("state", "tourapi_result.txt"), "w", encoding="utf-8").write(
        f"facilities={len(facilities)} festivals_live={len(live_fes)}")
    print("저장: real/data/raw/tourapi_facilities.json, tourapi_festivals.json")

if __name__ == "__main__":
    main()
