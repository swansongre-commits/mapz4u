"""운영 §6 - 제휴 콘솔 (Tier 3). 기관·지자체가 체험 정보를 직접 등록·갱신.
관리자 인증(HTTP Basic, 일반 사용자와 완전 분리) + 체험 CRUD + 상태 토글 + 최종수정일 자동 갱신.
실행: uvicorn admin.admin_app:admin --port 8090   (일반 앱과 별도 포트)
로그인: MAPZ_ADMIN_USER / MAPZ_ADMIN_PW (환경변수, 기본 admin/change-me)
"""
import os, sqlite3, secrets, datetime, json
from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "mapz_real.db")
ADMIN_USER = os.environ.get("MAPZ_ADMIN_USER", "admin")
ADMIN_PW = os.environ.get("MAPZ_ADMIN_PW", "change-me")
TODAY = os.environ.get("MAPZ_RUN_DATE", "2026-07-04")

admin = FastAPI(title="MAPZ 제휴 콘솔")
security = HTTPBasic()

def auth(cred: HTTPBasicCredentials = Depends(security)):
    ok = secrets.compare_digest(cred.username, ADMIN_USER) and secrets.compare_digest(cred.password, ADMIN_PW)
    if not ok:
        raise HTTPException(status_code=401, detail="인증 실패", headers={"WWW-Authenticate": "Basic"})
    return cred.username

def db():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; return con

def esc(s): return (str(s) if s is not None else "").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

PAGE = """<!doctype html><meta charset=utf-8><title>MAPZ 제휴 콘솔</title>
<style>body{{font-family:system-ui,'Malgun Gothic',sans-serif;max-width:1000px;margin:20px auto;padding:0 16px}}
table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{border:1px solid #ddd;padding:6px 8px;text-align:left}}
th{{background:#f4f4f4}}.op{{color:#2C6E63;font-weight:700}}.end{{color:#b00}}
input,select{{padding:5px}}.btn{{background:#2C6E63;color:#fff;border:0;padding:6px 12px;border-radius:6px;cursor:pointer}}
form.inline{{display:inline}}</style>
<h1>MAPZ 제휴 콘솔 <small>(Tier 3 · 관리자 전용)</small></h1>
<p>기관·지자체가 체험 정보를 직접 등록·갱신합니다. 저장 시 최종확인일이 오늘({today})로 갱신됩니다.</p>
{body}"""

@admin.get("/", response_class=HTMLResponse)
def home(user: str = Depends(auth)):
    con = db()
    rows = con.execute("SELECT id,name,type,status,region,last_verified,source FROM experience ORDER BY last_verified DESC LIMIT 100").fetchall()
    con.close()
    tr = ""
    for r in rows:
        st = f'<span class="op">{r["status"]}</span>' if r["status"] == "운영중" else f'<span class="end">{r["status"]}</span>'
        tr += f"""<tr><td>{esc(r['name'])}</td><td>{esc(r['type'])}</td><td>{st}</td><td>{esc(r['region'])}</td>
<td>{esc(r['last_verified'])}</td>
<td><form class=inline method=post action=/toggle><input type=hidden name=id value="{esc(r['id'])}">
<button class=btn>운영/종료 토글</button></form>
<form class=inline method=post action=/delete onsubmit="return confirm('삭제할까요?')"><input type=hidden name=id value="{esc(r['id'])}">
<button class=btn style="background:#b00">삭제</button></form></td></tr>"""
    body = f"""<h2>체험 항목 ({len(rows)}건, 최신순 100)</h2>
<table><tr><th>명칭</th><th>유형</th><th>상태</th><th>지역</th><th>최종확인</th><th>작업</th></tr>{tr}</table>
<h2>새 체험 등록</h2>
<form method=post action=/add>
명칭 <input name=name required> 유형 <select name=type><option>상설시설</option><option>행사</option></select>
주제 <input name=topic placeholder="예: history" required><br><br>
위도 <input name=lat required> 경도 <input name=lng required> 지역 <input name=region><br><br>
<button class=btn>등록</button></form>"""
    return PAGE.format(today=TODAY, body=body)

@admin.post("/toggle")
def toggle(user: str = Depends(auth), id: str = Form(...)):
    con = db()
    r = con.execute("SELECT status FROM experience WHERE id=?", (id,)).fetchone()
    if r:
        new = "종료" if r["status"] == "운영중" else "운영중"
        con.execute("UPDATE experience SET status=?, last_verified=? WHERE id=?", (new, TODAY, id))
        con.commit()
    con.close()
    return RedirectResponse("/", status_code=303)

@admin.post("/delete")
def delete(user: str = Depends(auth), id: str = Form(...)):
    con = db(); con.execute("DELETE FROM experience WHERE id=?", (id,)); con.commit(); con.close()
    return RedirectResponse("/", status_code=303)

@admin.post("/add")
def add(user: str = Depends(auth), name: str = Form(...), type: str = Form(...), topic: str = Form(...),
        lat: float = Form(...), lng: float = Form(...), region: str = Form("")):
    con = db()
    eid = "admin-" + secrets.token_hex(4)
    con.execute("""INSERT INTO experience
        (id,name,type,topic_tags,verb_tags,lat,lng,region,indoor,cost,source,is_seed,last_verified,status)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (eid, name, type, json.dumps([topic], ensure_ascii=False), "[]", lat, lng, region, 1,
         "현장 확인", "admin:제휴콘솔", 0, TODAY, "운영중"))
    con.commit(); con.close()
    return RedirectResponse("/", status_code=303)

@admin.get("/healthz")
def healthz(): return {"status": "ok", "role": "admin-console"}
