"""MAPZ 운영버전 — Streamlit 앱 (mapz4u.streamlit.app 배포용).
FastAPI 앱(app/main.py)과 동일한 SQLite DB·실데이터·로직을 재사용. 화면만 Streamlit으로 재구성.
헌장 준수: 금지어 0, 인기순 없음(발견=쿼터), 신선도 필터, 연봉·전망 미노출, 1차 CTA=네이버지도.
"""
import os, json, sqlite3, datetime, urllib.parse
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "db", "mapz_real.db")
RUN_DATE = os.environ.get("MAPZ_RUN_DATE", "2026-07-04")
TODAY = RUN_DATE
PALETTE = ["#5B8C5A","#3A5BA0","#C77D3E","#5A5AA0","#B0507A","#2C8C8C","#8C6D3A","#7A4FA0",
           "#3E8C6B","#A0503E","#6B8C3A","#8C3A6B"]

st.set_page_config(page_title="맵즈 — 어린이 체험지도", page_icon="🗺️", layout="wide")

# ── DB 없으면 커밋된 clean 데이터로 재생성 (Streamlit Cloud 대비) ──
def ensure_db():
    if os.path.exists(DB):
        return
    import subprocess, sys
    for s in ("build_linkage.py", "build_db.py"):
        subprocess.run([sys.executable, os.path.join("scripts", s)], cwd=ROOT, check=False)
ensure_db()

def jl(s):
    try: return json.loads(s) if s else []
    except Exception: return []

@st.cache_data(show_spinner=False)
def load_topics():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM topic ORDER BY connection_score DESC").fetchall(); con.close()
    d = {}
    for i, r in enumerate(rows):
        d[r["id"]] = {"id": r["id"], "name": r["name"], "emoji": r["emoji"],
                      "synonyms": jl(r["synonyms"]), "color": PALETTE[i % len(PALETTE)]}
    return d

@st.cache_data(show_spinner=False)
def load_linkage():
    return json.load(open(os.path.join(ROOT, "data", "clean", "linkage.json"), encoding="utf-8"))

TOPICS = load_topics()
LINK = load_linkage()
FRESH = "status='운영중' AND (period_end IS NULL OR period_end='' OR period_end >= ?)"

# 내비 콜백 (위젯 인스턴스화 전에 실행되어 위젯 키 state 수정 허용)
def go_topic(tid):
    st.session_state["topic"] = tid
    st.session_state["view"] = "🏛️ 주제관"
def set_topic(tid):
    st.session_state["topic"] = tid

def q(sql, args=()):
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows = con.execute(sql, args).fetchall(); con.close(); return rows

def naver(name, region):
    s = (name or "").strip()
    if region and region not in s: s = f"{s} {region}"
    return "https://map.naver.com/p/search/" + urllib.parse.quote(s)

def exp_dict(r):
    return {"id": r["id"], "name": r["name"], "type": r["type"], "topic_tags": jl(r["topic_tags"]),
            "lat": r["lat"], "lng": r["lng"], "region": r["region"], "cost": r["cost"],
            "indoor": r["indoor"], "tel": r["tel"], "period_start": r["period_start"],
            "period_end": r["period_end"], "age_note": r["age_note"], "is_seed": r["is_seed"],
            "last_verified": r["last_verified"], "naver": naver(r["name"], r["region"])}

def badge(is_seed):
    return "🟡 표본(검증 필요)" if is_seed else "🟢 실데이터"

# ── CSS (지금 FastAPI 디자인에 최대한 근접) ──
st.markdown("""<style>
.block-container{max-width:1000px;padding-top:1.2rem}
.mapz-card{background:#fff;border:1px solid #E6E3DC;border-radius:14px;padding:14px 16px;margin-bottom:10px}
.mapz-hero{border-radius:20px;padding:22px;color:#fff;margin-bottom:8px}
.mapz-age{color:#8A9099;font-size:.82rem}
.mapz-meta{color:#5A6169;font-size:.9rem}
.mapz-note{background:#EAF3F1;border-radius:12px;padding:8px 12px;color:#1B5E55;font-size:.9rem}
div.stButton>button{border-radius:14px;min-height:44px;font-weight:600}
</style>""", unsafe_allow_html=True)

