"""푸시 전에 이것 하나만 돌린다. 하나라도 실패하면 종료코드 1.

    python3 tools/check.py [--base <rev>]     # 기본 base: origin/main

1. build.py 를 돌린 뒤 tv/index.html · docs/tv.html 이 커밋된 것과 같은가
2. tvtest.py · docstest.py · synctest.py
3. consistency.py --base <rev>
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable


def run(name, cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
    ok = r.returncode == 0
    print(("OK   " if ok else "FAIL ") + name + "  " + tail[0])
    if not ok:
        for line in (r.stdout + r.stderr).splitlines():
            if line.startswith("FAIL") or "Error" in line:
                print("       " + line)
    return ok


def main(argv) -> int:
    base = argv[argv.index("--base") + 1] if "--base" in argv else "origin/main"
    res = []
    res.append(run("build.py", [PY, "tools/build.py"]))
    d = subprocess.run(["git", "diff", "--quiet", "--", "tv/index.html", "docs/tv.html"], cwd=ROOT)
    ok = d.returncode == 0
    print(("OK   " if ok else "FAIL ") + "빌드한 티비가 커밋된 것과 같다"
          + ("" if ok else " — tv/source.html 을 고쳤으면 build.py 를 돌리고 같이 커밋하라"))
    res.append(ok)
    res.append(run("tvtest.py", [PY, "tools/tvtest.py"]))
    res.append(run("docstest.py", [PY, "tools/docstest.py"]))
    res.append(run("synctest.py", [PY, "tools/synctest.py"]))
    args = [PY, "tools/consistency.py"] + (["--base", base] if base else [])
    res.append(run("consistency.py", args))
    print(f"\n검사 {sum(res)}/{len(res)} 통과")
    return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
