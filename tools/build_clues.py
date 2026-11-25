"""사진 단서 검토 페이지 — 티비 설계(tv/source.html)에서 사진 카드와 지점을 뽑아 docs/clues.html 로 그린다.

    python3 tools/build_clues.py

사진마다 누르면 열리는 자리(원)와 번호, 그 지점에서 뜨는 문장, 그 지점이 하는 일
(▶ 읽기 지시 · ▣ 특수 카드 · 이 지점을 열어야 나타나는 막의 질문 · 막 전환 문)을 보여 준다.
손으로 고치지 않는다 — 단서를 고친 뒤 다시 돌린다.
"""
import base64
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import synctest  # noqa: E402  (tv_data: tv/source.html 의 DEFAULT_DATA)

TOK = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
P, ACT = TOK["paperColor"], TOK["paperAct"]
FLAG = {"new": "새로", "chg": "바뀜"}
ACTNAME = {1: "1막 — 현행범 현장", 2: "2막 — 맥주집", 3: "3막 — 반지하"}


def img_uri(src: str) -> str:
    m = re.search(r"/_blob/([0-9a-f]{32})", src or "")
    f = ROOT / "tv" / "img" / (m.group(1) + ".jpg") if m else ROOT / "tv" / (src or "")
    return "data:image/jpeg;base64," + base64.b64encode(f.read_bytes()).decode() if f.exists() else ""


def roles(d):
    """지점 키(카드#번호, 카드) → 그것이 여는 것들"""
    out = {}
    for m in d["memory"]:
        for q in m.get("asks", []):
            if q.get("need"):
                out.setdefault(q["need"], []).append(
                    f"{m['from']}막 {q['who']}의 질문이 나타난다 — “{q['ask']}”")
        if m.get("gate"):
            out.setdefault(m["gate"], []).append(f"{m['from']}막 → {m['to']}막 문 — 이 지점을 열어야 막이 넘어간다")
    return out


