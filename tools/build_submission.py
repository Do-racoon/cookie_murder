"""제출본 묶음을 지금 설계에서 다시 만든다.

    python3 tools/build_submission.py submission-2026-11-26

원본은 저장소의 것들이다 — 소개서·룰북은 문서 모음(docs/index.html)의 탭, 롤카드·엔딩은
핸드아웃(text/핸드아웃.md), 시스템·인물·진실·판결은 기획서(text/기획서.md),
지점표·질문표는 티비 설계(tv/source.html), 카드 글은 cards/cards.py.
Word 모양은 11/22 제출본 파일을 본(reference)으로 쓴다. 11/22 묶음은 읽기만 한다.
"""
import ast
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OLD = ROOT / "submission-2026-11-22"


def pandoc(src_text, fmt, out, ref=None, extra=()):
    cmd = ["pandoc", "-f", fmt, "-o", str(out)] + list(extra)
    if ref:
        cmd += ["--reference-doc", str(ref)]
    subprocess.run(cmd, input=src_text.encode("utf-8"), check=True)


def section(html, sid):
    m = re.search(r'<section class="panel" id="%s"[^>]*>(.*?)</section>' % sid, html, re.S)
    body = m.group(1)
    body = re.sub(r'<nav class="toc">.*?</nav>', "", body, flags=re.S)
    return body


def md_sections(md):
    """'## 제목' 단위로 나눈다."""
    out, cur, buf = {}, None, []
    for line in md.split("\n"):
        if line.startswith("## "):
            if cur:
                out[cur] = "\n".join(buf).strip()
            cur, buf = line[3:].strip(), []
        elif cur:
            buf.append(line)
    if cur:
        out[cur] = "\n".join(buf).strip()
    return out


def demote(md, by=1):
    return re.sub(r"^(#+) ", lambda m: "#" * (len(m.group(1)) + by) + " ", md, flags=re.M)


def find(secs, prefix):
    return next(v for k, v in secs.items() if k.startswith(prefix))


def cards_py():
    tree = ast.parse((ROOT / "cards" / "cards.py").read_text(encoding="utf-8"))
    got = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ("CARDS", "SPECIAL_BODY") and node.targets[0].id not in got:
            got[node.targets[0].id] = eval(compile(ast.Expression(node.value), "cards", "eval"), {"dict": dict})
    return got["CARDS"], got["SPECIAL_BODY"]


def tv_data():
    src = (ROOT / "tv" / "source.html").read_text(encoding="utf-8")
    return json.loads(re.search(r"const DEFAULT_DATA\s*=\s*(\{.*?\n\});", src, re.S).group(1))


ACT = {1: "1막 — 현행범 현장", 2: "2막 — 맥주집", 3: "3막 — 반지하"}


def answer_sheet(d, cards, specials, plan):
    by = {c["id"]: c for c in cards}
    L = ["플레이 전에는 열지 않는다. 티비를 쓸 수 없을 때의 종이 진행, 그리고 판결에 쓴다.", "", "# 1. 사진 지점표와 글 카드", ""]
    for act in (1, 2, 3):
        L += [f"## {ACT[act]}", ""]
        for cid, c in d["cards"].items():
            if (c.get("act") or 1) != act:
                continue
            L.append(f"**{cid} {c.get('title','')}** ({c.get('code','')})")
            L.append("")
            if c.get("kind") == "photo":
                for i, h in enumerate(c.get("hotspots", []), 1):
                    t = h["hint"]
                    if h.get("card"):
                        t += f" ▣ 특수 카드 {h['card']}를 꺼낸다"
                    if h.get("pic"):
                        t += f" — 이어지는 사진: {h['pic'].get('cap','')}"
                    L.append(f"{i}. {t}")
                if c["hotspots"] and c.get("gate") is None:
                    pass
            else:
                L.append(c.get("text") or by.get(cid, {}).get("body", ""))
            L.append("")
    L += ["## 특수 카드 — 증언 · 국과수 감정서", ""]
    for s in d.get("specials", []):
        L += [f"**{s['id']} {s.get('title','')}** ({s.get('kind','')}, {s.get('act','')}막)", "", specials.get(s["id"], "").replace("\n\n", "\n\n"), ""]
    L += ["# 2. 막의 질문", "", "| 막 | 누구의 질문 | 질문 | 답 (핵심 낱말이면 된다) | 나타나는 때 |", "|---|---|---|---|---|"]
    for m in d["memory"]:
        for q in m.get("asks", []):
            ans = " / ".join(q.get("answers", [])[:3]) or "—"
            need = q.get("lock", "")
            opt = " (막 전환에 필요 없음)" if q.get("optional") else ""
            L.append(f"| {m['from']}막 | {q['who']}{opt} | {q['ask']} | {ans} | {need} |")
    gates = [m for m in d["memory"] if m.get("gate")]
    if gates:
        L += ["", "1막의 문: 두 질문을 다 맞혀도, 그녀의 방(K6) 사진의 책상 옆 서랍을 찾아야 2막이 열린다."]
    L += ["", "# 3. 사건의 진실", "", find(plan, "6."), "", find(plan, "7."), "", "# 4. 판결", "", demote(find(plan, "10."), 0)]
    return "\n".join(L)


