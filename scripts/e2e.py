"""Phase 8 - Playwright E2E. 자체 uvicorn(포트 8011) 기동 -> 4화면 로드 + 클릭 흐름 + 콘솔에러 0.
콘솔 에러/페이지 예외를 수집. Leaflet 지도는 CDN 로드 실패 대비 폴백 존재(map.html)."""
import sys, os, subprocess, time, socket, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import p

PORT = 8011
BASE = f"http://127.0.0.1:{PORT}"

def wait_port(port, timeout=25):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close(); return True
        except OSError:
            time.sleep(0.4)
    return False

def main():
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORT), "--log-level", "error"],
        cwd=p(), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = {"pages": [], "console_errors": [], "page_errors": [], "flow": []}
    try:
        if not wait_port(PORT):
            raise RuntimeError("server did not start")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            ctx = b.new_context(viewport={"width": 390, "height": 844})
            pg = ctx.new_page()
            def on_console(msg):
                if msg.type == "error":
                    # 외부 타일/CDN 리소스 네트워크 실패는 별도 표시(하드 게이트에서 제외 판단용)
                    result["console_errors"].append(msg.text[:200])
            def on_pageerror(err):
                result["page_errors"].append(str(err)[:200])
            pg.on("console", on_console); pg.on("pageerror", on_pageerror)
            for path, name in [("/", "search"), ("/topic/dino", "topic"), ("/map", "map"), ("/discover", "discover")]:
                r = pg.goto(BASE + path, wait_until="load")
                result["pages"].append({"name": name, "status": r.status})
            # 클릭 흐름: 검색 -> 주제 타일 클릭 -> 주제관 -> 지도 탭 -> 발견 탭
            pg.goto(BASE + "/", wait_until="load")
            pg.click('.tile[data-topic="space"]'); pg.wait_for_load_state("load")
            result["flow"].append(("tile->topic", "space" in pg.url))
            pg.click('nav.tabs a[href="/map"]'); pg.wait_for_load_state("load")
            result["flow"].append(("nav->map", pg.url.endswith("/map")))
            pg.click('nav.tabs a[href="/discover"]'); pg.wait_for_load_state("load")
            result["flow"].append(("nav->discover", pg.url.endswith("/discover")))
            time.sleep(1.5)  # 지도 타일/스크립트 콘솔 관찰
            ctx.close(); b.close()
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except Exception: proc.kill()

    all_200 = all(x["status"] == 200 for x in result["pages"]) and len(result["pages"]) == 4
    flow_ok = all(ok for _, ok in result["flow"])
    # 외부(unpkg/openstreetmap tile) 네트워크 실패는 앱 결함 아님 -> 분리
    app_console_errs = [e for e in result["console_errors"]
                        if "unpkg" not in e and "openstreetmap" not in e and "tile" not in e.lower()
                        and "ERR_" not in e and "Failed to load resource" not in e]
    g8_e2e = all_200 and flow_ok and len(result["page_errors"]) == 0 and len(app_console_errs) == 0

    out = [f"pages: {result['pages']}", f"flow: {result['flow']}",
           f"page_errors(uncaught JS): {result['page_errors']}",
           f"console_errors(all): {result['console_errors']}",
           f"console_errors(app-only, 외부리소스 제외): {app_console_errs}",
           f"E2E {'PASS' if g8_e2e else 'FAIL'}"]
    text = "\n".join(out)
    open(p("state", "e2e_result.txt"), "w", encoding="utf-8").write(text)
    print(text)
    return 0 if g8_e2e else 1

if __name__ == "__main__":
    sys.exit(main())
