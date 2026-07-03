"""운영 Phase 8 - Playwright E2E. 자체 uvicorn(8021) + 4화면 + 클릭흐름 + 콘솔에러0."""
import sys, os, subprocess, time, socket
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import rp
PORT=8021; BASE=f"http://127.0.0.1:{PORT}"
def wait(p,t=25):
    s=time.time()
    while time.time()-s<t:
        try: socket.create_connection(("127.0.0.1",p),1).close(); return True
        except OSError: time.sleep(0.4)
    return False
def main():
    env=dict(os.environ,PYTHONIOENCODING="utf-8")
    proc=subprocess.Popen([sys.executable,"-m","uvicorn","app.main:app","--port",str(PORT),"--log-level","error"],
        cwd=rp(),env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    res={"pages":[],"console":[],"pageerr":[],"flow":[]}
    try:
        if not wait(PORT): raise RuntimeError("no server")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b=pw.chromium.launch(); ctx=b.new_context(viewport={"width":390,"height":844}); pg=ctx.new_page()
            pg.on("console",lambda m:res["console"].append(m.text[:150]) if m.type=="error" else None)
            pg.on("pageerror",lambda e:res["pageerr"].append(str(e)[:150]))
            tid=None
            for path,name in [("/","search"),("/map","map"),("/discover","discover")]:
                r=pg.goto(BASE+path,wait_until="load"); res["pages"].append((name,r.status))
            # 첫 주제 타일 클릭
            pg.goto(BASE+"/",wait_until="load")
            pg.click(".tile"); pg.wait_for_load_state("load")
            res["flow"].append(("tile->topic","/topic/" in pg.url))
            pg.click('nav.tabs a[href="/map"]'); pg.wait_for_load_state("load")
            res["flow"].append(("nav->map",pg.url.endswith("/map")))
            time.sleep(1.5); ctx.close(); b.close()
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except Exception: proc.kill()
    all200=all(s==200 for _,s in res["pages"]) and len(res["pages"])==3
    flow=all(ok for _,ok in res["flow"])
    appconsole=[e for e in res["console"] if "unpkg" not in e and "openstreetmap" not in e and "tile" not in e.lower() and "Failed to load resource" not in e and "ERR_" not in e]
    ok=all200 and flow and not res["pageerr"] and not appconsole
    out=f"pages={res['pages']} flow={res['flow']} pageerr={res['pageerr']} console_app={appconsole} E2E {'PASS' if ok else 'FAIL'}"
    open(rp("state","e2e_result.txt"),"w",encoding="utf-8").write(out); print(out)
    return 0 if ok else 1
if __name__=="__main__": sys.exit(main())
