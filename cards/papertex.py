# -*- coding: utf-8 -*-
"""빵봉투·종이봉투의 결을 카드 바탕에 입힌다.

종이 섬유의 자잘한 얼룩, 봉투를 접었던 세로 자국, 가장자리로 갈수록 어두워지는 결.
인쇄해도 살아남게 아주 옅게만 넣는다 — 눈에 띄면 그건 노이즈지 종이가 아니다.
"""
import random
from PIL import Image, ImageDraw, ImageFilter, ImageChops


def bag(size, base, seed=7):
    """base 색의 봉투 종이 한 장을 만든다. size=(w,h)."""
    w, h = size
    im = Image.new("RGB", size, base)
    rnd = random.Random(seed)

    # 1) 종이 섬유 — 고운 얼룩
    small = Image.new("L", (w // 3, h // 3))
    small.putdata([rnd.randint(104, 150) for _ in range(small.width * small.height)])
    grain = small.resize(size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.6))
    im = ImageChops.overlay(im, Image.merge("RGB", (grain, grain, grain)))
    im = Image.blend(Image.new("RGB", size, base), im, 0.30)

    # 2) 섬유 부스러기 — 아주 드문 짙은 점
    d = ImageDraw.Draw(im)
    for _ in range((w * h) // 9000):
        x, y = rnd.randrange(w), rnd.randrange(h)
        v = rnd.randint(14, 30)
        d.point((x, y), fill=tuple(max(0, c - v) for c in base))

    # 3) 접힌 자국 — 봉투를 폈을 때 남는 세로선
    shade = Image.new("L", size, 0)
    sd = ImageDraw.Draw(shade)
    for fx in (0.30, 0.68):
        x = int(w * fx)
        sd.line([(x, 0), (x, h)], fill=26, width=max(1, w // 300))
        sd.line([(x + max(1, w // 210), 0), (x + max(1, w // 210), h)], fill=12, width=1)
    shade = shade.filter(ImageFilter.GaussianBlur(w / 160))
    im = ImageChops.subtract(im, Image.merge("RGB", (shade, shade, shade)))

    # 4) 가장자리 — 손 타는 자리가 조금 어둡다
    vig = Image.new("L", size, 0)
    vd = ImageDraw.Draw(vig)
    m = int(min(w, h) * 0.10)
    vd.rectangle([m, m, w - m, h - m], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(m * 0.9))
    dark = Image.new("RGB", size, tuple(max(0, c - 16) for c in base))
    return Image.composite(im, dark, vig)


def pinked(d, x1, x2, y, depth, color, step):
    """빵봉투 윗단처럼 톱니로 자른 선."""
    pts, x, up = [], x1, True
    while x < x2:
        pts.append((x, y if up else y + depth)); up = not up; x += step
    pts.append((x2, y))
    d.line(pts, fill=color, width=max(1, depth // 6), joint="curve")