def exp_card(x):
    with st.container():
        st.markdown(f"""<div class="mapz-card">
<b>{x['name']}</b><br>
<span class="mapz-meta">📍 {x['region']} · 💰 {x['cost'] or '현장 확인'} · {'🏠 실내' if x['indoor'] else '🌳 야외'}{' · 📞 '+x['tel'] if x['tel'] else ''}</span><br>
{('<span class="mapz-meta">📅 '+str(x['period_start'])+' ~ '+str(x['period_end'])+'</span><br>') if x['period_start'] else ''}
<span class="mapz-age">권장 {x['age_note'] or '전연령'} (참고)</span> · <span class="mapz-age">최종 확인 {x['last_verified']}</span> · {badge(x['is_seed'])}
</div>""", unsafe_allow_html=True)
        st.link_button("🧭 네이버 지도 →", x["naver"])

def freshness_ok_ids(ids):
    if not ids: return []
    marks = ",".join("?" * len(ids))
    rows = q(f"SELECT * FROM experience WHERE id IN ({marks}) AND {FRESH}", (*ids, TODAY))
    return {r["id"]: exp_dict(r) for r in rows}

# ── 상단 네비 ──
st.markdown("## 🗺️ 맵즈 — 어린이 체험지도 <span style='font-size:.9rem;color:#8A9099'>· 운영</span>", unsafe_allow_html=True)
view = st.radio("화면", ["🔍 검색", "🏛️ 주제관", "🗺️ 지도", "✨ 발견"], horizontal=True,
                label_visibility="collapsed", key="view")

# ================= 검색 =================
if view == "🔍 검색":
    st.caption('아이가 좋아하는 걸 그대로 검색해 보세요. "공룡", "별", "곤충"처럼요.')
    query = st.text_input("검색", placeholder="무엇에 관심 있어요? (예: 우주, 그림, 곤충)", label_visibility="collapsed")
    c1, c2, c3, c4 = st.columns(4)
    f_indoor = c1.checkbox("🏠 실내"); f_free = c2.checkbox("💰 무료")
    f_week = c3.checkbox("📅 이번 주"); region = c4.text_input("📍 지역", placeholder="예: 서울", label_visibility="collapsed")

    st.caption(f"관심이 있으면 깊게 검색하고, 없으면 아래에서 골라 둘러봐요. (실수요로 뽑은 {len(TOPICS)}개 세계)")
    cols = st.columns(4)
    for i, (tid, t) in enumerate(TOPICS.items()):
        cols[i % 4].button(f"{t['emoji']} {t['name']}", key=f"tile_{tid}",
                           use_container_width=True, on_click=go_topic, args=(tid,))

    if query or f_indoor or f_free or region or f_week:
        rows = q(f"SELECT * FROM experience WHERE {FRESH}", (TODAY,))
        res = []
        mt = [tid for tid, t in TOPICS.items() if query and (query in t["name"] or any(s in query or query in s for s in t["synonyms"]))]
        for r in rows:
            x = exp_dict(r)
            if query and not (any(t in mt for t in x["topic_tags"]) or query in x["name"] or query in (x["region"] or "")): continue
            if f_indoor and not x["indoor"]: continue
            if f_free and not (("무료" in (x["cost"] or "")) or (x["cost"] or "") == ""): continue
            if region and region not in (x["region"] or ""): continue
            if f_week and not (x["type"] == "상설시설" or (x["period_start"] and x["period_start"] <= str((datetime.date.fromisoformat(TODAY)+datetime.timedelta(days=7))))): continue
            res.append(x)
        st.subheader(f"검색 결과 {len(res)}건")
        for x in res[:40]: exp_card(x)
        if not res: st.info("딱 맞는 곳이 없어요. 위 그림에서 둘러보는 건 어때요?")
    else:
        st.subheader("가까운 체험처 미리보기")
        for r in q(f"SELECT * FROM experience WHERE {FRESH} AND type='상설시설' LIMIT 6", (TODAY,)):
            exp_card(exp_dict(r))

