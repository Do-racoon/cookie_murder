# -*- coding: utf-8 -*-
import math
from PIL import Image, ImageDraw, ImageFilter, ImageChops
FILL=(122,99,64); EDGE=(214,186,132); DET=(74,60,38)

def _poly_param(d,box,fn,n=360):
    pts=[]
    for i in range(n+1):
        t=i/n*2*math.pi; x,y=fn(t); pts.append((box/2+x,box/2+y))
    d.polygon(pts,fill=255)

def m_pastry(d,box):   # 페이스트리 — 하트
    def f(t):
        x=16*math.sin(t)**3
        y=-(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))
        return x*box/40, y*box/40
    _poly_param(d,box,f,240)
def m_short(d,box):    # 쇼트브레드 — 직사각 핑거
    w,h=box*0.42,box*0.78
    d.rounded_rectangle([box/2-w/2,box/2-h/2,box/2+w/2,box/2+h/2],radius=box*0.045,fill=255)
def m_ginger(d,box):   # 진저브레드 — 사람 모양
    c=box/2
    d.ellipse([c-box*0.155,box*0.08,c+box*0.155,box*0.39],fill=255)
    d.rounded_rectangle([c-box*0.165,box*0.34,c+box*0.165,box*0.68],radius=box*0.07,fill=255)
    for s in (-1,1):
        d.line([(c+s*box*0.10,box*0.44),(c+s*box*0.39,box*0.57)],fill=255,width=int(box*0.115))
        d.ellipse([c+s*box*0.39-box*0.057,box*0.57-box*0.057,c+s*box*0.39+box*0.057,box*0.57+box*0.057],fill=255)
        d.line([(c+s*box*0.075,box*0.63),(c+s*box*0.19,box*0.89)],fill=255,width=int(box*0.125))
        d.ellipse([c+s*box*0.19-box*0.062,box*0.89-box*0.062,c+s*box*0.19+box*0.062,box*0.89+box*0.062],fill=255)
def m_meringue(d,box): # 머랭 — 짜 올린 꼭지
    for wf,yf in ((0.58,0.79),(0.50,0.665),(0.41,0.545),(0.31,0.43)):
        w=box*wf; yy=box*yf
        d.ellipse([box/2-w/2,yy-box*0.145,box/2+w/2,yy+box*0.075],fill=255)
    d.polygon([(box/2-box*0.105,box*0.44),(box/2+box*0.105,box*0.44),(box/2+box*0.045,box*0.205)],fill=255)
    d.ellipse([box/2+box*0.012,box*0.195,box/2+box*0.072,box*0.255],fill=255)
def m_biscotti(d,box): # 비스코티 — 비스듬히 자른 조각
    p=[(0.09,0.345),(0.93,0.315),(0.91,0.655),(0.07,0.685)]
    d.polygon([(box*a,box*b) for a,b in p],fill=255)
def m_sable(d,box):    # 사블레 — 가장자리가 물결진 동그란 쿠키
    def f(t): r=box*0.405*(1+0.055*math.sin(16*t)); return r*math.cos(t), r*math.sin(t)
    _poly_param(d,box,f,480)

SHAPES={"페이스트리":m_pastry,"쇼트브레드":m_short,"진저브레드":m_ginger,
        "머랭":m_meringue,"비스코티":m_biscotti,"사블레":m_sable}

def details(d,box,ox,oy,name):
    X=lambda v:(v+0 ,)
    c=ox+box/2
    if name=="페이스트리":
        for k in (-1,0,1):
            d.line([(c+k*box*0.11-box*0.08,oy+box*0.33),(c+k*box*0.11+box*0.04,oy+box*0.60)],fill=DET,width=int(box*0.022))
    elif name=="쇼트브레드":
        for r in range(3):
            for col in (-1,1):
                x=c+col*box*0.075; y=oy+box*0.30+r*box*0.19
                d.ellipse([x-box*0.021,y-box*0.021,x+box*0.021,y+box*0.021],fill=DET)
    elif name=="진저브레드":
        for s in (-1,1):
            d.ellipse([c+s*box*0.055-box*0.021,oy+box*0.195,c+s*box*0.055+box*0.021,oy+box*0.237],fill=DET)
        d.arc([c-box*0.07,oy+box*0.23,c+box*0.07,oy+box*0.32],20,160,fill=DET,width=int(box*0.018))
        for i in range(2):
            y=oy+box*0.47+i*box*0.10
            d.ellipse([c-box*0.025,y-box*0.025,c+box*0.025,y+box*0.025],fill=DET)
    elif name=="머랭":
        for wf,yf in ((0.50,0.665),(0.41,0.545),(0.31,0.43)):
            w=box*wf; yy=oy+box*yf
            d.arc([c-w/2,yy-box*0.145,c+w/2,yy+box*0.075],200,340,fill=DET,width=int(box*0.018))
    elif name=="비스코티":
        for dx,dy in ((-0.24,-0.02),(-0.05,0.04),(0.16,-0.03),(0.28,0.05)):
            x=c+box*dx; y=oy+box/2+box*dy
            d.ellipse([x-box*0.045,y-box*0.028,x+box*0.045,y+box*0.028],fill=DET)
    elif name=="사블레":
        for a in range(6):
            t=a/6*2*math.pi+0.4; x=c+math.cos(t)*box*0.17; y=oy+box/2+math.sin(t)*box*0.17
            d.ellipse([x-box*0.022,y-box*0.022,x+box*0.022,y+box*0.022],fill=DET)
        d.ellipse([c-box*0.028,oy+box/2-box*0.028,c+box*0.028,oy+box/2+box*0.028],fill=DET)

def draw_cookie(im, name, cx, cy, box):
    """카드 이미지 위 (cx,cy)를 중심으로 box 크기의 쿠키를 그린다."""
    fn=SHAPES.get(name)
    if not fn: return
    m=Image.new('L',(box,box),0); md=ImageDraw.Draw(m); fn(md,box)
    m=m.filter(ImageFilter.GaussianBlur(0.6))
    ring=ImageChops.subtract(m.filter(ImageFilter.MaxFilter(max(3,int(box*0.022)//2*2+1))),m)
    ox,oy=int(cx-box/2),int(cy-box/2)
    im.paste(FILL,(ox,oy),m); im.paste(EDGE,(ox,oy),ring)
    details(ImageDraw.Draw(im),box,ox,oy,name)
