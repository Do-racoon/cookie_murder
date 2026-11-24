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
        chrome = pathlib.Path("/usr/bin/google-chrome")
        b = p.chromium.launch(
            # 크롬이 없는 컨테이너에서는 Playwright 에 딸린 chromium 을 쓴다
            **({"executable_path": str(chrome)} if chrome.exists() else {}),
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
        check("DEFAULT_DATA.version 이 34 다", ver == 34, ver)

        e2 = pg.evaluate("(DEFAULT_DATA.endings.find(e=>e.id==='E2')||{}).code")
        check("엔딩 E2 코드가 쇼트브레드다", e2 == "쇼트브레드", e2)

        ends = pg.evaluate("DEFAULT_DATA.endings")
        check(
            "엔딩이 아홉 장이고 id 가 E1~E9 다",
            [e["id"] for e in ends] == ["E%d" % i for i in range(1, 10)],
            [e["id"] for e in ends],
        )
        codes = [e.get("code") for e in ends]
        check("엔딩 쿠키 이름이 아홉 개 다 다르다", len(set(codes)) == 9, codes)

        keys = pg.evaluate("VQ.map(q=>q.k)")
        check("판결 질문이 기소·자수서 둘이다", keys == ["charge", "confess"], keys)

        grid = pg.evaluate(
            """(()=>{const o={};for(const c of ["all","split","her"])
               for(const f of ["S1","S2","none"])
                 o[c+"/"+f]=verdictPick({charge:c,confess:f}).join(",");
               return o;})()"""
        )
        check("3×3 아홉 칸이 서로 다른 엔딩 하나씩이다",
              sorted(grid.values()) == ["E%d" % i for i in range(1, 10)], grid)
        check("S1×전부묶기는 E1 이다", grid.get("all/S1") == "E1", grid.get("all/S1"))
        check("못냄×가르기는 E4 다", grid.get("split/none") == "E4", grid.get("split/none"))

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

        # 티비의 색과 design/tokens.json 이 어긋나지 않는다
        import json as _json
        tk = _json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
        css = pg.evaluate(
            "(()=>{const s=getComputedStyle(document.documentElement);const o={};"
            "for(const v of %s) o[v]=s.getPropertyValue(v).trim(); return o;})()"
            % _json.dumps(list(tk["fromTv"].values()))
        )
        drift = {
            name: (tk["color"][name], css.get(var))
            for name, var in tk["fromTv"].items()
            if css.get(var, "").lower() != tk["color"][name].lower()
        }
        check("tokens.json 의 색이 티비와 같다", not drift, drift)

        sp = pg.evaluate("DEFAULT_DATA.specials||[]")
        check("특수 카드가 여섯 장이다", len(sp) == 6, len(sp))
        check(
            "특수 카드 id 가 X1~X6 이다",
            [x.get("id") for x in sp] == ["X1", "X2", "X3", "X4", "X5", "X6"],
            [x.get("id") for x in sp],
        )
        x1 = next((x for x in sp if x.get("id") == "X1"), {})
        check("X1 일기장은 형사만 읽는다", x1.get("only") == "D", x1.get("only"))
        check("특수 카드마다 본문이 있다", all(len(x.get("text") or "") > 40 for x in sp))

        hooked = pg.evaluate(
            "Object.entries(DEFAULT_DATA.cards).flatMap(([id,c])=>"
            "(c.hotspots||[]).filter(h=>h.card).map(h=>id+':'+h.card))"
        )
        check(
            "지점 다섯 곳에 카드가 매달려 있다",
            sorted(hooked) == ["B4:X5", "B5:X4", "K2:X2", "K6:X1", "K6:X3"],
            sorted(hooked),
        )
        check(
            "G1 본문이 X6 을 꺼내라고 한다",
            "X6" in (pg.evaluate("DEFAULT_DATA.cards.G1.text") or ""),
        )
        check(
            "G3 에서 비밀 ③ 지시가 빠졌다",
            "비밀 ③" not in (pg.evaluate("DEFAULT_DATA.cards.G3.text") or ""),
        )

        # 자수서는 3막 범인의 질문("그녀는 왜 쿠키를 먹을까")을 맞혀야 쓴다
        r = pg.evaluate("""(()=>{ try{ setRoleCode("TV","T9"); start();
          const a=confessOpen(); setVerdict("confess","S1"); const b=(S.verdict||{}).confess;
          setVerdict("confess","none"); const c=S.verdict.confess; setVerdict("reset","");
          S.act.D=3; S.memDone.D=[1,2]; enterCode("G2"); answerMemory("피를 좋아하니까");
          const d=confessOpen(); setVerdict("confess","S1"); const e=S.verdict.confess;
          const S0=S; S=Object.assign({},S0); delete S.memPart; const f=confessOpen(); S=S0;
          return {a,b:b===undefined?null:b,c,d,e,f}; }catch(err){ return {err:String(err)}; } })()""")
        check("처음에는 자수서가 잠겨 있다", r.get("a") is False, r)
        check("잠겨 있으면 S1을 골라도 적히지 않는다", "b" in r and r["b"] is None, r)
        check("못 썼다는 언제나 고를 수 있다", r.get("c") == "none", r)
        check("3막 범인의 질문을 맞히면 열린다", r.get("d") is True, r)
        check("열린 뒤에는 S1이 적힌다", r.get("e") == "S1", r)
        check("memPart 없는 옛 상태에서도 false", r.get("f") is False, r)

        b.close()

    print()
    bad = RESULTS.count(False)
    print(f"{len(RESULTS) - bad}/{len(RESULTS)} 통과")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