def main(argv=None) -> int:
    argv = argv or []
    d = synctest.tv_data()
    draft = None
    if "--draft" in argv:   # 고칠 안: 티비 설계는 그대로 두고, 안(JSON)을 얹어 검토용으로만 그린다
        draft = json.loads((ROOT / argv[argv.index("--draft") + 1]).read_text(encoding="utf-8"))
        for cid, ov in draft.get("cards", {}).items():
            c = d["cards"].setdefault(cid, {"kind": "photo"})
            for k in ("title", "img", "act"):
                if k in ov: c[k] = ov[k]
            if "hotspots" in ov: c["hotspots"] = ov["hotspots"]
    gone = set((draft or {}).get("remove", []))
    notes = (draft or {}).get("notes", {})
    specials = {x["id"]: x for x in d.get("specials", [])}
    R = roles(d)
    cards = [(k, c) for k, c in d["cards"].items() if c.get("kind") == "photo"]
    cards.sort(key=lambda kc: (kc[1].get("act", 1), kc[0]))
    total = sum(len(c.get("hotspots", [])) for _, c in cards)
    idle = 0
    sections, cur = [], None
    for cid, c in cards:
        act = c.get("act", 1)
        if act != cur:
            if cur is not None:
                sections.append("</section>")
            sections.append(f'<section class="act" style="--act:{ACT.get(cid[0], P["bronze"])}">'
                            f'<h2>{html.escape(ACTNAME.get(act, f"{act}막"))}</h2>')
            cur = act
        hs = c.get("hotspots", [])
        marks, rows = [], []
        card_roles = R.get(cid, [])
        for i, h in enumerate(hs):
            n = i + 1
            r = h.get("r", 8)
            marks.append(f'<span class="ring" style="left:{h["x"]}%;top:{h["y"]}%;width:{2*r}%;height:{2*r}%"></span>'
                         f'<span class="num" style="left:{h["x"]}%;top:{h["y"]}%">{n}</span>')
            hint = h.get("hint", "")
            star = hint.startswith("★")
            text = hint.lstrip("★")
            does = []
            for t in re.findall(r"▶\s*([^▶▣]+)", text):
                does.append(("read", "▶ " + t.strip()))
            text = re.split(r"\s*▶", text)[0].strip()
            if h.get("card"):
                sp = specials.get(h["card"], {})
                does.append(("card", f"▣ 특수 카드 {h['card']} · {sp.get('kind','')} 「{sp.get('title','')}」을 꺼낸다"))
            for t in R.get(f"{cid}#{i}", []):
                does.append(("gate" if "문" in t else "ask", t))
            if h.get("only"):
                does.append(("note", "지시는 " + ("형사" if h["only"] == "D" else "범인") + "에게"))
            if not [x for x in does if x[0] != "note"]:
                idle += 1
                does.append(("none", "이어지는 곳 없음 — 읽을거리만"))
            li = "".join(f'<li class="{k}">{html.escape(t)}</li>' for k, t in does)
            flag = h.get("flag", "")
            was = f'<p class="was">지금: {html.escape(h["was"])}</p>' if h.get("was") else ""
            rows.append(f'<li class="spot {flag}" id="{cid}-{n}"><b class="sn">{cid}-{n}</b>'
                        + (f'<span class="flag">{FLAG.get(flag, "")}</span>' if flag else "")
                        + f'{"<span class=star>★</span>" if star else ""}'
                        f'<span class="xy">x {h["x"]} · y {h["y"]} · 반경 {r}</span>'
                        f'<p>{html.escape(text)}</p>{was}<ul class="does">{li}</ul></li>')
        cr = "".join(f'<p class="cardrole">{html.escape(t)}</p>' for t in card_roles)
        if cid in notes: cr = f'<p class="note">{html.escape(notes[cid])}</p>' + cr
        uri = img_uri(c.get("img", ""))
        sections.append(
            f'<article class="card{" gone" if cid in gone else ""}" id="{cid}"><header><span class="cid">{cid}</span>'
            + ('<span class="gonetag">이 카드는 빠진다</span>' if cid in gone else "")
            + f'<h3>{html.escape(c.get("title",""))}</h3><span class="code">{html.escape(c.get("code",""))}</span>'
            f'<span class="cnt">지점 {len(hs)}</span></header>'
            f'<div class="grid"><figure class="ph">'
            + (f'<img src="{uri}" alt="{html.escape(c.get("title",""))} 사진">' if uri else '<div class="noimg">사진 없음</div>')
            + "".join(marks) + f'</figure><div class="list">{cr}<ol>{"".join(rows)}</ol></div></div></article>')
    sections.append("</section>")
    toc = " ".join(f'<a href="#{cid}">{cid}</a>' for cid, _ in cards)
    page = f"""<title>사진 단서 검토</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700&family=Nanum+Gothic+Coding:wght@400;700&display=swap">
<style>
/* 종이 한 벌 — 문서 모음의 읽는 면과 같은 빵봉투 크라프트. 한 가지 모습으로만 그린다. */
:root{{--paper:{P['paper']};--paper2:{P['paper-2']};--kraft:{P['kraft']};--ink:{P['ink']};--dim:{P['ink-dim']};
  --rule:{P['rule']};--stamp:{P['stamp']};--room:#1c1712;--lamp:#f2dfb4;
  --serif:"Gowun Batang","Nanum Myeongjo",serif;--mono:"Nanum Gothic Coding",ui-monospace,monospace;color-scheme:light}}
body{{background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:16px;line-height:1.6}}
.top{{background:var(--room);color:var(--lamp);padding-block:22px 16px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
.top h1{{margin:0;font-size:1.5rem;text-wrap:balance}}
.top p{{margin:.3rem 0 .6rem;color:#cbb98f;font-size:.92rem;max-width:62ch}}
.top nav{{display:flex;flex-wrap:wrap;gap:6px;font-family:var(--mono);font-size:.85rem}}
.top nav a{{color:var(--lamp);text-decoration:none;border:1px solid #5a4a33;border-radius:4px;padding:2px 8px}}
.top nav a:focus-visible,.top nav a:hover{{background:#3a2f22}}
main{{padding-block:8px 48px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));max-width:1180px;margin:0 auto}}
.legend{{font-family:var(--mono);font-size:.82rem;color:var(--dim);display:flex;flex-wrap:wrap;gap:4px 14px;margin:14px 0 4px}}
.act h2{{font-size:1.2rem;margin:34px 0 10px;padding-top:6px;border-top:4px solid var(--act)}}
.card{{background:var(--paper2);border:1px solid var(--rule);border-radius:6px;margin:0 0 18px;padding:12px}}
.card header{{display:flex;align-items:baseline;flex-wrap:wrap;gap:6px 12px;margin-bottom:10px}}
.cid{{font-family:var(--mono);font-weight:700;background:var(--act);color:var(--paper);padding:1px 8px;border-radius:3px}}
.card h3{{margin:0;font-size:1.1rem}}
.code{{font-family:var(--mono);border:1.5px solid var(--stamp);color:var(--stamp);padding:0 6px;border-radius:2px}}
.cnt{{font-family:var(--mono);font-size:.82rem;color:var(--dim);margin-left:auto}}
.grid{{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:16px;align-items:start}}
@media (max-width:760px){{.grid{{grid-template-columns:minmax(0,1fr)}}}}
.ph{{position:relative;margin:0;max-width:100%;line-height:0;border-radius:4px;overflow:hidden;background:var(--room)}}
.ph img{{width:100%;height:auto;display:block}}
.ring{{position:absolute;transform:translate(-50%,-50%);border:2px solid #ffe7a8;border-radius:50%;box-shadow:0 0 0 2px rgba(27,21,14,.55),inset 0 0 0 1px rgba(27,21,14,.4);pointer-events:none}}
.num{{position:absolute;transform:translate(-50%,-50%);font:700 13px/1 var(--mono);background:#ffe7a8;color:var(--ink);border-radius:50%;width:22px;height:22px;display:grid;place-items:center;box-shadow:0 0 0 2px var(--ink)}}
.noimg{{padding:40px;color:var(--lamp);font-family:var(--mono);line-height:1.4}}
.list{{min-width:0}}
.cardrole{{margin:0 0 8px;font-family:var(--mono);font-size:.84rem;background:var(--paper);border-left:3px solid var(--act);padding:4px 8px}}
.list ol{{list-style:none;margin:0;padding:0;display:grid;gap:10px}}
.spot{{background:var(--paper);border:1px solid var(--rule);border-radius:4px;padding:8px 10px}}
.sn{{font-family:var(--mono);margin-right:6px}}
.star{{color:var(--stamp);font-weight:700;margin-right:6px}}
.xy{{font-family:var(--mono);font-size:.75rem;color:var(--dim)}}
.spot p{{margin:4px 0 6px}}
.does{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:3px;font-family:var(--mono);font-size:.8rem}}
.does li{{padding:2px 6px;border-radius:3px;background:var(--paper2)}}
.does .read{{color:#3d2a7a}} .does .card{{color:#4f3f7d}} .does .ask{{color:#355a6d}} .does .gate{{color:var(--stamp);font-weight:700}}
.note{{margin:0 0 8px;font-size:.9rem;background:#fff6dc;border:1px solid #d8b75f;border-radius:4px;padding:6px 9px}}
.was{{margin:0 0 6px;font-size:.82rem;color:var(--dim);text-decoration:line-through}}
.flag{{font-family:var(--mono);font-size:.72rem;background:var(--stamp);color:var(--paper);border-radius:3px;padding:0 5px;margin-right:6px}}
.spot.new{{border-color:var(--stamp)}} .spot.chg{{border-color:#c79a3a}}
.card.gone{{opacity:.5}} .gonetag{{font-family:var(--mono);font-size:.8rem;color:var(--paper);background:var(--stamp);padding:1px 8px;border-radius:3px}}
.does .none{{color:var(--dim);background:transparent;border:1px dashed var(--rule)}} .does .note{{color:var(--dim);background:transparent}}
</style>
<div class="top"><h1>{"사진 단서 — 고칠 안" if draft else "사진 단서 검토"}</h1>
<p>티비가 실제로 반응하는 자리를 원으로 그렸다. 원 크기가 누르면 열리는 범위다. 번호(예: K2-3)로 짚어 말하면 된다. 사진 {len(cards)}장 · 지점 {total}개 · 아무 데도 이어지지 않는 지점 {idle}개.</p>
<nav>{toc}</nav></div>
<main><div class="legend"><span>★ 핵심 지점</span><span>▶ 누구에게 읽으라는 지시</span><span>▣ 꺼내는 특수 카드</span><span>막의 질문이 나타나는 곳</span><span>막 전환 문</span><span>점선 = 이어지는 곳 없음</span></div>
{''.join(sections)}
</main>"""
    if draft:
        head = "".join(f"<li>{html.escape(x)}</li>" for x in draft.get("summary", []))
        page = page.replace("<title>사진 단서 검토</title>", "<title>사진 단서 고칠 안</title>").replace(
            '<main><div class="legend">', f'<main><ul class="summary">{head}</ul><div class="legend">')
        page = page.replace("</style>", ".summary{margin:14px 0 0;padding-left:1.2em;display:grid;gap:4px}</style>")
    out = ROOT / "docs" / ("clues-draft.html" if draft else "clues.html")
    out.write_text(page, encoding="utf-8")
    print(f"{out.relative_to(ROOT)} — 사진 {len(cards)}장, 지점 {total}개, 이어지는 곳 없음 {idle}개")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
