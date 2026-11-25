# -*- coding: utf-8 -*-
import sys, re, io, zipfile, shutil
import pathlib
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from cards import CARDS
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
OUT=str(HERE)+'/'; R=str(HERE)+'/png/'
# 증언·감정서는 서류다 — 63x88 에 넣으면 글자가 7pt 아래로 떨어진다. A6 쪽에 따로 앉힌다.
BIG = [c['id'] for c in CARDS if c['kind'] == 'special']
SMALL = [c['id'] for c in CARDS if c['kind'] != 'special']
ids = SMALL + BIG

from reportlab.lib.utils import ImageReader


def place(pdf, cid, side, x, y, w, h):
    im = Image.open(R + '%s_%s.png' % (cid, side)).convert('RGB')
    b = io.BytesIO(); im.save(b, 'JPEG', quality=93); b.seek(0)
    pdf.drawImage(ImageReader(b), x, y, w, h)


def lay(pdf, group, cw, ch, cols, rows, label):
    """앞면 쪽 다음에 좌우를 뒤집은 뒷면 쪽 — 긴 변 양면 인쇄용."""
    gap = 3 * mm
    mx = (A4[0] - cols * cw - (cols - 1) * gap) / 2
    my = (A4[1] - rows * ch - (rows - 1) * gap) / 2
    per = cols * rows
    sheets = [group[i:i + per] for i in range(0, len(group), per)]
    for si, sh in enumerate(sheets):
        for side in ('front', 'back'):
            for n, cid in enumerate(sh):
                r, c = divmod(n, cols)
                if side == 'back':
                    c = cols - 1 - c
                place(pdf, cid, side,
                      mx + c * (cw + gap), A4[1] - my - (r + 1) * ch - r * gap, cw, ch)
            pdf.setFont('Helvetica', 7); pdf.setFillGray(0.35)
            pdf.drawString(mx, max(my - 10, 8),
                           '%s  sheet %d/%d - actual size %.0f x %.0f mm - print at 100%%  - %s'
                           % (label, si + 1, len(sheets), cw / mm, ch / mm,
                              'FRONT' if side == 'front' else 'BACK mirrored for long-edge duplex'))
            pdf.showPage()


pdf = canvas.Canvas(OUT + '쿠키살인사건_%d장_양면인쇄.pdf' % len(ids), pagesize=A4)
pdf.setTitle('Cookie Murder Case - %d cards duplex (63x88 + A6)' % len(ids))
lay(pdf, SMALL, 63 * mm, 88 * mm, 3, 3, '63x88')
# A6 칸(105x148)에 63:88 비를 그대로 지켜 앉힌다 — 디자인을 다시 짤 필요가 없다
lay(pdf, BIG, 105 * mm, 105 * 88 / 63 * mm, 2, 2, 'A6')
pdf.save()
print('PDF — 작은 카드 %d장 + A6 %d장' % (len(SMALL), len(BIG)))

# ---- 앞뒤 전체 비교 PNG
F=lambda s:ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',s,index=1)
tw,th=252,352; cols=2; rows=(len(ids)+1)//2
Wd=60+cols*(2*tw+70); Hd=110+rows*(th+62)
ov=Image.new('RGB',(Wd,Hd),(240,238,233)); d=ImageDraw.Draw(ov)
d.text((40,28),'쿠키 살인 사건 | 카드 앞면 · 뒷면 %d장'%len(ids),font=F(30),fill=(40,40,40))
for n,cid in enumerate(ids):
    r,c=divmod(n,cols); x=40+c*(2*tw+70); y=96+r*(th+62)
    ov.paste(Image.open(R+cid+'_front.png').resize((tw,th),Image.LANCZOS),(x,y)); ov.paste(Image.open(R+cid+'_back.png').resize((tw,th),Image.LANCZOS),(x+tw+18,y))
    d.text((x,y+th+8),cid+' | 앞면 / 뒷면',font=F(20),fill=(60,60,60))
ov.save(OUT+'쿠키살인사건_앞뒤_전체비교_%d장.png'%len(ids))
print(ov.size)
