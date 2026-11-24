# -*- coding: utf-8 -*-
r"""design/tokens.json 의 값을 쓰는 곳에 넣어 준다.

    python3 design/build_tokens.py

지금은 docs/index.html 의 /*TOKENS*/ … /*\/TOKENS*/ 사이를 CSS 변수로 갈아 끼운다.
티비(tv/source.html)는 건드리지 않는다 — 티비가 기준이고, 어긋나면 tools/tvtest.py 가 잡는다.
"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OPEN, CLOSE = "/*TOKENS*/", "/*/TOKENS*/"


def load_tokens():
    """색·막 색·글꼴 값을 담은 dict. 카드 생성기도 이걸 쓴다."""
    return json.loads((HERE / "tokens.json").read_text(encoding="utf-8"))


def rgb(hex_):
    h = hex_.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def act_rgb(tk, act):
    """막 글자(K/B/G/S/E/X) → (r,g,b)."""
    return rgb(tk["color"][tk["act"][act]])


def css_block(tk):
    """바깥은 어두운 방, 읽는 면은 그 위에 놓인 종이.

    :root 는 방(티비 쪽 색), .panel 은 종이 쪽 색으로 같은 이름들을 덮는다.
    그래서 머리글·탭은 호박색으로 빛나고, 본문은 종이에 먹으로 찍힌다.
    """
    root  = ["--%s:%s" % (k, v) for k, v in tk["color"].items()]
    root += ["--%s:%s" % (k, v) for k, v in tk.get("paperColor", {}).items()]
    root += ["--%s:%s" % (o, tk["color"][n]) for o, n in tk.get("docsAlias", {}).items()]
    root.append("--mono:'Nanum Gothic Coding',monospace")
    root.append("--serif:'Gowun Batang',serif")
    panel = ["--%s:%s" % (o, tk["paperColor"][n]) for o, n in tk.get("docsPaperAlias", {}).items()]
    panel.append("color:var(--ink)")
    return ":root{%s}\n.panel{%s}" % (";".join(root), ";".join(panel))


def paper_rgb(tk, name):
    return rgb(tk["paperColor"][name])


def paper_act_rgb(tk, act):
    return rgb(tk["paperAct"][act])


def main():
    tk = load_tokens()
    target = ROOT / "docs" / "index.html"
    s = target.read_text(encoding="utf-8")
    if OPEN not in s or CLOSE not in s:
        print("docs/index.html 에 %s … %s 자리가 없다" % (OPEN, CLOSE))
        return 1
    new = re.sub(
        re.escape(OPEN) + ".*?" + re.escape(CLOSE),
        OPEN + css_block(tk) + CLOSE,
        s, count=1, flags=re.S,
    )
    if new == s:
        print("docs/index.html — 바뀐 값 없음")
        return 0
    target.write_text(new, encoding="utf-8")
    print("docs/index.html — 색 %d개를 넣었다" % len(tk["color"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
