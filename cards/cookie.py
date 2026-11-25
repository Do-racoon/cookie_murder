# -*- coding: utf-8 -*-
import json, os
from PIL import Image, ImageDraw, ImageChops
def _tk():   # 일러스트 먹색은 design/tokens.json 의 paperColor.art
    import sys; sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','design'))
    from build_tokens import load_tokens, rgb
    return rgb(load_tokens()['paperColor']['art'])
ART_FILL=_tk()

# 받아 온 과자 일러스트. 0..1 좌표의 닫힌 다각형 목록, 구멍은 evenodd.
# 원본 SVG → tools/svg2cookie.py 가 적는다.
_AP=os.path.join(os.path.dirname(os.path.abspath(__file__)),'art','cookies.json')
ART=json.load(open(_AP,encoding='utf-8')) if os.path.exists(_AP) else {}

def art_mask(name, box, ss=4):
    """일러스트를 box 크기의 마스크로. 겹친 다각형은 XOR 해서 구멍을 뚫는다."""
    a=ART[name]; n=max(8,int(box*ss))
    ox,oy=(n-a['w']*n)/2,(n-a['h']*n)/2
    m=Image.new('L',(n,n),0)
    for sub in a['paths']:
        lay=Image.new('L',(n,n),0)
        ImageDraw.Draw(lay).polygon([(ox+x*n,oy+y*n) for x,y in sub],fill=255)
        m=ImageChops.difference(m,lay)          # 0/255 두 값이니 차 = XOR
    return m.resize((int(box),int(box)),Image.LANCZOS)

def draw_cookie(im, name, cx, cy, box):
    """카드 이미지 위 (cx,cy)를 중심으로 box 크기의 과자를 찍는다."""
    if name not in ART:
        raise SystemExit('「%s」 일러스트가 없다 — SVG 를 tools/svg2cookie.py 로 넣어라' % name)
    im.paste(ART_FILL,(int(cx-box/2),int(cy-box/2)),art_mask(name,box))
