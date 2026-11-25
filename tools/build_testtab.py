# -*- coding: utf-8 -*-
"""문서 모음의 "테스트 코드" 탭을 티비 설계에서 다시 그린다.

    python3 tools/build_testtab.py

손으로 적어 두면 설계가 바뀔 때마다 어긋난다(실제로 어긋났다). 카드·코드·지시를
tv/source.html 에서 뽑아 docs/index.html 의 <!--TESTTAB--> … <!--/TESTTAB--> 사이를 채운다.
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN, CLOSE = "<!--TESTTAB-->", "<!--/TESTTAB-->"
ACTS = [("K", "1막 — 현행범 현장 (처음부터 열림)"),
        ("B", "2막 — 맥주집 (1막 질문을 맞히면)"),
        ("G", "3막 — 반지하 (2막 질문을 맞히면)")]
KIND = {"photo": "사진", "text": "글", "choice": "선택"}


def orders(card):
    """카드 본문과 사진 지점에 붙은 ▶ · ▣ 지시를 모은다."""
    out = []
    for m in re.finditer(r"[▶▣][^▶▣]*", card.get("text") or ""):
        out.append(m.group(0).strip())
    for h in card.get("hotspots") or []:
        for m in re.finditer(r"[▶▣][^▶▣]*", h.get("hint") or ""):
            out.append(m.group(0).strip())
    return out


def esc(t):
    return html.escape(t, quote=False)


def table(rows, head):
    th = "".join("<th>%s</th>" % esc(h) for h in head)
    tr = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return '<div class="tw"><table><tr>%s</tr>%s</table></div>' % (th, tr)


def main():
    src = (ROOT / "tv" / "source.html").read_text(encoding="utf-8")
    D = json.loads(re.search(r"const DEFAULT_DATA\s*=\s*(\{.*?\n\});", src, re.S).group(1))
    out = []
    for letter, heading in ACTS:
        rows = []
        for cid, c in D["cards"].items():
            if not cid.startswith(letter):
                continue
            rows.append([
                esc("%s · %s" % (cid, c["title"].replace(" ★", ""))),
                "<b>%s</b>" % esc(c.get("code", "")),
                KIND.get(c.get("kind"), c.get("kind", "")),
                esc(" · ".join(o.lstrip("▶▣ ") for o in orders(c))),
            ])
        out.append("<h2>%s</h2>%s" % (esc(heading), table(rows, ["카드", "코드", "종류", "▶ 지시"])))

    sp = D.get("specials") or []
    if sp:
        where = {}
        for cid, c in D["cards"].items():
            for i, h in enumerate(c.get("hotspots") or []):
                if h.get("card"):
                    where[h["card"]] = "%s 사진의 %d번 지점" % (cid, i + 1)
            for x in sp:
                if x["id"] in (c.get("text") or ""):
                    where[x["id"]] = "%s 본문의 ▣ 지시" % cid
        rows = [[esc("%s · %s" % (x["id"], x["title"])), esc(x["kind"]),
                 esc("%d막" % x.get("act", 1)),
                 esc(where.get(x["id"], "")),
                 esc("형사만" if x.get("only") == "D" else "범인만" if x.get("only") == "C" else "둘 다")]
                for x in sp]
        out.append("<h2>특수 카드 — 코드가 없다. 사진 지점을 눌러 꺼낸다</h2>"
                   + table(rows, ["카드", "종류", "막", "꺼내는 자리", "읽는 사람"])
                   + '<p class="mut">증언·국과수 감정서는 서류라 다른 카드보다 크다 — A6(105×148mm).'
                     ' 그녀의 일기장은 카드가 아니라 형사 핸드아웃의 비밀 ③ 이다.</p>')

    body = "\n".join(out)
    p = ROOT / "docs" / "index.html"
    s = p.read_text(encoding="utf-8")
    if OPEN not in s:
        print("docs/index.html 에 %s 자리가 없다" % OPEN)
        return 1
    new = re.sub(re.escape(OPEN) + ".*?" + re.escape(CLOSE), OPEN + body + CLOSE, s, count=1, flags=re.S)
    if new == s:
        print("테스트 코드 탭 — 바뀐 것 없음")
        return 0
    p.write_text(new, encoding="utf-8")
    print("테스트 코드 탭을 다시 그렸다 — 막 %d개 + 특수 %d장" % (len(ACTS), len(sp)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
