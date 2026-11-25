# -*- coding: utf-8 -*-
"""문서 모음(docs/index.html)을 헤드리스 크롬으로 열어 검사한다.

    python3 tools/docstest.py
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "docs" / "index.html"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(ok)
    print(("OK   " if ok else "FAIL ") + name + (" — " + str(detail) if detail else ""))


def main():
    from playwright.sync_api import sync_playwright
    tk = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
    src = TARGET.read_text(encoding="utf-8")
    errors = []

    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome",
                              args=["--allow-file-access-from-files", "--no-sandbox"])
        pg = b.new_page(viewport={"width": 1100, "height": 820})
        pg.on("console", lambda m: errors.append(m.text)
              if m.type == "error" and "Failed to load resource" not in m.text else None)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(TARGET.as_uri())
        pg.wait_for_timeout(900)

        got = pg.evaluate("""(()=>{const b=getComputedStyle(document.body);
            const t=document.querySelector('.tabs button[aria-selected=true]');
            const h=document.querySelector('h2');
            return {bg:b.backgroundColor, color:b.color, font:b.fontFamily,
                    size:b.fontSize, lh:b.lineHeight,
                    tab:t?getComputedStyle(t).color:null,
                    rule:h?getComputedStyle(h).borderBottomColor:null};})()""")

        def rgb(hex_):
            h = hex_.lstrip("#")
            return "rgb(%d, %d, %d)" % tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        check("바탕이 방 색이다", got["bg"] == rgb(tk["color"]["bg"]), got["bg"])
        check("글자가 인광색이다", got["color"] == rgb(tk["color"]["phos"]), got["color"])
        check("본문 글꼴이 고운바탕이다", "Gowun Batang" in got["font"], got["font"])
        check("본문이 17px 이다", got["size"] == "17px", got["size"])
        check("고른 탭이 호박색이다", got["tab"] == rgb(tk["color"]["amber"]), got["tab"])
        check("콘솔 오류가 없다", not errors, errors[:3])
        b.close()

    check("옛 다크모드 분기가 없다", "prefers-color-scheme" not in src)
    check("인쇄용 스타일이 있다", "@media print" in src)
    check("구성이 카드 30장이다", "카드 30장" in src and "카드 22장" not in src and "카드 31장" not in src)
    check("엔딩이 아홉이다", "엔딩은 아홉" in src and "엔딩은 다섯" not in src)

    print()
    bad = RESULTS.count(False)
    print("%d/%d 통과" % (len(RESULTS) - bad, len(RESULTS)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
