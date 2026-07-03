"""Phase 6 - 4개 화면 정적 HTML 시안 생성 (design/draft_round1/).
실제 linkage/clean 데이터를 임베드해 디자인 리뷰가 실 콘텐츠를 보게 함.
헌장 10항 체크리스트 충족: 그림타일 우선, 44px, 시드배지, 최종확인일, 소장/대출 표기, 현실전환 CTA, 인기순 금지.
"""
import sys, json, shutil, html
sys.path.insert(0, ".")
from common import p, read_json, TOPICS, TOPIC_IDS, TODAY

link=read_json(p("data","clean","linkage.json"),{})
exp=read_json(p("data","clean","experiences.json"),[])
books=read_json(p("data","clean","books.json"),[])
people=read_json(p("data","clean","people.json"),[])
jobs=read_json(p("data","clean","jobs.json"),[])
EXP={x["id"]:x for x in exp}; BOOK={b["isbn"]:b for b in books}
PERSON={pe["id"]:pe for pe in people}; JOB={j["id"]:j for j in jobs}
TODAY_ISO=TODAY.isoformat()
def esc(s): return html.escape(str(s))

HEAD="""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>맵즈 — {t}</title><link rel="stylesheet" href="style.css"></head><body>
<header class="site"><div class="wrap">
<a class="brand" href="search.html">맵즈<small>어린이 체험지도</small></a>
<nav class="tabs">
<a href="search.html"{a0}>🔍 검색</a>
<a href="topic.html"{a1}>🏛️ 주제관</a>
<a href="map.html"{a2}>🗺️ 지도</a>
<a href="discover.html"{a3}>✨ 발견</a>
</nav></div></header><main class="wrap">"""
FOOT="""</main><footer class="site">맵즈 — 어린이 체험지도 · 공영 중립 · 표본(검증 필요) 데이터 포함<br>
최종 확인일 표기와 시드 배지로 정보의 신선도를 정직하게 알려요.</footer></body></html>"""

def head(title, active):
    a=["","","",""]; a[active]=' aria-current="page"'
    return HEAD.format(t=title,a0=a[0],a1=a[1],a2=a[2],a3=a[3])

def seed_badge(is_seed):
    return '<span class="badge-seed">표본(검증 필요)</span>' if is_seed else '<span class="badge-live">실데이터</span>'

def exp_card(x):
    age=f'<span class="age">권장 {esc(x.get("age_note","전연령"))} (참고)</span>'
    cost=esc(x.get("cost","")) or "현장 확인"
    resv= '예약 필요' if x.get('reservation_url') else '자유 관람'
    maplink=f'https://www.openstreetmap.org/?mlat={x["lat"]}&mlon={x["lng"]}#map=17/{x["lat"]}/{x["lng"]}'
    return f"""<article class="card">
<h3>{esc(x['name'])}</h3>
<div class="meta"><span>📍 {esc(x.get('region',''))}</span><span>💰 {cost}</span>
<span>{'🏠 실내' if x.get('indoor') else '🌳 야외'}</span><span>🕒 {esc(x.get('hours','') or '운영시간 확인')}</span></div>
<div class="meta"><span>{esc(resv)}</span>{age}</div>
<div class="meta"><span class="verified">최종 확인 {esc(x.get('last_verified',TODAY_ISO))}</span> {seed_badge(x.get('is_seed'))}</div>
<div class="cta-row"><a class="btn" href="{maplink}" target="_blank" rel="noopener">길찾기 →</a>
<a class="btn ghost" href="topic.html">주제 더보기</a></div></article>"""

def book_card(b):
    return f"""<article class="card"><div class="book-row"><h3>📖 {esc(b['title'])}</h3>
<div class="meta"><span>{esc(b.get('author',''))}</span><span>{esc(b.get('publisher',''))}</span>
<span class="age">권장 {esc(b.get('age_band',''))}세 (참고)</span></div>
<div class="avail">🏫 소장 도서관·대출 가능 여부 조회 →</div>
<div class="meta"><span class="verified">최종 확인 {esc(b.get('last_verified',TODAY_ISO))}</span> {seed_badge(b.get('is_seed'))}</div>
<div class="cta-row"><a class="btn ghost" href="#">도서관 소장 조회</a></div></div></article>"""

