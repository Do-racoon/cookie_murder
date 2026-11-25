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
        check("DEFAULT_DATA.version 이 36 다", ver == 36, ver)

        e2 = pg.evaluate("(DEFAULT_DATA.endings.find(e=>e.id==='E2')||{}).code")
        check("엔딩 E2 코드가 쇼트브레드다", e2 == "쇼트브레드", e2)

        ends = pg.evaluate("DEFAULT_DATA.endings")
        check(
            "엔딩이 열 장이고 id 가 E1~E10 다",
            [e["id"] for e in ends] == ["E%d" % i for i in range(1, 11)],
            [e["id"] for e in ends],
        )
        codes = [e.get("code") for e in ends]
        check("엔딩 쿠키 이름이 열 개 다 다르다", len(set(codes)) == 10, codes)

        keys = pg.evaluate("VQ.map(q=>q.k)")
        check("판결 질문이 기소·자수서 둘이다", keys == ["charge", "confess"], keys)

        grid = pg.evaluate(
            """(()=>{const o={};for(const c of ["all","split","her"])
               for(const f of ["S1","S2","none"])
                 o[c+"/"+f]=VGRID[c+"/"+f];
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
        check("특수 카드가 다섯 장이다 — 일기장은 핸드아웃", len(sp) == 5, len(sp))
        check(
            "특수 카드 id 가 X2~X6 이다",
            [x.get("id") for x in sp] == ["X2", "X3", "X4", "X5", "X6"],
            [x.get("id") for x in sp],
        )
        diary = pg.evaluate(
            "(DEFAULT_DATA.cards.K6.hotspots||[]).filter(h=>/일기장/.test(h.hint||''))"
        )
        check("일기장 지점은 카드가 아니라 비밀 ③을 가리킨다",
              len(diary) == 1 and not diary[0].get("card")
              and "비밀 ③" in diary[0].get("hint", ""), diary)
        check("특수 카드마다 본문이 있다", all(len(x.get("text") or "") > 40 for x in sp))

        hooked = pg.evaluate(
            "Object.entries(DEFAULT_DATA.cards).flatMap(([id,c])=>"
            "(c.hotspots||[]).filter(h=>h.card).map(h=>id+':'+h.card))"
        )
        check(
            "지점 네 곳에 카드가 매달려 있다",
            sorted(hooked) == ["B4:X5", "B5:X4", "K2:X2", "K6:X3"],
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

        # 4막에 G2 없이 들어오면, 판결 화면의 안내는 "아직 나타나지 않았다"를 말해야 한다
        h = pg.evaluate("""(()=>{ S=freshState(); start(); S.act.D=4; S.memDone.D=[1,2,3];
          setVerdict("charge","all"); setChannel(4); const t1=document.getElementById('body').innerText;
          enterCode("G2"); setChannel(4); const t2=document.getElementById('body').innerText;
          const dis=[...document.querySelectorAll('[data-vq="confess"]')].filter(x=>x.disabled).length;
          return {t1,t2,dis}; })()""")
        check("G2를 안 열었으면 안내가 질문이 아직 없다고 말한다",
              "열려 있다" not in h["t1"] and "2ㄱ0ㅇ" in h["t1"], h["t1"][-160:])
        check("G2를 열면 안내가 질문이 열려 있다고 말한다", "열려 있다" in h["t2"], h["t2"][-160:])
        check("답하기 전에는 S1·S2 두 버튼이 잠겨 있다", h["dis"] == 2, h["dis"])

        # 문서 모음의 핸드아웃 탭도 새 목표 문구여야 한다
        hub = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        check("문서 모음 핸드아웃 탭에 옛 범인 목표가 없다", "이름을 듣고 나면 선택해야 한다" not in hub)
        check("문서 모음 핸드아웃 탭에 형사 목표 새 문장이 있다", "자수서를 쓸 수 있게 된다" in hub)

        # ── 엔딩 갈래 (2026-11-25) ──
        g = pg.evaluate("""(()=>{ const R={}; const S3=()=>{ S=freshState(); start(); S.act.D=3; S.memDone.D=[1,2]; };
          const lastLog=()=>S.log[0].text;
          try{
          const E=DEFAULT_DATA.endings; R.n=E.length; R.last=E[E.length-1];
          const a3=DEFAULT_DATA.memory.find(m=>m.from===3).asks.map(q=>q.key); R.keys=a3;
          S3(); enterCode("G1"); answerMemory("다리"); R.det=[route(),confessOpen(),S.act.D];
          setChannel(4); R.detLine=document.getElementById('body').innerText;
          S3(); enterCode("G2"); answerMemory("피를 좋아하니까"); endAct3(); endAct3(); R.cul=[route(),S.act.D];
          setChannel(4); R.culLine=document.getElementById('body').innerText;
          answerMemory("다리"); R.culBridge=qDone("bridge");
          S3(); enterCode("G1"); enterCode("G2"); answerMemory("피를 좋아하니까"); answerMemory("다리");
          setVerdict("charge","all"); setVerdict("confess","S1"); R.both=lastLog();
          S3(); endAct3(); endAct3(); setVerdict("charge","her"); setVerdict("confess","none"); R.none=verdictPick(S.verdict);
          S3(); endAct3(); setChannel(1); setChannel(4); endAct3(); R.arm=S.act.D;
          const bad1=Object.assign(JSON.parse(JSON.stringify(DEFAULT_DATA)),{memory:[]});
          const bad2=JSON.parse(JSON.stringify(DEFAULT_DATA)); bad2.memory[2].asks.reverse();
          R.mig=[JSON.stringify(migrate(bad1).memory)===JSON.stringify(DEFAULT_DATA.memory),
                 JSON.stringify(migrate(bad2).memory)===JSON.stringify(DEFAULT_DATA.memory)];
          }catch(e){ R.err=String(e); } return R; })()""")
        check("갈래 검사가 오류 없이 돈다", "err" not in g, g.get("err"))
        check("엔딩이 열 장이고 마지막이 히든 마들렌이다",
              g.get("n") == 10 and (g.get("last") or {}).get("id") == "E10"
              and (g.get("last") or {}).get("code") == "마들렌" and (g.get("last") or {}).get("hidden") is True, g.get("last"))
        check("3막 질문에 herReason·bridge 이름표", sorted(k or "" for k in (g.get("keys") or [])) == ["bridge", "herReason"], g.get("keys"))
        check("형사만 맞히면 연쇄 살인마 갈래, 자수서 잠김, 4막", g.get("det") == ["detective", False, 4], g.get("det"))
        check("형사만 — 판결 화면에 연쇄 살인마", "연쇄 살인마" in (g.get("detLine") or ""))
        check("범인만 맞히고 시간이 끝나면 자수 갈래, 4막", g.get("cul") == ["culprit", 4], g.get("cul"))
        check("범인만 — 판결 화면에 자수", "자수" in (g.get("culLine") or ""))
        check("시간이 끝난 뒤에는 형사의 질문이 닫힌다", g.get("culBridge") is False, g.get("culBridge"))
        check("둘 다 맞히면 고른 엔딩 뒤에 마들렌", "페이스트리" in (g.get("both") or "") and "마들렌" in (g.get("both") or ""), g.get("both"))
        check("둘 다 못 맞히면 취조서와 상관없이 E4", g.get("none") == ["E4"], g.get("none"))
        check("한 번만 누르고 채널을 옮기면 넘어가지 않는다", g.get("arm") == 3, g.get("arm"))
        check("옛 설계·바꾼 질문은 저장소 질문으로 되돌린다", g.get("mig") == [True, True], g.get("mig"))

        b.close()

    print()
    bad = RESULTS.count(False)
    print(f"{len(RESULTS) - bad}/{len(RESULTS)} 통과")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