# ================= 주제관 =================
elif view == "🏛️ 주제관":
    tid = st.session_state.get("topic", list(TOPICS)[0])
    tid = st.selectbox("주제 선택", list(TOPICS), index=list(TOPICS).index(tid),
                       format_func=lambda t: f"{TOPICS[t]['emoji']} {TOPICS[t]['name']}")
    st.session_state["topic"] = tid
    t = TOPICS[tid]; L = LINK["topics"].get(tid, {})
    st.markdown(f'<div class="mapz-hero" style="background:{t["color"]}"><div style="font-size:2.4rem">{t["emoji"]}</div>'
                f'<h2 style="margin:4px 0">{t["name"]} 세계</h2>전국의 {t["name"]} 체험처와 이야기를 모았어요.</div>', unsafe_allow_html=True)

    st.markdown("#### 옆으로 한 칸")
    st.caption("비슷한 다른 세계로 한 칸만 옮겨볼까요? (골라보는 건 아이 몫)")
    adj = LINK["adjacency"].get(tid, [])
    acs = st.columns(max(1, len(adj)))
    for i, a in enumerate(adj):
        acs[i].button(f"{TOPICS[a['topic']]['emoji']} {a['name']} 세계로",
                      key=f"adj_{a['topic']}", on_click=set_topic, args=(a["topic"],))

    st.markdown("#### 전국 상설·행사 체험처")
    fresh = freshness_ok_ids([e["id"] for e in L.get("experiences", [])])
    shown = [fresh[e["id"]] for e in L.get("experiences", []) if e["id"] in fresh]
    if shown:
        for x in shown: exp_card(x)
    else:
        st.info("지금 운영 중인 체험처를 준비 중이에요.")

    st.markdown("#### 더 깊이 — 이 세계를 더 볼 수 있는 책")
    st.caption("도서관에서 빌려 읽어요. 숙제가 아니라 이 세계를 더 볼 수 있는 책이에요. (전국 아이들이 실제로 많이 빌린 책)")
    for b in L.get("books", []):
        br = q("SELECT * FROM book WHERE isbn=?", (b["isbn"],))
        if not br: continue
        bk = br[0]
        with st.container():
            loan = f" · 전국 대출 {bk['loan_count']:,}회" if bk["loan_count"] else ""
            st.markdown(f'<div class="mapz-card">📖 <b>{bk["title"]}</b><br>'
                        f'<span class="mapz-meta">{bk["author"]} · {bk["publisher"]} · 권장 {bk["age_band"]}세(참고){loan}</span><br>'
                        f'<span class="mapz-age">최종 확인 {bk["last_verified"]}</span> · {badge(bk["is_seed"])}</div>', unsafe_allow_html=True)
            st.link_button("🏫 도서관 소장 조회 →", "https://www.nl.go.kr/NL/contents/search.do?srchTarget=total&kwd=" + urllib.parse.quote(bk["title"]))

    st.markdown("#### 이 세계의 어른들")
    if L.get("person"):
        pr = q("SELECT * FROM person WHERE id=?", (L["person"]["id"],))
        if pr:
            p = pr[0]
            anti = " 🏷️반고정관념" if p["anti_stereotype"] else ""
            st.markdown(f'<div class="mapz-card" style="border-left:5px solid {t["color"]}">'
                        f'<b style="font-size:1.1rem">{p["name"]}{anti}</b> <span class="mapz-age">· {p["era"]}</span><br>'
                        f'<span class="mapz-meta">{p["story_trial"]}</span><br><br>'
                        f'<b>하는 일:</b> {p["verb_desc"]}<br>'
                        f'<span class="mapz-age">이 이야기에서 뻗어나가는 일들: {" · ".join(jl(p["job_lineage"]))}</span></div>', unsafe_allow_html=True)

    # 직업: 눌러서 상세 (popover)
    st.markdown("#### 이 세계와 이어진 일들")
    st.caption("궁금한 걸 눌러보면 무슨 일을 하는지 알려줘요. (연봉·전망 같은 건 보여주지 않아요)")
    jobs = q("SELECT * FROM job WHERE topic_tags LIKE ?", (f'%\"{tid}\"%',))
    jcols = st.columns(3)
    for i, jrow in enumerate(jobs[:6]):
        with jcols[i % 3].popover(f"{jrow['emoji']} {jrow['name']}", use_container_width=True):
            st.markdown(f"### {jrow['emoji']} {jrow['name']}")
            st.write(jrow["verb_desc"])
            places = q(f"SELECT * FROM experience WHERE {FRESH} AND type='상설시설' AND topic_tags LIKE ? LIMIT 3", (TODAY, f'%\"{tid}\"%'))
            if places:
                st.markdown("**이런 데서 볼 수 있어요**")
                for pl in places:
                    st.link_button(f"📍 {pl['name']} ({pl['region']})", naver(pl["name"], pl["region"]))
            if L.get("person"):
                pr = q("SELECT name, verb_desc FROM person WHERE id=?", (L["person"]["id"],))
                if pr: st.markdown(f"**이 세계의 어른** · {pr[0]['name']} — {pr[0]['verb_desc']}")
            st.caption("직업 이름보다 '하는 일(동사)'로 만나요. 연봉·전망 같은 건 보여주지 않아요.")

