"""문서끼리 어긋남을 본다 — 옛 규칙 문구, 카드 수, 엔딩 수, 막의 질문 이름표, 설계 버전.

    python3 tools/consistency.py [--base <rev>]

--base 를 주면 그 판의 tv/source.html 과 DEFAULT_DATA 를 비교한다.
설계가 바뀌었는데 version 이 오르지 않았으면 FAIL. 기본 base 는 origin/main.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# 옛 규칙. 다시 나타나면 안 되는 문구 — 새로 버린 규칙이 생기면 여기에 더한다.
BANNED = [
    "이름을 들었을 때만",
    "4막 미도달",
    "발인 날 사라진 사람",
    "엔딩 카드 6",
    "취조서 세 칸",
    "22장 — 현장 카드",
    "카드 31장",       # 2026-11-26 사진 개편으로 30장
    "31장 —",
    "2022년", "2023년", "2024년", "2025년", "2026년",   # 2026-11-26 연도 7년 앞당김
    "2022.10", "2025.10", "2026.1",
    "달림국밥",
    "점수",            # 2026-11-25 점수 폐지
    "취조 45분",
    "타이머(45분)",
    "45분에 맞",
    "읽는 45분",
    "약 70분",
]

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(ok)
    print(("OK   " if ok else "FAIL ") + name + ("" if ok or not detail else f" — {detail}"))


def data_of(src: str) -> dict:
    return json.loads(re.search(r"const DEFAULT_DATA\s*=\s*(\{.*?\n\});", src, re.S).group(1))


def main(argv) -> int:
    base = "origin/main"
    if "--base" in argv:
        base = argv[argv.index("--base") + 1]

    tv_src = (ROOT / "tv" / "source.html").read_text(encoding="utf-8")
    plan = (ROOT / "text" / "기획서.md").read_text(encoding="utf-8")
    hub = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    d = data_of(tv_src)

    # 1. 금지 문구
    files = sorted((ROOT / "text").glob("*.md")) + [ROOT / "docs" / "index.html", ROOT / "tv" / "source.html",
                                                ROOT / "cards" / "cards.py"]
    for f in files:
        t = f.read_text(encoding="utf-8")
        hits = [b for b in BANNED if b in t]
        check(f"옛 규칙 문구가 없다 — {f.relative_to(ROOT)}", not hits, ", ".join(hits))

    # 2. 카드 총수
    n = len(d["cards"]) + len(d["endings"]) + len(d.get("specials", [])) + 2
    m = re.search(r"카드는 모두 (\d+)장", plan)
    check(f"기획서의 카드 총수가 티비 설계와 같다 ({n})", bool(m) and int(m.group(1)) == n,
          m.group(1) if m else "\"카드는 모두 N장\" 이 없다")
    m = re.search(r"(\d+)장 — 현장 카드", hub)
    check(f"문서 모음 구성의 카드 총수가 티비 설계와 같다 ({n})", bool(m) and int(m.group(1)) == n,
          m.group(1) if m else "\"N장 — 현장 카드\" 가 없다")
    m = re.search(r"카드 (\d+)장 · 종이 핸드아웃", hub)
    check(f"문서 모음 소개서의 카드 수가 같다 ({n})", bool(m) and int(m.group(1)) == n,
          m.group(1) if m else "소개서 구성 줄이 없다")

    # 3. 엔딩 수
    m = re.search(r"^\| 엔딩 카드 \| (\d+) \|", plan, re.M)
    e = len(d["endings"])
    check(f"기획서 9절 엔딩 카드 수가 티비 endings 와 같다 ({e})", bool(m) and int(m.group(1)) == e,
          m.group(1) if m else "9절 엔딩 카드 행이 없다")

    # 4. 막의 질문 이름표
    last = [x for x in d["memory"] if x.get("from") == 3]
    keys = [q.get("key") for x in last for q in x.get("asks", [])]
    check("3막 질문에 herReason·bridge 이름표가 있다", "herReason" in keys and "bridge" in keys, keys)

    # 5. 설계 버전
    try:
        old_src = subprocess.run(["git", "-C", str(ROOT), "show", f"{base}:tv/source.html"],
                                 capture_output=True, text=True, check=True).stdout
        old = data_of(old_src)
    except Exception:
        print(f"SKIP 설계 버전 — 비교할 판({base})을 읽지 못했다")
    else:
        a = {k: v for k, v in old.items() if k != "version"}
        b = {k: v for k, v in d.items() if k != "version"}
        if a == b:
            check(f"설계가 {base} 와 같다 — version 그대로 둬도 된다", d["version"] >= old["version"],
                  f"{old['version']} → {d['version']}")
        else:
            check(f"설계가 {base} 와 달라졌으니 version 이 올랐다",
                  d["version"] > old["version"], f"{old['version']} → {d['version']} (올려라)")

    print(f"\n{sum(RESULTS)}/{len(RESULTS)} 통과")
    return 0 if all(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
