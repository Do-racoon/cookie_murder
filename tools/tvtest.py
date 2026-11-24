# -*- coding: utf-8 -*-
"""티비를 헤드리스 크롬으로 열어 검사한다.

    python3 tools/tvtest.py [열어 볼 파일]

기본은 tv/index.html (tools/build.py 가 만든 판). 검사마다 OK/FAIL 한 줄을 찍고,
FAIL 이 하나라도 있으면 종료코드 1 로 끝난다.
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tv" / "index.html"

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(ok)
    print(("OK   " if ok else "FAIL ") + name + (" — " + str(detail) if detail else ""))


def main():
    from playwright.sync_api import sync_playwright

    errors = []
    with sync_playwright() as p:
        b = p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            args=["--allow-file-access-from-files", "--no-sandbox"],
        )
        pg = b.new_page(viewport={"width": 1100, "height": 900})
        # 바깥 CDN(qrcode)은 이 컨테이너에서 못 받는다 — 스크립트 오류만 센다
        pg.on("console", lambda m: errors.append(m.text)
               if m.type == "error" and "Failed to load resource" not in m.text else None)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(TARGET.as_uri())
        pg.wait_for_timeout(900)

        check("콘솔 오류가 없다", not errors, errors[:3])
        ver = pg.evaluate("DEFAULT_DATA.version")
        check("DEFAULT_DATA.version 이 32 다", ver == 32, ver)

        e2 = pg.evaluate("(DEFAULT_DATA.endings.find(e=>e.id==='E2')||{}).code")
        check("엔딩 E2 코드가 쇼트브레드다", e2 == "쇼트브레드", e2)

        # 알림 띠가 본문 첫 줄을 덮지 않는다 — 화면 아래쪽에 있어야 한다
        box = pg.evaluate("""(()=>{ showTick('검사용 알림'); const t=document.getElementById('ticker');
            const sc=document.querySelector('.screen'); const b=document.getElementById('body');
            const r=t.getBoundingClientRect(), s=sc.getBoundingClientRect(), bb=b.getBoundingClientRect();
            return {hidden:t.hidden, tickTop:r.top, bodyTop:bb.top, scrTop:s.top, scrH:s.height}; })()""")
        check("알림 띠가 보인다", box["hidden"] is False, box)
        check(
            "알림 띠가 화면 아래쪽에 있다",
            box["tickTop"] > box["scrTop"] + box["scrH"] * 0.6,
            box,
        )

        b.close()

    print()
    bad = RESULTS.count(False)
    print(f"{len(RESULTS) - bad}/{len(RESULTS)} 통과")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
