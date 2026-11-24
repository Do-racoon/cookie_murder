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
ids=[c['id'] for c in CARDS]
# ---- PDF: A4, 3x3, 앞면 쪽 다음에 좌우를 뒤집은 뒷면 쪽 (긴 변 양면 인쇄)
cw,ch,gap=63*mm,88*mm,3*mm
mx=(A4[0]-3*cw-2*gap)/2; my=(A4[1]-3*ch-2*gap)/2
pdf=canvas.Canvas(OUT+'쿠키살인사건_%d장_양면인쇄_63x88mm.pdf'%len(ids),pagesize=A4)
pdf.setTitle('Cookie Murder Case - %d cards duplex 63x88mm'%len(ids))
sheets=[ids[i:i+9] for i in range(0,len(ids),9)]
for si,sh in enumerate(sheets):
    for side in ('front','back'):
        for n,cid in enumerate(sh):
            r,c=divmod(n,3)
            if side=='back': c=2-c
            x=mx+c*(cw+gap); y=A4[1]-my-(r+1)*ch-r*gap
            im=Image.open(R+'%s_%s.png'%(cid,side)).convert('RGB'); b=io.BytesIO(); im.save(b,'JPEG',quality=93); b.seek(0)
            from reportlab.lib.utils import ImageReader
            pdf.drawImage(ImageReader(b),x,y,cw,ch)
            pdf.setStrokeGray(0.6); pdf.setLineWidth(0.3)
            for (px,py) in ((x,y),(x+cw,y),(x,y+ch),(x+cw,y+ch)):
                pass
        pdf.setFont('Helvetica',7); pdf.setFillGray(0.35)
        pdf.drawString(mx,my-10,'Sheet %d / %d - %s - actual size 63 x 88 mm - print at 100%%'%(si+1,len(sheets),'FRONT' if side=='front' else 'BACK mirrored for long-edge duplex'))
        pdf.showPage()
pdf.save()
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
