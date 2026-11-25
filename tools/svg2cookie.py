# -*- coding: utf-8 -*-
"""엔딩 카드 과자 일러스트(SVG) → cards/art/cookies.json

받는 그림은 M/L/Z 다각형만으로 되어 있고, 구멍은 fill-rule="evenodd" 로 뚫는다.
그 좌표를 0..1 로 눕혀 json 에 적으면 cookie.py 가 어느 크기로든 찍는다.

한 파일에 과자 하나 (`과자-벡터-일러스트` 묶음 + <title>에서 이름을 읽는다):
    python3 -I tools/svg2cookie.py 01_진저브레드.svg 02_머랭.svg

한 파일에 여러 장 (칠한 색으로 골라 내고, 몇 번째인지로 이름을 붙인다):
    python3 -I tools/svg2cookie.py 두장.svg --fill #7e5e39 0=페이스트리 1=쇼트브레드
"""
import json, re, sys
from pathlib import Path

ROOT  = Path(__file__).resolve().parent.parent
OUT   = ROOT/'cards'/'art'/'cookies.json'
GROUP = '과자-벡터-일러스트'

def polys(d):
    """path 의 d 를 닫힌 다각형 목록으로. M/L/Z 만 받는다."""
    if re.search(r'[^MLZmlz\d\s.,-]', d): raise SystemExit('모르는 명령: %r' % d[:60])
    out = []
    for part in re.split(r'[Zz]', d):
        pts = [(float(a), float(b)) for a, b in
               re.findall(r'[MLml]?\s*(-?[\d.]+)[,\s]+(-?[\d.]+)', part)]
        if len(pts) >= 3: out.append(pts)
    return out

def unit(shape):
    """가로세로 비를 지키며 0..1 로 눕힌다."""
    xs = [p[0] for s in shape for p in s]; ys = [p[1] for s in shape for p in s]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    side = max(x1-x0, y1-y0)
    return {'w': round((x1-x0)/side, 5), 'h': round((y1-y0)/side, 5),
            'paths': [[[round((x-x0)/side, 5), round((y-y0)/side, 5)] for x, y in s] for s in shape]}

def from_group(path):
    """묶음 하나에 과자 하나. 이름은 <title>에서."""
    svg = Path(path).read_text(encoding='utf-8')
    nm = re.search(r'<title>([^<]*?)\s*엔딩 카드</title>', svg)
    if not nm: raise SystemExit('%s: 과자 이름을 못 찾았다' % path)
    i = svg.find('<g id="%s"' % GROUP)
    if i < 0: raise SystemExit('%s: %s 묶음이 없다' % (path, GROUP))
    g = svg[i:svg.find('</g>', i)]
    shape = [s for d in re.findall(r'\sd="([^"]+)"', g) for s in polys(d)]
    return [(nm.group(1), unit(shape))]

def from_fill(path, fill, picks):
    """한 파일에 여러 장. 그 색으로 칠한 path 를 차례로 세어 이름을 붙인다."""
    svg = Path(path).read_text(encoding='utf-8')
    ds = [m.group(1) for m in re.finditer(r'<path\b[^>]*\bfill="%s"[^>]*\sd="([^"]+)"' % re.escape(fill), svg)]
    if not ds: raise SystemExit('%s: %s 로 칠한 path 가 없다' % (path, fill))
    out = []
    for n, name in picks:
        if n >= len(ds): raise SystemExit('%s: %s 로 칠한 path 는 %d개뿐이다' % (path, fill, len(ds)))
        out.append((name, unit(polys(ds[n]))))
    return out

def main(argv):
    if not argv: raise SystemExit(__doc__)
    files, fill, picks = [], None, []
    it = iter(range(len(argv)))
    for k in it:
        a = argv[k]
        if a == '--fill': fill = argv[k+1]; argv[k+1] = ''
        elif re.fullmatch(r'\d+=.+', a): n, nm = a.split('=', 1); picks.append((int(n), nm))
        elif a: files.append(a)
    if fill and len(files) != 1: raise SystemExit('--fill 은 파일 하나에만 쓴다')

    art = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    got = []
    for f in files:
        got += from_fill(f, fill, picks) if fill else from_group(f)
    for nm, data in got:
        art[nm] = data
        print('%-8s 다각형 %2d개, 점 %4d개' % (nm, len(data['paths']), sum(len(s) for s in data['paths'])))
    OUT.write_text(json.dumps(art, ensure_ascii=False, indent=0, separators=(',', ':')), encoding='utf-8')
    print('→', OUT.relative_to(ROOT), OUT.stat().st_size, 'bytes,', len(art), '종')

if __name__ == '__main__': main(sys.argv[1:])
