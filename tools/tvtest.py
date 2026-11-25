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
        check("DEFAULT_DATA.version 이 41 이다", ver == 41, ver)

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
        check("특수 카드에 본문이 없다 — 글은 카드에만 있다",
              not any(x.get("text") for x in sp),
              [x["id"] for x in sp if x.get("text")])

        hooked = pg.evaluate(
            "Object.entries(DEFAULT_DATA.cards).flatMap(([id,c])=>"
            "(c.hotspots||[]).filter(h=>h.card).map(h=>id+':'+h.card))"
        )
        check(
            "지점 네 곳에 카드가 매달려 있다",
            sorted(hooked) == ["B3:X5", "B5:X4", "K2:X2", "K6:X3"],
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
          S.act.D=3; S.memDone.D=[1,2]; enterCode("G2"); S.found.D.push("G2#0"); answerMemory("피를 좋아하니까");
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
          enterCode("G2"); S.found.D.push("G2#0"); setChannel(4); const t2=document.getElementById('body').innerText;
          const dis=[...document.querySelectorAll('[data-vq="confess"]')].filter(x=>x.disabled).length;
          return {t1,t2,dis}; })()""")
        check("G2를 안 열었으면 안내가 질문이 아직 없다고 말한다",
              "열려 있다" not in h["t1"] and "2ㄱ0ㅇ" in h["t1"], h["t1"][-160:])
        check("G2 의 쿠키를 찾으면 안내가 질문이 열려 있다고 말한다", "열려 있다" in h["t2"], h["t2"][-160:])
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
          S3(); enterCode("G2"); S.found.D.push("G2#0"); answerMemory("피를 좋아하니까"); endAct3(); endAct3(); R.cul=[route(),S.act.D];
          setChannel(4); R.culLine=document.getElementById('body').innerText;
          answerMemory("다리"); R.culBridge=qDone("bridge");
          S3(); enterCode("G1"); enterCode("G2"); S.found.D.push("G2#0"); answerMemory("피를 좋아하니까"); answerMemory("다리");
          setVerdict("charge","all"); setVerdict("confess","S1"); R.both=lastLog();
          S3(); endAct3(); endAct3(); setVerdict("charge","her"); setVerdict("confess","none"); R.none=verdictPick(S.verdict);
          S3(); endAct3(); setChannel(1); setChannel(4); endAct3(); R.arm=S.act.D;
          S3(); setChannel(4); R.act3hint=document.getElementById('body').innerText;
          S=freshState(); start(); setChannel(4); R.act1hint=document.getElementById('body').innerText;
          S3(); endAct3(); const saved=JSON.parse(JSON.stringify(S)); S=migrateState(saved); R.armReload=[!!S.endArm,S.act.D];
          endAct3(); R.armReload.push(S.act.D);
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
        check("3막 화면은 '두 질문을 모두'라고 하지 않고 형사의 질문으로 판결에 간다고 한다",
              "두 질문을 모두 맞혀야" not in (g.get("act3hint") or "") and "형사의 질문을 맞히면 판결" in (g.get("act3hint") or ""))
        check("한 번 누른 뒤 새로고침하면 대기가 풀린다 — 한 번 더 눌러도 판결로 가지 않는다",
              g.get("armReload") == [False, 3, 3], g.get("armReload"))
        check("1막 화면은 여전히 두 질문을 모두 맞혀야 한다고 한다", "두 질문을 모두 맞혀야" in (g.get("act1hint") or ""))

        # ── 서랍 문 · 비비기 멘트 · 히든 엔딩 순서 · 잠금 안내 (2026-11-25 오후) ──
        def tap(card, x, y):
            pg.evaluate(f"(()=>{{ if(!$('shutter').hidden) closeSheet(); viewCard='{card}'; ch=2; render();}})()")
            box = pg.evaluate("(()=>{const L=document.querySelector('.photo .layer')||document.querySelector('.photo'); const r=L.getBoundingClientRect(); return [r.left,r.top,r.width,r.height];})()")
            pg.mouse.click(box[0] + box[2] * x / 100, box[1] + box[3] * y / 100)
            pg.wait_for_timeout(50)
        def fresh1():
            pg.evaluate("""(()=>{ S=freshState(); start(); enterCode("K3"); enterCode("K6"); S.found.D.push("K6#0"); })()""")
        last = lambda: pg.evaluate("S.log[0].text")
        fresh1()
        pg.evaluate("""(()=>{ setChannel(4); answerMemory("3년"); answerMemory("그녀"); })()""")
        g1 = [pg.evaluate("S.act.D"), last()]
        check("질문 둘을 맞혀도 서랍 전이면 1막 그대로, 문 안내", g1[0] == 1 and "열지 않은 곳" in g1[1], g1)
        t = pg.evaluate("""(()=>{ let T=""; const o=toast; toast=x=>{T=x;}; setChannel(4); answerMemory("아무거나"); toast=o; return T; })()""")
        check("서랍 전에 답을 넣으면 문 안내 토스트", "열지 않은 곳" in t, t)
        tap("K6", 93, 52)
        logs = pg.evaluate("S.log.slice(0,3).map(l=>l.text).join(' | ')")
        check("서랍을 열면 그 자리에서 2막, 비비기 멘트", pg.evaluate("S.act.D") == 2 and "2막으로" in logs and "비벼서 봐라" in logs, logs)
        sc = pg.evaluate("[ch, document.getElementById('body').innerText]")
        check("질문 먼저 → 서랍을 누르면 사진에 서랍 설명(▶ 형사: 비밀 ③)이 그대로 보인다", sc[0] == 2 and "비밀 ③" in sc[1], [sc[0], sc[1][-200:]])
        fresh1(); tap("K6", 93, 52)
        pg.evaluate("""(()=>{ setChannel(4); answerMemory("3년"); answerMemory("그녀"); })()""")
        logs = pg.evaluate("S.log.map(l=>l.text).join(' | ')")
        check("서랍을 먼저 열면 질문 둘로 바로 2막", pg.evaluate("S.act.D") == 2 and "열지 않은 곳" not in logs, logs[:200])
        fresh1()
        pg.evaluate("""(()=>{ S.found.C.push("K6#3"); setChannel(4); answerMemory("3년"); answerMemory("그녀"); })()""")
        check("범인 시점으로 서랍을 눌러도 문이 열린다", pg.evaluate("S.act.D") == 2)
        fresh1()
        pg.evaluate("""(()=>{ setChannel(4); answerMemory("3년"); answerMemory("그녀"); const j=JSON.parse(JSON.stringify(S)); S=migrateState(j); })()""")
        tap("K6", 93, 52)
        check("옛 판: 질문 둘만 맞힌 저장값에서 서랍을 누르면 2막", pg.evaluate("S.act.D") == 2)
        r = pg.evaluate("""(()=>{ S=freshState(); start(); S.act.D=2; S.memDone.D=[1]; enterCode("B3"); enterCode("B5");
              S.found.D.push("B3#0"); setChannel(4); answerMemory("어머니"); answerMemory("진짜 범인"); const a=S.log[0].text;
              S=freshState(); start(); S.act.D=3; S.memDone.D=[1,2]; enterCode("G1"); setChannel(4); answerMemory("다리"); const b=S.log[0].text;
              S=freshState(); start(); S.act.D=3; S.memDone.D=[1,2]; enterCode("G1"); enterCode("G2"); S.found.D.push("G2#0"); answerMemory("피를 좋아하니까"); answerMemory("다리");
              setVerdict("charge","all"); setVerdict("confess","S1"); const c=S.log[0].text; setChannel(4); const d=document.getElementById('body').innerText;
              return {a,b,c,d}; })()""")
        check("2→3 전환에도 비비기 멘트", "3막으로" in r["a"] and "비벼서 봐라" in r["a"], r["a"])
        check("3→판결에는 비비기 멘트 없음", "판결" in r["b"] and "비벼서" not in r["b"], r["b"])
        c = r["c"]
        check("둘 다 맞힌 엔딩 기록: 고른 엔딩 먼저, 다 읽은 뒤 마들렌",
              "다 읽은 뒤" in c and "「마들렌」" in c and c.find("「페이스트리」") < c.find("「마들렌」"), c)
        check("둘 다 맞힌 판결 화면도 같은 순서", "다 읽은 뒤" in r["d"] and "그녀의 이야기" in r["d"])
        lk = pg.evaluate("""(()=>{ const go=()=>{ S=freshState(); start(); S.act.D=4; S.memDone.D=[1,2,3]; enterCode("G1"); S.memPart.D[3]=[askByKey("bridge").i];
              S.verdict={charge:"all"}; setChannel(4); return document.getElementById('body').innerText; };
              const a=go(); const keep=DEFAULT_DATA.memory; const m=JSON.parse(JSON.stringify(D.memory)); m[2].asks.reverse(); D.memory=m;
              const b=go(); D.memory=keep; return [a,b]; })()""")
        check("자수서 잠금 안내가 herReason 질문을 이름표로 찾는다", lk[0] == lk[1] and "그녀가 왜 쿠키를 먹는지" in lk[0], [lk[0][-160:], lk[1][-160:]])

        # ── 비비기 ──
        def lay(card):
            pg.evaluate(f"(()=>{{ if(!$('shutter').hidden) closeSheet(); viewCard='{card}'; ch=2; render();}})()")
            return pg.evaluate("(()=>{const L=document.querySelector('.photo .layer'); if(!L) return null; const r=L.getBoundingClientRect(); return [r.left,r.top,r.width,r.height];})()")
        def rub(box, pts):
            X = lambda x: box[0] + box[2] * x / 100; Y = lambda y: box[1] + box[3] * y / 100
            pg.mouse.move(X(pts[0][0]), Y(pts[0][1])); pg.mouse.down()
            for x, y in pts[1:]:
                pg.mouse.move(X(x), Y(y), steps=4)
            pg.mouse.up(); pg.wait_for_timeout(60)
        pg.evaluate("""(()=>{ S=freshState(); start(); enterCode("K4"); enterCode("K3"); })()""")
        h = pg.evaluate("D.cards.K4.hotspots[0]")
        box = lay("K4"); n0 = pg.evaluate("S.log.length")
        rub(box, [(h["x"] - 15, h["y"]), (h["x"] + 15, h["y"]), (h["x"], h["y"])])
        glow = pg.evaluate("document.querySelectorAll('.photo .glow').length")
        check("비비면 못 찾은 지점 근처에서 빛(.glow)이 생긴다", glow >= 1, glow)
        check("비비기를 지점 위에서 끝내도 지점이 열리지 않는다", pg.evaluate("S.found.D.includes('K4#0')") is False)
        check("비비기는 기록을 남기지 않는다", pg.evaluate("S.log.length") == n0)
        pg.wait_for_timeout(1800)
        check("1.5초 뒤 빛이 사라진다", pg.evaluate("document.querySelectorAll('.photo .glow').length") == 0)
        box = lay("K4"); pg.mouse.click(box[0] + box[2] * h["x"] / 100, box[1] + box[3] * h["y"] / 100); pg.wait_for_timeout(60)
        check("짧게 누르면 지금처럼 열린다", pg.evaluate("S.found.D.includes('K4#0')") is True)
        box = lay("K4"); rub(box, [(h["x"] - 15, h["y"]), (h["x"] + 15, h["y"])])
        check("이미 찾은 지점은 빛나지 않는다", pg.evaluate("[...document.querySelectorAll('.photo .glow')].every(g=>g.dataset.i!=='0')"))
        box = lay("K4"); X = lambda x: box[0] + box[2] * x / 100; Y = lambda y: box[1] + box[3] * y / 100
        pg.mouse.move(X(30), Y(50)); pg.mouse.down(); pg.mouse.move(X(70), Y(50), steps=6); pg.mouse.move(box[0] + box[2] + 40, Y(50), steps=3); pg.mouse.up()
        pg.click(".photo .pbig"); pg.wait_for_timeout(120)
        check("비비다 사진 밖에서 놓은 뒤 ⤢(크게 보기)를 누르면 바로 열린다", pg.evaluate("!!document.querySelector('.bigview')"))
        pg.evaluate("closeSheet()")
        pg.evaluate("(()=>{viewCard='K3'; ch=2; render();})()")
        bb = pg.evaluate("(()=>{const r=document.getElementById('body').getBoundingClientRect(); return [r.left,r.top,r.width,r.height];})()")
        pg.mouse.move(bb[0] + 50, bb[1] + 50); pg.mouse.down(); pg.mouse.move(bb[0] + 200, bb[1] + 60, steps=5); pg.mouse.up()
        check("글 카드에서 끌어도 오류 없음", pg.evaluate("document.querySelectorAll('.glow').length") == 0)

        # ── 휴대폰 터치 (문지른 뒤 첫 탭을 브라우저가 click 으로 안 내 주는 경우) ──
        tctx = b.new_context(**p.devices["iPhone 13"]); tp = tctx.new_page(); tp.goto(pg.url.split("#")[0]); tp.wait_for_timeout(400)
        cdp = tctx.new_cdp_session(tp)
        def T(pts, w=350):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": pts[0][0], "y": pts[0][1]}]})
            for x, y in pts[1:]:
                tp.wait_for_timeout(16); cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y}]})
            cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}); tp.wait_for_timeout(w)
        def tl(sel):
            return tp.evaluate(f"(()=>{{const L=document.querySelector('{sel}'); if(!L) return null; const r=L.getBoundingClientRect(); return [r.left,r.top,r.width,r.height]}})()")
        tp.evaluate('(()=>{setRoleCode("TV","T9"); S=freshState(); start(); enterCode("K4"); viewCard="K4"; ch=2; render();})()'); tp.wait_for_timeout(200)
        th = tp.evaluate("D.cards.K4.hotspots[0]"); bx = tl(".photo .layer"); TP = lambda x, y: (bx[0] + bx[2] * x / 100, bx[1] + bx[3] * y / 100)
        T([TP(th["x"] - 18 + i * 3, th["y"]) for i in range(13)])
        T([TP(th["x"], th["y"])])
        check("터치: 문지른 뒤 빛난 자리를 바로 탭하면 열린다", tp.evaluate("S.found.D.includes('K4#0')"))
        bx = tl(".photo .layer"); T([TP(20, 50), TP(40, 50), TP(60, 52), TP(80, 50)])
        pb = tl(".photo .pbig"); T([(pb[0] + pb[2] / 2, pb[1] + pb[3] / 2)])
        check("터치: 문지른 뒤 ⤢ 첫 탭에 크게 보기가 열린다", tp.evaluate("!!document.querySelector('.bigview')"))
        tp.evaluate("closeSheet()"); tp.evaluate("(()=>{viewCard='K4'; ch=2; capIdx=null; lastFound=null; render();})()"); tp.wait_for_timeout(700)
        n0 = tp.evaluate("S.log.length"); bx = tl(".photo .layer"); T([TP(th["x"], th["y"])])
        check("터치: 찾은 지점을 한 번 탭하면 한 번만 반응한다(설명 열기)", tp.evaluate("capIdx") == 0, tp.evaluate("[capIdx, !!document.querySelector('.bigview'), S.found.D, S.log.slice(0,2).map(l=>l.text)]"))
        tctx.close()

        # ── 사진 단서 개편 (2026-11-26) ──
        r = pg.evaluate("""(()=>{ const ids=Object.keys(D.cards);
          S=freshState(); start(); S.act.D=3; S.memDone.D=[1,2]; enterCode("6ㅈ1ㅂ"); enterCode("4ㄹ7ㅎ"); enterCode("2ㄱ0ㅇ");
          const yrs=JSON.stringify(DEFAULT_DATA).match(/20(22|23|24|25|26)[년.]/g);
          return {ids, op:S.opened.D.slice(), g2:D.cards.G2.kind, g2h:(D.cards.G2.hotspots||[])[0]&&D.cards.G2.hotspots[0].hint, yrs}; })()""")
        check("K1·B2·B4 카드가 없다", not set(r["ids"]) & {"K1", "B2", "B4"}, r["ids"])
        check("B6·G4 가 새 코드로 열린다", "B6" in r["op"] and "G4" in r["op"], r["op"])
        check("G2 는 사진 카드이고 지점 1 에 ▶ 범인 기억 ④", r["g2"] == "photo" and "기억 ④" in (r["g2h"] or ""), [r["g2"], r["g2h"]])
        check("티비 설계에 옛 연도(2022~2026)가 없다", not r["yrs"], r["yrs"])
        r = pg.evaluate("""(()=>{ S=freshState(); start(); enterCode("K6"); viewCard="K6"; ch=2; render();
          const before=!!document.querySelector('.picview'); S.found.D.push("K6#0"); openPicFor("K6",0); const a=!!document.querySelector('.picview img') && document.querySelector('.picview').innerText.includes('곰인형');
          closeSheet(); const b=!document.querySelector('.picview') && ch===2; return {before,a,b}; })()""")
        check("곰인형 눈 → 이어지는 사진이 뜨고 닫으면 돌아온다", (not r["before"]) and r["a"] and r["b"], r)
        box = pg.evaluate("""(()=>{ S=freshState(); start(); enterCode("K6"); viewCard="K6"; ch=2; capIdx=null; lastFound=null; render();
          const r=document.querySelector('.photo .layer').getBoundingClientRect(); return [r.left,r.top,r.width,r.height]; })()""")
        hh = pg.evaluate("D.cards.K6.hotspots[0]")
        pg.mouse.click(box[0] + box[2] * hh["x"] / 100, box[1] + box[3] * hh["y"] / 100); pg.wait_for_timeout(120)
        check("곰인형 눈을 처음 찾으면 확대 사진이 저절로 뜬다", pg.evaluate("!!document.querySelector('.picview img') && document.querySelector('.picview').innerText.includes('곰인형')"))
        pg.evaluate("closeSheet()")
        pg.evaluate("(()=>{viewCard='K6'; ch=2; capIdx=0; render();})()")
        check("설명에 「사진을 본다」 단추가 있다", pg.evaluate("!!document.querySelector('.photo .cap [data-pic]')"))
        r = pg.evaluate("""(()=>{ S=freshState(); start(); S.act.D=3; S.memDone.D=[1,2]; enterCode("G1"); enterCode("4ㄹ7ㅎ");
          const pre=!!document.querySelector('.picview'); setChannel(4); answerMemory("다리");
          const post=!!document.querySelector('.picview img') && document.querySelector('.picview').innerText.includes('다리'); closeSheet(); return {pre,post}; })()""")
        check("다리 사진은 답하기 전엔 없고, 답하면 뜬다", r["pre"] is False and r["post"] is True, r)
        r = pg.evaluate("""(()=>{ const q=D.memory.find(x=>x.from===3).asks.find(a=>a.key==="herReason");
          const sv=JSON.stringify(S); S.opened.D=[...new Set([...S.opened.D,"G2"])]; S.found.D=S.found.D.filter(k=>k!=="G2#0");
          const a=askOpen("D",q); S.found.D.push("G2#0"); const b=askOpen("D",q); Object.assign(S,JSON.parse(sv)); return {a,b}; })()""")
        check("3막 범인의 질문은 G2 의 쿠키(기억 ④ 지시)를 찾은 뒤에야 뜬다", r["a"] is False and r["b"] is True, r)
        r = pg.evaluate("""(()=>{ const st=freshState(); st.started=true; st.opened.D=["K1","K2","B2","B4"]; st.found.D=["K1#0","B4#1","K2#0"];
          S=migrateState(st); setChannel(2); render(); return {op:S.opened.D, fd:S.found.D}; })()""")
        check("옛 판(K1·B2·B4 열림)도 오류 없이, 없는 카드는 걸러 낸다", r["op"] == ["K2"] and r["fd"] == ["K2#0"], r)

        b.close()

    print()
    bad = RESULTS.count(False)
    print(f"{len(RESULTS) - bad}/{len(RESULTS)} 통과")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
