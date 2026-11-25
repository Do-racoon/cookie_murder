# -*- coding: utf-8 -*-
"""엔딩 카드 과자 일러스트(SVG) → cards/art/cookies.json

쓰는 법:  python3 -I tools/svg2cookie.py <그림.svg> [...]
받는 SVG는 `과자-벡터-일러스트` 묶음 하나에 M/L/Z 만으로 된 path 가 들어 있고,
구멍은 fill-rule="evenodd" 로 뚫는다. 그 좌표를 0..1 로 눕혀 json 에 적는다.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT/'cards'/'art'/'cookies.json'
GROUP = '과자-벡터-일러스트'

def group_of(svg):
    i = svg.find('<g id="%s"' % GROUP)
    if i < 0: raise SystemExit('%s 묶음이 없다' % GROUP)
    j = svg.find('</g>', i)
    return svg[i:j]

def subpaths(g):
    """path 의 d 를 닫힌 다각형 목록으로. M/L/Z 만 받는다."""
    out = []
    for d in re.findall(r'\sd="([^"]+)"', g):
        if re.search(r'[^MLZmlz\d\s.,-]', d): raise SystemExit('모르는 명령: %r' % d)
        for part in re.split(r'[Zz]', d):
            pts = [(float(a), float(b)) for a, b in
                   re.findall(r'[MLml]\s*(-?[\d.]+)[,\s]+(-?[\d.]+)', part)]
            if len(pts) >= 3: out.append(pts)
    return out

def convert(path):
    svg = Path(path).read_text(encoding='utf-8')
    name = re.search(r'<title>([^<]*?)\s*엔딩 카드</title>', svg)
    if not name: raise SystemExit('%s: 과자 이름을 못 찾았다' % path)
    g = group_of(svg)
    polys = subpaths(g)
    xs = [p[0] for s in polys for p in s]; ys = [p[1] for s in polys for p in s]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    side = max(x1-x0, y1-y0)                      # 가로세로 비를 지킨다
    return name.group(1), {
        'w': round((x1-x0)/side, 5), 'h': round((y1-y0)/side, 5),
        'paths': [[[round((x-x0)/side, 5), round((y-y0)/side, 5)] for x, y in s] for s in polys],
    }

def main(argv):
    if not argv: raise SystemExit(__doc__)
    art = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    for p in argv:
        nm, data = convert(p)
        art[nm] = data
        print('%-8s 다각형 %2d개, 점 %4d개' % (nm, len(data['paths']), sum(len(s) for s in data['paths'])))
    OUT.write_text(json.dumps(art, ensure_ascii=False, indent=0, separators=(',', ':')), encoding='utf-8')
    print('→', OUT.relative_to(ROOT), OUT.stat().st_size, 'bytes')

if __name__ == '__main__': main(sys.argv[1:])
