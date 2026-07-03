"""운영 Phase 8 - 금지어 lint. 렌더 텍스트노드 대상, 12주제 페이지 전수."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from app.main import app, TOPICS
FORBIDDEN = ["등급","백분위","또래","비교해","필독","수준별","레벨테스트","지금 안 하면","늦기 전에","골든타임","선행","유형입니다"]
def vis(html):
    s=BeautifulSoup(html,"html.parser")
    for t in s(["script","style"]): t.decompose()
    return s.get_text(" ",strip=True)
def main():
    c=TestClient(app); pages=["/","/?q=우주","/map","/discover"]+[f"/topic/{t}" for t in TOPICS]
    hits=[]
    for p in pages:
        txt=vis(c.get(p).text)
        for w in FORBIDDEN:
            if w in txt: hits.append((p,w))
    from common import rp
    res=f"검사 {len(pages)}p / 위반 {len(hits)}건 {'LINT PASS' if not hits else 'LINT FAIL '+str(hits)}"
    open(rp("state","lint_result.txt"),"w",encoding="utf-8").write(res); print(res)
    return 0 if not hits else 1
if __name__=="__main__": sys.exit(main())
