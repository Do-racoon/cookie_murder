"""tv/source.html 하나로 티비 파일 두 개를 만든다.

- tv/index.html  : 사진을 파일 안에 넣은 판. 인터넷 없이 열린다 (제출·배포용).
- docs/tv.html   : 문서 모음의 '티비 목업' 탭이 쓰는 판. 사진은 docs/img/tv-*.jpg 를 가리킨다.

tv/source.html 은 claude.ai 티비 아티팩트와 같은 파일이다. 사진은 아티팩트에
"/_blob/<32자리 id>" 로 올라가 있고, 같은 사진이 tv/img/<id>.jpg 로 저장소에 있다.

    python3 tools/build.py
"""
import base64
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "tv" / "source.html"
IMG = ROOT / "tv" / "img"


def data_uri(path: pathlib.Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    blobs = sorted(set(re.findall(r"/_blob/([0-9a-f]{32})", src)))
    locals_ = sorted(set(re.findall(r'"(img/[A-Za-z0-9_-]+\.jpg)"', src)))
    missing = [b for b in blobs if not (IMG / f"{b}.jpg").exists()]
    missing += [f for f in locals_ if not (ROOT / "tv" / f).exists()]
    if missing:
        print("사진이 없다 — tv/img 에 먼저 넣는다:", *missing, sep="\n  ")
        return 1

    # 1) 오프라인 판
    out = src
    for b in blobs:
        out = out.replace(f"/_blob/{b}", data_uri(IMG / f"{b}.jpg"))
    for f in locals_:
        out = out.replace(f'"{f}"', '"' + data_uri(ROOT / "tv" / f) + '"')
    (ROOT / "tv" / "index.html").write_text(out, encoding="utf-8")

    # 2) 문서 모음 판
    docs_img = ROOT / "docs" / "img"
    docs_img.mkdir(parents=True, exist_ok=True)
    out = src
    for b in blobs:
        name = f"tv-{b[:8]}.jpg"
        shutil.copyfile(IMG / f"{b}.jpg", docs_img / name)
        out = out.replace(f"/_blob/{b}", f"img/{name}")
    for f in locals_:
        shutil.copyfile(ROOT / "tv" / f, docs_img / pathlib.Path(f).name)
    (ROOT / "docs" / "tv.html").write_text(out, encoding="utf-8")

    print(f"tv/index.html, docs/tv.html — 사진 {len(blobs) + len(locals_)}장")
    return 0


if __name__ == "__main__":
    sys.exit(main())
