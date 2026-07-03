"""정보나루 인기대출 CSV 파서 (연령대별). 실데이터 수요 코퍼스 + 도서 노드 원천.
CSV 구조: 메타행 여러 개 후 '순위,서명,저자,출판사,출판년도,권,ISBN,ISBN부가기호,KDC,대출건수' 헤더.
"""
import os, csv, io, re

AGE_FILES = {
    "pre": "loan_age_6_7.csv",     # 유아 6~7
    "low": "loan_age_8_9.csv",     # 1,2학년 8~9
    "mid1": "loan_age_10_11.csv",  # 3,4학년 10~11
    "mid2": "loan_age_12_13.csv",  # 5,6학년 12~13
}

def _read_text(path):
    raw = open(path, "rb").read()
    for e in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            return raw.decode(e)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")

def parse_file(path):
    txt = _read_text(path)
    lines = txt.splitlines()
    # 데이터 헤더 행 찾기
    hidx = None
    for i, l in enumerate(lines):
        if l.startswith("순위,") and "서명" in l:
            hidx = i; break
    if hidx is None:
        return []
    reader = csv.reader(io.StringIO("\n".join(lines[hidx:])))
    header = next(reader)
    col = {name: idx for idx, name in enumerate(header)}
    rows = []
    for r in reader:
        if not r or len(r) < 8:
            continue
        def g(name):
            i = col.get(name)
            return r[i].strip() if i is not None and i < len(r) else ""
        loan = g("대출건수").replace(",", "")
        try:
            loan = int(loan)
        except ValueError:
            loan = 0
        title = g("서명")
        if not title:
            continue
        rows.append({
            "rank": g("순위"), "title": title, "author": g("저자"),
            "publisher": g("출판사"), "pub_year": g("출판년도"),
            "isbn": g("ISBN"), "isbn_add": g("ISBN부가기호"),
            "kdc": g("KDC"), "loan": loan})
    return rows

def load_all(folder):
    """{band: [rows]} 반환."""
    out = {}
    for band, fname in AGE_FILES.items():
        fp = os.path.join(folder, fname)
        out[band] = parse_file(fp) if os.path.exists(fp) else []
    return out
