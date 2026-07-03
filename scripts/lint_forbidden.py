"""Phase 8 - 금지어 lint. 렌더링된 HTML의 '텍스트 노드'만 대상(script/style 제외).
금지어 0건 게이트. '권장 연령' 표기는 허용 예외.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from app.main import app, TOPICS

FORBIDDEN = ["등급","백분위","또래","비교해","필독","수준별","레벨테스트",
             "지금 안 하면","늦기 전에","골든타임","선행","유형입니다"]

def visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)

def main():
    client = TestClient(app)
    pages = ["/", "/?q=쥬라기", "/map", "/discover"] + [f"/topic/{t}" for t in TOPICS]
    hits = []
    for path in pages:
        r = client.get(path)
        text = visible_text(r.text)
        for w in FORBIDDEN:
            if w in text:
                # 위치 컨텍스트
                idx = text.find(w)
                ctx = text[max(0,idx-20):idx+20]
                hits.append((path, w, ctx))
    from common import p
    lines = [f"검사 페이지: {len(pages)}개", f"금지어 목록: {FORBIDDEN}"]
    if hits:
        lines.append(f"위반 {len(hits)}건:")
        for h in hits: lines.append(f"  {h[0]} | '{h[1]}' | …{h[2]}…")
        lines.append("LINT FAIL")
    else:
        lines.append("위반 0건")
        lines.append("LINT PASS")
    out = "\n".join(lines)
    open(p("state","lint_result.txt"),"w",encoding="utf-8").write(out)
    print(out)
    return 0 if not hits else 1

if __name__ == "__main__":
    sys.exit(main())