# ================= 지도 =================
elif view == "🗺️ 지도":
    import folium
    from streamlit_folium import st_folium
    st.markdown("#### 지도 둘러보기")
    st.caption("운영 중인 곳만 표시해요. 지난 행사는 지도에 나오지 않아요(신선도).")
    picks = st.multiselect("주제 필터", list(TOPICS), default=list(TOPICS),
                           format_func=lambda t: f"{TOPICS[t]['emoji']} {TOPICS[t]['name']}")
    rows = q(f"SELECT * FROM experience WHERE {FRESH}", (TODAY,))
    m = folium.Map(location=[36.5, 127.8], zoom_start=7, tiles="OpenStreetMap")
    n = 0
    for r in rows:
        tags = jl(r["topic_tags"])
        if not any(tt in picks for tt in tags): continue
        color = TOPICS.get(tags[0], {}).get("color", "#2C6E63") if tags else "#2C6E63"
        nav = naver(r["name"], r["region"])
        folium.CircleMarker([r["lat"], r["lng"]], radius=5, color=color, fill=True, fill_opacity=0.8,
            popup=folium.Popup(f'<b>{r["name"]}</b><br>{r["region"] or ""}<br><a href="{nav}" target="_blank">네이버 지도 →</a>', max_width=250)).add_to(m)
        n += 1
    st.caption(f"전국 {n}곳 표시 중")
    st_folium(m, use_container_width=True, height=520, returned_objects=[])

# ================= 발견 =================
elif view == "✨ 발견":
    st.markdown("#### 발견 피드")
    st.markdown('<div class="mapz-note">🔀 인기순으로 줄 세우지 않아요. 가까운 세계 하나, 안 가본 먼 세계 하나, 그리고 한 사람의 이야기를 골고루 섞어요.</div>', unsafe_allow_html=True)
    dq = LINK["discover_quota"]
    for key, label in [("near", "가까운 세계"), ("far", "안 가본 먼 세계")]:
        blk = dq[key]
        st.markdown(f"#### {label} — {TOPICS[blk['topic']]['emoji']} {blk['name']}")
        se = blk.get("sample_exp")
        fresh = freshness_ok_ids([se["id"]]) if se else {}
        if se and se["id"] in fresh: exp_card(fresh[se["id"]])
        else: st.info("운영 중 항목 준비 중이에요.")
    st.markdown("#### 한 사람의 이야기")
    pr = q("SELECT * FROM person WHERE id=?", (dq["anti_stereotype_person"]["id"],))
    if pr:
        p = pr[0]
        anti = " 🏷️반고정관념" if p["anti_stereotype"] else ""
        st.markdown(f'<div class="mapz-card"><b>{p["name"]}{anti}</b><br><span class="mapz-meta">{p["story_trial"]}</span><br><br><b>하는 일:</b> {p["verb_desc"]}</div>', unsafe_allow_html=True)
    st.caption("여기까지가 오늘의 발견이에요. (끝이 있는 화면)")

# ── 출처 footer (§7) ──
st.divider()
st.caption("맵즈 — 어린이 체험지도(운영) · 공영 중립 · 도서관 대출 우선 | "
           "출처: 체험·행사=한국관광공사 국문관광정보(TourAPI, 공공누리1) · 도서=국립중앙도서관 정보나루 인기대출(BY) · 지도=OpenStreetMap")
