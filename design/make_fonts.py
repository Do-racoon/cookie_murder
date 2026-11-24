# -*- coding: utf-8 -*-
"""티비가 쓰는 글꼴 셋을 받아 design/fonts/ 에 넣는다.

    python3 design/make_fonts.py

npm 의 @fontsource 패키지에서 woff2 를 받아 ttf 로 바꾼다. 고운바탕은 전체가 8MB 라
카드에 실제로 쓰이는 글자만 남겨 줄인다. 글이 바뀌면 다시 돌려야 하고, 빠진 글자가
있으면 cards.py 가 그리기 전에 멈춘다(check_coverage).
"""
import glob, pathlib, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
FONTS = HERE / "fonts"

PKGS = {
    "VT323":             ("@fontsource/vt323", False, [400]),
    "NanumGothicCoding": ("@fontsource/nanum-gothic-coding", True, [400, 700]),
    "GowunBatang":       ("@fontsource/gowun-batang", True, [400, 700]),
}

# 글꼴에 반드시 있어야 하는 글자 — 카드 본문에서 모은 것에 이것을 더한다
EXTRA = ("0123456789"
         "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
         " .,·!?\"'()[]{}<>:;/\\-—–…★▶▣■□"
         "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ"
         "「」『』※")


def source_strings(path):
    """파이썬 소스 안의 문자열 리터럴을 전부 모은다.

    "증거 식별 코드" 처럼 그리는 코드에 박힌 문구를 놓치지 않으면서, 주석과 식별자는
    끌어오지 않는다. (주석까지 넣으면 쓰지도 않는 글자가 글꼴에 섞인다.)
    """
    import ast
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    return "".join(n.value for n in ast.walk(tree)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str))


def card_chars():
    """카드가 실제로 찍는 글자 전부 — CARDS 의 글 + cards.py 에 박힌 문구."""
    sys.path.insert(0, str(HERE.parent / "cards"))
    import cards
    buf = [source_strings(HERE.parent / "cards" / "cards.py"), EXTRA]
    for c in cards.CARDS:
        for v in c.values():
            if isinstance(v, str):
                buf.append(v)
    return set("".join(buf))


def check_coverage(ttf_path, chars):
    """글꼴에 없는 글자를 돌려준다."""
    from fontTools.ttLib import TTFont
    cmap = set()
    for t in TTFont(str(ttf_path))["cmap"].tables:
        cmap |= set(t.cmap.keys())
    return sorted(c for c in chars if ord(c) not in cmap and c not in "\n\r\t")


def unpack(pkg, work):
    """패키지를 받아 풀고, 조각들이 든 폴더를 돌려준다."""
    subprocess.run(["npm", "pack", pkg], cwd=work, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tgz = glob.glob(str(work / "*.tgz"))[-1]
    shutil.unpack_archive(tgz, work / "x", format="gztar")
    return work / "x" / "package" / "files"


def pick(files, chars):
    """필요한 글자를 하나라도 담은 조각만 고른다.

    @fontsource 는 한글 글꼴을 120개 넘는 조각으로 쪼개 둔다. 한글은 korean 조각에,
    「」『』▶ 같은 기호는 번호 조각에 흩어져 있어서, 하나만 받으면 빈 네모가 나온다.
    """
    from fontTools.ttLib import TTFont
    want = {ord(c) for c in chars}
    keep = []
    for f in files:
        try:
            ft = TTFont(f)
        except Exception:
            continue
        cm = set()
        for t in ft["cmap"].tables:
            cm |= set(t.cmap.keys())
        if cm & want:
            keep.append(f)
    return keep


def merge_and_subset(files, chars, out, do_subset):
    from fontTools.ttLib import TTFont
    from fontTools.merge import Merger
    from fontTools import subset as ftsubset
    if len(files) == 1:
        f = TTFont(files[0])
    else:
        f = Merger().merge(files)
    f.flavor = None
    if do_subset:
        opts = ftsubset.Options(layout_features=["*"], notdef_outline=True,
                                drop_tables=[], passthrough_tables=False)
        sub = ftsubset.Subsetter(options=opts)
        sub.populate(text="".join(sorted(chars)))
        sub.subset(f)
    f.save(str(out))


def main():
    FONTS.mkdir(parents=True, exist_ok=True)
    chars = card_chars()
    print("카드가 쓰는 글자 %d 자" % len(chars))
    bad = 0

    for name, (pkg, do_subset, weights) in PKGS.items():
        with tempfile.TemporaryDirectory() as td:
            work = pathlib.Path(td)
            folder = unpack(pkg, work)
            for wt in weights:
                files = sorted(glob.glob(str(folder / ("*-%d-normal.woff2" % wt))))
                if not files:
                    raise SystemExit("%s 에 %d 굵기가 없다" % (pkg, wt))
                keep = pick(files, chars) or files[:1]
                out = FONTS / ("%s-%d%s.ttf" % (name, wt, "-subset" if do_subset else ""))
                merge_and_subset(keep, chars, out, do_subset)
                kb = out.stat().st_size / 1024
                missing = [] if name == "VT323" else check_coverage(out, chars)
                print("%-30s 조각 %3d개 → %6.0fKB  빠진 글자 %d"
                      % (out.name, len(keep), kb, len(missing)))
                if missing:
                    bad += 1
                    print("   →", "".join(missing[:40]))
    (FONTS / "chars.txt").write_text("".join(sorted(chars)), encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