# ── 1) 검색 화면 ──
def page_search():
    out=[head("검색",0)]
    out.append('<p class="hint">아이가 좋아하는 걸 그대로 검색해 보세요. "쥬라기", "별", "곤충"처럼요.</p>')
    out.append("""<form class="searchbar" onsubmit="return false">
<input type="search" placeholder="무엇에 관심 있어요? (예: 쥬라기, 로봇, 나비)" aria-label="검색어">
<button class="btn" type="submit">찾기</button></form>""")
    out.append('<div class="chips" role="group" aria-label="부모 필터">')
    for label in ["🏠 실내","💰 무료","📍 우리 지역","📅 이번 주"]:
        out.append(f'<button class="chip" aria-pressed="false">{label}</button>')
    out.append('</div>')
    out.append('<p class="section-note">관심이 있으면 깊게 검색하고, 없으면 아래 그림에서 골라 둘러봐요.</p>')
    out.append('<div class="tiles">')
    for tid in TOPIC_IDS:
        t=TOPICS[tid]
        out.append(f'<a class="tile" data-topic="{tid}" href="topic.html"><span class="emoji">{t["emoji"]}</span><span class="label">{t["name"]}</span></a>')
    out.append('</div>')
    out.append('<h2 class="section-title">검색 결과 미리보기</h2>')
    out.append('<div class="cards">')
    live=[x for x in exp if x['status']=='운영중' and (not x.get('period_end') or x['period_end']>=TODAY_ISO)]
    for x in live[:4]: out.append(exp_card(x))
    out.append('</div>')
    out.append(FOOT); return "".join(out)

# ── 2) 주제관 (공룡) ──
def page_topic():
    tid="dino"; T=link["topics"][tid]; t=TOPICS[tid]
    out=[head("주제관",1)]
    out.append(f'<div class="hero" style="background:var(--t-{tid})"><div style="font-size:2.6rem">{t["emoji"]}</div>'
               f'<h1 style="margin:6px 0">{t["name"]} 세계</h1><p style="margin:0;opacity:.95">전국의 {t["name"]} 체험처와 이야기를 모았어요.</p></div>')
    # 옆으로 한 칸
    out.append('<h2 class="section-title">옆으로 한 칸</h2>')
    out.append('<p class="section-note">비슷한 다른 세계로 한 칸만 옮겨볼까요? (골라보는 건 아이 몫)</p><div class="sidestep">')
    for a in link["adjacency"][tid]:
        out.append(f'<a href="topic.html">{TOPICS[a["topic"]]["emoji"]} {esc(a["name"])} 세계로</a>')
    out.append('</div>')
    # 상설 체험
    out.append('<h2 class="section-title">전국 상설 체험처</h2><div class="cards">')
    for e in T["experiences"]:
        if e["id"] in EXP: out.append(exp_card(EXP[e["id"]]))
    out.append('</div>')
    # 더 깊이 도서
    out.append('<h2 class="section-title">더 깊이 — 이 세계를 더 볼 수 있는 책</h2>')
    out.append('<p class="section-note">도서관에서 빌려 읽어요. 숙제가 아니라 이 세계를 더 볼 수 있는 책이에요.</p><div class="cards">')
    for b in T["books"]:
        if b["isbn"] in BOOK: out.append(book_card(BOOK[b["isbn"]]))
    out.append('</div>')
    # 이 세계의 어른들 (Layer B 인물 + 직업 계보)
    out.append('<h2 class="section-title">이 세계의 어른들</h2>')
    pe=PERSON.get(T["person"]["id"]) if T["person"] else None
    if pe:
        anti='<span class="anti">반고정관념</span>' if pe.get("anti_stereotype") else ''
        lin="".join(f"<span>{esc(n)}</span>" for n in pe.get("job_lineage",[]))
        out.append(f"""<div class="person"><div class="who">{esc(pe['name'])} {anti}<span class="age"> · {esc(pe.get('era',''))}</span></div>
<p class="trial">{esc(pe.get('story_trial',''))}</p>
<p style="margin:6px 0"><b>하는 일:</b> {esc(pe.get('verb_desc',''))}</p>
<p style="margin:6px 0 4px" class="hint">이 이야기에서 뻗어나가는 일들 (하나가 여럿으로):</p>
<div class="lineage">{lin}</div></div>""")
    out.append(FOOT); return "".join(out)

