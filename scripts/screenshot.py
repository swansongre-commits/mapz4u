"""Phase 6 - Playwright 스크린샷 (모바일 390 + 데스크톱 1280) -> design/screenshots/."""
import sys, os
sys.path.insert(0, ".")
from common import p
pages=["search","topic","map","discover"]
out=[]
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b=pw.chromium.launch()
        for vp,w,h in [("m",390,844),("d",1280,900)]:
            ctx=b.new_context(viewport={"width":w,"height":h})
            pg=ctx.new_page()
            for name in pages:
                fp="file:///"+p("design","draft_round1",name+".html").replace("\\","/")
                pg.goto(fp,wait_until="load")
                dst=p("design","screenshots",f"{name}_{vp}.png")
                pg.screenshot(path=dst,full_page=True)
                out.append(f"OK {name}_{vp}.png")
            ctx.close()
        b.close()
    open(p("state","screenshot_out.txt"),"w",encoding="utf-8").write("SCREENSHOTS_OK\n"+"\n".join(out))
    print("SCREENSHOTS_OK", len(out))
except Exception as ex:
    open(p("state","screenshot_out.txt"),"w",encoding="utf-8").write(f"SCREENSHOT_SKIP {ex}")
    print("SCREENSHOT_SKIP", str(ex)[:200])
