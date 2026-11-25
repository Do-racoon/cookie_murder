# -*- coding: utf-8 -*-
"""문서가 설계와 어긋났는지 본다.

    python3 tools/synctest.py

원본은 tv/source.html(설계)과 cards/cards.py(카드)다. 문서 모음·기획서·핸드아웃이
거기서 벗어나면 FAIL. 손으로 적은 숫자와 카드 이름은 반드시 어긋나므로 검사로 묶는다.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(ok)
    print(("OK   " if ok else "FAIL ") + name + (" — " + str(detail) if detail else ""))


def tv_data():
    s = (ROOT / "tv" / "source.html").read_text(encoding="utf-8")
    return json.loads(re.search(r"const DEFAULT_DATA\s*=\s*(\{.*?\n\});", s, re.S).group(1))


def main():
    sys.path.insert(0, str(ROOT / "cards"))
    import cards

    D = tv_data()
    specials = [x["id"] for x in D.get("specials") or []]
    endings = D.get("endings") or []
    n_cards = len(cards.CARDS)
    n_small = len([c for c in cards.CARDS if c["kind"] != "special"])
    n_big = len(specials)

    docs = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    plan = (ROOT / "text" / "기획서.md").read_text(encoding="utf-8")
    hand = (ROOT / "text" / "핸드아웃.md").read_text(encoding="utf-8")
    papers = {"문서 모음": docs, "기획서": plan, "핸드아웃": hand}

    # 1) 없어진 카드 번호가 아직 적혀 있나
    gone = [i for i in ["X1"] if i not in specials]
    for name, txt in papers.items():
        found = [g for g in gone if re.search(r"\b%s\b" % g, txt)]
        check("%s에 없어진 카드 번호가 없다" % name, not found, found)

    # 2) 살아 있는 특수 카드가 문서 모음에 다 적혀 있나
    missing = [i for i in specials if i not in docs]
    check("문서 모음에 특수 카드가 다 적혀 있다", not missing, missing)

    # 3) 엔딩 쿠키 이름이 문서와 같나
    for name, txt in (("문서 모음", docs), ("기획서", plan)):
        off = [e["code"] for e in endings if e["code"] not in txt]
        check("%s의 엔딩 쿠키 이름이 티비와 같다" % name, not off, off)

    # 4) 장수
    check("기획서의 카드 장수가 %d장이다" % n_cards, "%d장" % n_cards in plan)
    check("문서 모음의 카드 장수가 %d장이다" % n_cards, "카드 %d장" % n_cards in docs)
    check("기획서가 두 크기를 적고 있다 (%d + %d)" % (n_small, n_big),
          "63×88" in plan and "A6" in plan)

    # 5) 티비에서 뗀 지시가 문서에 남아 있나
    g3 = D["cards"]["G3"]["text"]
    if "비밀 ③" not in g3:
        stale = [n for n, t in papers.items()
                 if re.search(r"G3[^\n]{0,80}비밀 ③", t) or re.search(r"그 뒤의 두 건[^\n]{0,80}비밀 ③", t)]
        check("G3 에서 뗀 비밀 ③ 지시가 문서에 남아 있지 않다", not stale, stale)

    # 6) 카드 코드가 문서 모음의 테스트 코드 탭과 같나
    codes = {c["code"] for c in cards.CARDS if c.get("code")}
    off = sorted(c for c in codes if c not in docs)
    check("문서 모음에 카드 코드가 다 적혀 있다", not off, off)

    print()
    bad = RESULTS.count(False)
    print("%d/%d 통과" % (len(RESULTS) - bad, len(RESULTS)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