# ── 3) 지도 ──
def page_map():
    out=[head("지도",2)]
    out.append('<h1 class="section-title">지도 둘러보기</h1>')
    out.append('<p class="section-note">운영 중인 곳만 표시해요. 지난 행사는 지도에 나오지 않아요(신선도).</p>')
    out.append('<div class="map-legend chips">')
    for tid in TOPIC_IDS:
        out.append(f'<button class="chip" aria-pressed="true">{TOPICS[tid]["emoji"]} {TOPICS[tid]["name"]}</button>')
    out.append('</div>')
    out.append('<div id="map" role="img" aria-label="체험처 지도 (정적 시안 - 실제 화면은 Leaflet)">'
               '<div style="padding:20px;color:var(--ink-soft)">🗺️ Leaflet + OpenStreetMap 지도 영역<br>'
               '(마커: 운영중 체험처만 · 팝업에 명칭·좌표·길찾기)</div></div>')
    out.append('<h2 class="section-title">이번 주말·실내·무료</h2><div class="cards">')
    live=[x for x in exp if x['status']=='운영중' and x['type']=='상설시설' and x.get('indoor')]
    for x in live[:3]: out.append(exp_card(x))
    out.append('</div>')
    out.append(FOOT); return "".join(out)

# ── 4) 발견 피드 ──
def page_discover():
    dq=link["discover_quota"]; out=[head("발견",3)]
    out.append('<h1 class="section-title">발견 피드</h1>')
    out.append('<div class="discover-note">🔀 인기순으로 줄 세우지 않아요. 가까운 세계 하나, 안 가본 먼 세계 하나, 그리고 한 사람의 이야기를 골고루 섞어요.</div>')
    out.append('<div style="margin:12px 0"><button class="btn ghost">🔀 다른 것 섞어보기</button></div>')
    # 인접 1
    out.append(f'<h2 class="section-title">가까운 세계 — {esc(dq["near"]["name"])}</h2><div class="cards">')
    if dq["near"]["sample_exp"] and dq["near"]["sample_exp"]["id"] in EXP:
        out.append(exp_card(EXP[dq["near"]["sample_exp"]["id"]]))
    out.append('</div>')
    # 먼 주제 1
    out.append(f'<h2 class="section-title">안 가본 먼 세계 — {esc(dq["far"]["name"])}</h2><div class="cards">')
    if dq["far"]["sample_exp"] and dq["far"]["sample_exp"]["id"] in EXP:
        out.append(exp_card(EXP[dq["far"]["sample_exp"]["id"]]))
    out.append('</div>')
    # 반고정관념 인물
    pe=PERSON.get(dq["anti_stereotype_person"]["id"])
    if pe:
        out.append('<h2 class="section-title">한 사람의 이야기</h2>')
        out.append(f'<div class="person"><div class="who">{esc(pe["name"])} <span class="anti">반고정관념</span></div>'
                   f'<p class="trial">{esc(pe.get("story_trial",""))}</p></div>')
    out.append(FOOT); return "".join(out)

def main():
    d=p("design","draft_round1")
    shutil.copy(p("app","static","style.css"), p("design","draft_round1","style.css"))
    files={"search.html":page_search(),"topic.html":page_topic(),"map.html":page_map(),"discover.html":page_discover()}
    for name,content in files.items():
        open(p("design","draft_round1",name),"w",encoding="utf-8").write(content)
    print("시안 4종 생성:", list(files.keys()))

if __name__=="__main__":
    main()