def main(argv):
    out = ROOT / (argv[0] if argv else "submission-2026-11-26")
    out.mkdir(exist_ok=True)
    hub = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    ho = md_sections((ROOT / "text" / "핸드아웃.md").read_text(encoding="utf-8"))
    plan_md = (ROOT / "text" / "기획서.md").read_text(encoding="utf-8")
    plan = md_sections(plan_md)
    cards, specials = cards_py()
    d = tv_data()

    # 1. 소개서 · 3. 규칙서 — 문서 모음 탭 그대로
    pandoc("<h1>쿠키 살인 사건</h1><p>작품 소개서 · 두 사람의 알리바이 2인 머더미스터리 공모전</p>" + section(hub, "intro"), "html", out / "1_게임소개서.docx", OLD / "1_게임소개서.docx")
    pandoc("<h1>쿠키 살인 사건 — 게임 규칙서</h1>" + section(hub, "rule"), "html", out / "3_게임규칙서.docx", OLD / "3_게임규칙서.docx")

    # 2. 롤카드 및 시스템
    ho_c = find(ho, "범인 HO")
    ho_c = re.sub(r"^### ", "## ", ho_c, flags=re.M)
    role = "\n\n".join([
        "2인 대립형 취조 머더미스터리 · 범인 1명, 형사 1명 · GM 없음 · 약 75분 (취조 50분)",
        "# 1. 시스템", demote(find(plan, "8."), 1),
        "# 2. 캐릭터", demote(find(plan, "5."), 1),
        "# 3. 구성물", demote(find(plan, "9."), 1),
        "# 롤카드 ① — 공용 프롤로그", find(ho, "공용 프롤로그"),
        "# 롤카드 ② — 범인", ho_c,
        "# 롤카드 ③ — 형사", find(ho, "형사 HO"),
    ])
    pandoc(role, "markdown", out / "2_롤카드_및_시스템.docx", OLD / "2_롤카드_및_시스템.docx")

    # 엔딩 책자
    ends = [c for c in cards if c["kind"] == "ending"]
    book = ["판결이 끝난 뒤에 연다. 티비가 부른 엔딩 카드를 뒤집어 읽고, 카드가 가리키면 이 책자의 그 대목을 읽는다. 히든 엔딩이 열렸을 때만 마지막에 그녀의 이야기를 읽는다.", "",
            "# 엔딩 카드 뒷면", ""]
    for c in ends:
        book += [f"## {c['id']} 「{c['code']}」 — {c['title']}", "", f"*{c.get('cond','')}*", "", c.get("back", ""), ""]
    book += ["# 엔딩 S1 — 쿠키는 두 개", "", find(ho, "엔딩 S1"), "", "# 엔딩 S2 — 하나만 했다", "", find(ho, "엔딩 S2"), "",
             "# 그녀의 이야기", "", find(ho, "그녀의 이야기")]
    pandoc("\n".join(book), "markdown", out / "엔딩책자_스포일러.docx", OLD / "엔딩책자_스포일러.docx")

    # 정답 봉투
    pandoc(answer_sheet(d, cards, specials, plan), "markdown", out / "정답봉투_스포일러.docx", OLD / "정답봉투_스포일러.docx")

    # 기획서 전체 (스포일러) — 한 장짜리 HTML
    css = ("body{max-width:860px;margin:2em auto;padding:0 16px;font:16px/1.7 'Gowun Batang',serif;color:#2a2118;background:#f4ead6}"
           "table{border-collapse:collapse;width:100%;margin:1em 0;font-size:14px}td,th{border:1px solid #b9a27a;padding:.4em .6em;vertical-align:top}"
           "th{background:#e6d6b4}h1,h2{font-family:'Nanum Gothic Coding',monospace}")
    pandoc(plan_md, "markdown", out / "5_기획서_전체_스포일러.html",
           extra=["-s", "--metadata", "title=쿠키 살인 사건 — 기획서", "-V", f"header-includes=<style>{css}</style>"])

    # 카드 · 티비
    for src, dst in [("cards/쿠키살인사건_32장_양면인쇄.pdf", "쿠키살인사건_32장_양면인쇄.pdf"),
                     ("cards/쿠키살인사건_앞뒤_전체비교_32장.png", "쿠키살인사건_앞뒤_전체비교_32장.png"),
                     ("tv/index.html", "티비_쿠키살인사건.html")]:
        shutil.copy(ROOT / src, out / dst)
    for f in sorted(out.iterdir()):
        print(f.name, f.stat().st_size)


if __name__ == "__main__":
    main(sys.argv[1:])
