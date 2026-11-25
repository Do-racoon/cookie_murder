# -*- coding: utf-8 -*-
import os, sys, re, json, pathlib
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent

from PIL import Image, ImageDraw, ImageFont
S=2; W,H=630*S,880*S
# 색·글꼴은 design/tokens.json 하나에서 온다 — 티비가 기준이다
sys.path.insert(0, str(ROOT/'design'))
from build_tokens import load_tokens, rgb
TK=load_tokens()
_C=TK['color']
FD=str(ROOT/'design'/'fonts')+'/'
_FACE={'Regular':('serif','400'),'Medium':('serif','700'),'Bold':('serif','700'),
       'Mono':('mono','400'),'MonoBold':('mono','700'),'Digit':('digit','400')}
def F(sz,w='Regular'):
    kind,wt=_FACE[w]
    return ImageFont.truetype(FD+TK['font'][kind]['ttf'][wt], int(sz*S))
def M(sz,bold=False): return F(sz,'MonoBold' if bold else 'Mono')   # 라벨·코드 — 티비에 치는 글자
def D(sz):            return F(sz,'Digit')                          # 카드 번호 (라틴·숫자만)

# 카드는 종이다 — 빛나는 것은 티비 유리 하나뿐이다
_P=TK['paperColor']
BG=rgb(_P['paper']); LINE=rgb(_P['rule']); PANEL=rgb(_P['paper-2'])
WHITE=rgb(_P['ink']); GRAY=rgb(_P['ink-dim']); DIM=rgb(_P['rule'])
ORA=rgb(_P['bronze']); ORA2=rgb(_P['stamp']); RED=rgb(_P['stamp'])
KRAFT=rgb(_P['kraft'])
from papertex import bag, pinked
def sheet(c, base=None):
    """봉투 종이 한 장. 카드마다 결이 조금씩 다르다."""
    return bag((W,H), base or BG, seed=sum(ord(x) for x in c['id']))
_ACTNAME={'K':'현행범 현장','B':'맥주집','G':'반지하','S':'자수서','E':'엔딩','X':'특수 카드'}
ACT={k:(_ACTNAME[k], rgb(TK['paperAct'][k])) for k in _ACTNAME}

CARDS=[
 dict(id='K1',code='8ㅎ8ㅎ',title='현관 앞 CCTV',kind='photo',desc='302호 현관. 사건이 일어난 밤.',hint='위를 보라. 이 집을 보고 있던 것이 있다.'),
 dict(id='K2',code='1ㅁ5ㅈ',title='현관과 영수증',kind='photo',desc='같은 현관의 계단 쪽.',hint='바닥에 떨어진 종이 한 장.'),
 dict(id='K3',code='4ㄷ8ㅇ',title='가방 끈',kind='text',hint='이 끈은 어디서 왔나.',
      body='붉은 가방 끈. 피해자의 집에 있던 물건이 아니다 — 피의자가 가지고 들어왔다. 끈에 피해자의 피, 그리고 더 오래된 다른 피. 품에서는 밀봉된 쿠키 봉지도 나왔다. 안에 쿠키 두 개.'),
 dict(id='K4',code='3ㄴ7ㅁ',title='피해자 — 그녀',kind='photo',desc='피해자의 사건 전 사진.',hint='손에 든 것을 보라.'),
 dict(id='K5',code='9ㅊ4ㄹ',title='피의자',kind='photo',desc='체포 뒤에 찍은 사진.',hint='이마.'),
 dict(id='K6',code='7ㄱ2ㅂ',title='방 안 — 곰인형',kind='photo',desc='302호 방 안.',hint='인형과 눈을 맞춰 보라.'),
 dict(id='B1',code='4ㅈ3ㅋ',title='피해자 — 서연',kind='photo',desc='맥주집에서 찍힌 사진.',hint='가슴의 명찰, 그리고 뒤에 앉은 사람.'),
 dict(id='B2',code='5ㅇ0ㅋ',title='피해자의 방',kind='photo',desc='피해자가 숨진 방.',hint='가방에서 없어진 것.'),
 dict(id='B3',code='2ㅇ4ㅅ',title='책상 위 쿠키',kind='photo',desc='같은 방의 책상.',hint='봉지 안을 들여다보라.'),
 dict(id='B4',code='9ㅎ1ㅌ',title='국과수 촬영',kind='photo',desc='현장 감식.',hint='피가 어디에 묻었나. 어느 쪽에서 맞았나.'),
 dict(id='B5',code='5ㅂ3ㅈ',title='오락실 친구',kind='photo',desc='사건이 일어난 밤의 오락실.',hint='그녀가 서 있는 자리의 기계.'),
 dict(id='G1',code='2ㄷ3ㅌ',title='첫 번째 쿠키 살인',kind='text',hint='날짜와 시각을 보라.',
      body='여성, 20대 후반. 2022년 10월, 달림동 반지하. 손목·발목에 결박 자국, 목에 넓은 압흔 — 벨트. 침입 흔적 없음, 현관은 열려 있었다. 책상에 반으로 쪼갠 쿠키의 반쪽 — 피가 묻지 않았다. 가게 점장을 의심했으나 미제. 처음으로 "쿠키 살인"이라 불린 사건. 사망 추정은 새벽 4시 — 그날 아침, 한 경찰 가족의 발인이 있었다.'),
 dict(id='G2',code='2ㄱ0ㅇ',title='반지하의 책상',kind='text',hint='남은 쿠키를 맥주집의 것과 견주어 보라.',
      body='책상 위, 반으로 쪼갠 쿠키의 남은 반쪽 — 피가 없다. 먹은 반쪽에만 피를 댔다. 맥주집과 다르다. 찻잔이 두 개, 두 번째 잔의 입술 자국이 작다 — 손님은 아는 사람. 벽의 사진: 오락실 앞, 피해자 옆에 초커를 한 여자. 눈에 달이 있다.'),
 dict(id='G3',code='6ㄱ6ㅍ',title='그 뒤의 두 건',kind='text',hint='주기를 세어 보라.',
      body='2023년 10월, 2024년 10월. 혼자 사는 여성, 현장에 쿠키. 두 현장 모두 심하게 훼손되어 감식할 것이 남지 않았다. 경찰이 알아낸 것은 주기뿐이다 — 1년에 한 번, 10월. 그 뒤로 경찰들은 그 쿠키를 불길하다며 먹지 않는다. 2025년 10월 맥주집이 네 번째로 기록됐고, 다음은 2026년 10월로 예상했다.'),
 dict(id='S1',title='자수서 — 전부 내가 했다',kind='choice',body='내가 저지른 쿠키 살인은 네 건이다. 반지하도, 그 뒤의 두 건도, 맥주집도.\n\n마지막에 덮어서 낸다. 형사에게 그녀의 이름을 들었을 때만 낼 수 있다.',foot='자수서 · 끝까지 봉인'),
 dict(id='S2',title='자수서 — 나는 하나만 했다',kind='choice',body='내가 저지른 쿠키 살인은 한 건이다. 맥주집. 나머지는 내 것이 아니다.\n\n마지막에 덮어서 낸다. 형사에게 그녀의 이름을 들었을 때만 낼 수 있다.',foot='자수서 · 끝까지 봉인'),
 dict(id='E1',code='페이스트리',title='쿠키는 두 개',kind='ending',cond='전부 묶는다 × S1',
      back='범인이 전부를 자기 것이라 말한다. 반지하도, 그 뒤의 두 건도. 형사는 그 말이 거짓인 줄 알면서 조서에 서명한다.\n\n범인: "당신 동생 눈에는 달이 있어. 당신은 없고."\n\n병실. 그녀가 쿠키 하나를 보고 배시시 웃는다.\n\n▶ 엔딩 책자 S1을 번갈아 읽는다.'),
 dict(id='E2',code='쇼트브레드',title='하나만 했다',kind='ending',cond='동생의 이름을 적는다 × S2',
      back='범인이 맥주집 하나만 자기 것이라 말한다. 나머지는 전부 그 애의 것이라고. 형사는 동생의 이름을 적는다.\n\n병실. 동생이 눈을 떠 오빠를 본다. "일찍 왔네."\n\n▶ 엔딩 책자 S2를 번갈아 읽는다.'),
 dict(id='E3',code='진저브레드',title='문을 닫는다',kind='ending',cond='전부 묶는다 × 자수서 못 냄',
      back='형사는 쿠키 살인 네 건과 미수를 전부 이 남자의 이름 아래 적는다. 동생의 이름은 어디에도 없다.\n\n범인: "그 애 이름이 뭐였죠?"\n\n형사는 답하지 않고 문을 닫는다.'),
 dict(id='E4',code='머랭',title='다른 패턴',kind='ending',cond='손을 가른다 × 자수서 못 냄',
      back='취조가 끝났다. 누가 무엇을 했는지는 끝내 갈리지 않았다. 그녀는 열흘 뒤 퇴원했다.\n\n— 달림동 살인, 쿠키는 없었다 —\n\n달림동에서 혼자 살던 20대 여성이 숨진 채 발견됐다. 현장에 쿠키는 없었다. 10월도 아니었다. 경찰은 쿠키 살인과 무관한 사건으로 보고 있다.'),
 dict(id='E5',code='비스코티',title='맛이 없게 생겼군',kind='ending',cond='동생의 이름을 적는다 × 자수서 못 냄',
      back='범인은 끝내 이름을 듣지 못했다. 형사는 누가 시키지 않았는데 동생의 이름을 적는다. 반지하, 그리고 그 뒤의 두 건.\n\n범인: "당신은 맛이 없게 생겼군."\n\n형사: "알아. 내 피를 뽑았잖아."'),
 dict(id='E6',code='사블레',title='반쪽',kind='ending',cond='손을 가른다 × S2',
      back='형사는 두 줄 중 한 줄을 비워 둔다. 나머지는 신원 미상. 연쇄는 성립하지 않는다.\n\n범인: "빈 칸이 답이야."\n\n형사는 서류철을 덮지 않고 일어선다. 미제 서류철 위에 쿠키 반쪽.'),
 dict(id='E7',code='랑그드샤',title='서명 없음',kind='ending',cond='전부 묶는다 × S2',
      back='범인이 펜을 밀어낸다. "하나만 했다고 했어."\n\n형사는 혼자 조서를 완성한다. 네 건 전부, 이 사람의 이름 아래.\n\n법정 복도. 증인석 쪽에 보라색 머리가 앉아 있다.'),
 dict(id='E8',code='마카롱',title='두 이름',kind='ending',cond='동생의 이름을 적는다 × S1',
      back='범인은 전부 떠안으려 했고, 형사는 그 선물을 받지 않는다. 조서에 이름이 둘 적힌다.\n\n범인: "…당신, 맛이 있게 생겼군."'),
 dict(id='E9',code='튀일',title='받지 않은 편지',kind='ending',cond='손을 가른다 × S1',
      back='범인이 전부 가져가겠다는데, 형사는 두 건만 적고 나머지는 신원 미상으로 둔다.\n\n범인: "왜 안 받아?"\n\n형사: "내 것이 아니라서."\n\n티비가 꺼진다.'),
 dict(id='E10',code='마들렌',title='그녀의 이야기',kind='ending',cond='두 사람 다 3막의 질문을 맞혔다',
      back='두 사람 다 그녀에게 닿았다.\n\n엔딩 책자의 「그녀의 이야기」를 읽는다.\n\n고른 엔딩을 다 읽은 뒤에 연다.'),
]
VIO=rgb(TK['paperAct']['X']); VIO2=rgb(_P['stamp'])
def load_specials():
    """tv/source.html 의 DEFAULT_DATA 에서 특수 카드와 그 카드를 꺼내는 자리를 읽는다."""
    src=(ROOT/'tv'/'source.html').read_text(encoding='utf-8')
    D=json.loads(re.search(r'const DEFAULT_DATA\s*=\s*(\{.*?\n\});',src,re.S).group(1))
    where={}
    for cid,c in D['cards'].items():
        for i,h in enumerate(c.get('hotspots') or []):
            if h.get('card'): where[h['card']]='%s 「%s」의 %d번 지점'%(cid,c['title'].replace(' ★',''),i+1)
        if c.get('kind')=='text':
            for x in D.get('specials') or []:
                if x['id'] in (c.get('text') or ''): where[x['id']]='%s 「%s」의 본문'%(cid,c['title'])
    out=[]
    for x in D.get('specials') or []:
        out.append(dict(id=x['id'],kind='special',title=x['title'],sort=x['kind'],act=x.get('act',1),
                        only=x.get('only'),body=x['text'],
                        where=where.get(x['id'],'티비의 지시를 따른다')))
    return out


def wrap(d,text,font,maxw):
    out=[]
    for para in text.split('\n'):
        if para=='': out.append(''); continue
        line=''
        for ch in para:
            if d.textlength(line+ch,font=font)>maxw and line:
                # 줄 머리에 오면 안 되는 문장부호는 앞줄에 붙인다
                if ch in '.,)”"·!?' : line+=ch; out.append(line); line=''; continue
                out.append(line.rstrip()); line=ch.lstrip()
            else: line+=ch
        if line: out.append(line)
    return out
# 63mm 카드에서 단위 25 = 7.1pt 다. 읽히려면 9pt(=단위 32) 쯤은 돼야 한다.
BODY=[34,32,30,28,26,25,24,23,22,21,20,19,18]
CHOICE=[34,32,30,28,27,25]
LEAD=1.68
OVERFLOW=[]
def fit(d,text,maxw,maxh,sizes,lead=1.5,w='Regular',who=''):
    """가장 큰 크기부터 넣어 본다. 제일 작은 크기로도 안 들어가면 적어 둔다."""
    for sz in sizes:
        f=F(sz,w); ls=wrap(d,text,f,maxw); lh=sz*S*lead
        h=sum(lh if l else lh*0.5 for l in ls)
        if h<=maxh: return f,ls,lh
    OVERFLOW.append((who or text[:12], len(text), int(h-maxh)))
    return f,ls,lh
def para(d,x,y,ls,f,lh,fill):
    for l in ls:
        if l: d.text((x,y),l,font=f,fill=fill); y+=lh
        else: y+=lh*0.5
    return y
def X(v): return int(v*S)

def base(c):
    im=sheet(c); d=ImageDraw.Draw(im)
    d.rectangle([X(5),X(5),W-X(6),H-X(6)],outline=LINE,width=X(2))
    d.rectangle([X(34),X(43),X(174),X(47)],fill=ACT[c['id'][0]][1])
    k=c['id'][0]; act=ACT[k][0]
    # 막은 섞인 더미에서 갈라내야 하니 네모 탭으로 크게 — 머리글 줄 안에 앉힌다
    n={'K':'1막','B':'2막','G':'3막'}.get(k)
    x=X(40)
    if n:
        af=M(34,True); aw=d.textlength(n,font=af); bx=x+aw+X(24)
        d.rectangle([x,X(62),bx,X(122)],outline=WHITE,width=X(3))
        d.text(((x+bx)//2,X(92)),n,font=af,fill=WHITE,anchor='mm')
        x=bx+X(18)
    d.text((x,X(94)),act,font=F(26),fill=GRAY,anchor='lm')
    d.text((X(588),X(94)),c['id'],font=D(34),fill=WHITE,anchor='rm')
    tf=F(44,'Medium')
    if d.textlength(c['title'],font=tf)>X(548): tf=F(36,'Medium')
    d.text((X(40),X(186)),c['title'],font=tf,fill=WHITE,anchor='lm')
    d.line([X(40),X(228),X(588),X(228)],fill=LINE,width=X(2))
    return im,d
def footer(d,label,big,color=ORA2):
    d.line([X(40),X(739),X(588),X(739)],fill=LINE,width=X(2))
    d.text((X(40),X(772)),label,font=M(21),fill=GRAY,anchor='lm')
    f=M(46,True); w=d.textlength(big,font=f)
    x2,y1,y2=X(588),X(752),X(820)
    d.rectangle([x2-w-X(34),y1,x2,y2],outline=WHITE,width=X(3))
    d.text(((x2-w-X(34)+x2)//2,(y1+y2)//2),big,font=f,fill=WHITE,anchor='mm')
    d.rectangle([X(40),X(838),X(588),X(842)],fill=ORA)
def hintblock(d,hint):
    d.text((X(40),X(622)),'눈여겨볼 것',font=M(18,True),fill=WHITE,anchor='lm')
    d.line([X(188),X(622),X(588),X(622)],fill=LINE,width=X(1))
    f,ls,lh=fit(d,hint,X(548),X(84),[27,25,23,21],1.45)
    para(d,X(40),X(644),ls,f,lh,WHITE)

def front(c):
    if c['kind']=='special': return special_front(c)
    if c['kind']=='ending': return ending_code_side(c)
    im,d=base(c); k=c['kind']
    if k=='photo':
        d.rounded_rectangle([X(40),X(250),X(588),X(588)],radius=X(18),fill=PANEL)
        cx,cy=X(314),X(372)
        for r,wd in ((58,2),(37,2),(10,2)): d.ellipse([cx-X(r),cy-X(r),cx+X(r),cy+X(r)],outline=GRAY,width=X(wd))
        d.line([cx-X(118),cy,cx-X(84),cy],fill=GRAY,width=X(2)); d.line([cx+X(84),cy,cx+X(118),cy],fill=GRAY,width=X(2))
        d.text((cx,X(478)),'현장 사진',font=F(27),fill=GRAY,anchor='mm')
        f,ls,lh=fit(d,c['desc'],X(500),X(70),[23,21],1.4)
        y=X(526)
        for l in ls: d.text((cx,y),l,font=f,fill=GRAY,anchor='mm'); y+=lh
        hintblock(d,c['hint']); footer(d,'증거 식별 코드',c['code'])
    elif k=='text':
        f,ls,lh=fit(d,c['body'],X(560),X(356),BODY,LEAD,who=c['id'])
        para(d,X(36),X(244),ls,f,lh,WHITE)
        hintblock(d,c['hint']); footer(d,'증거 식별 코드',c['code'])
    elif k=='choice':
        f,ls,lh=fit(d,c['body'],X(560),X(316),CHOICE,LEAD,who=c['id'])
        para(d,X(36),X(250),ls,f,lh,WHITE)
        footer(d,c['foot'],c['id'])
    return im

def back_button(c):
    name,col=ACT[c['id'][0]]
    im=sheet(c,KRAFT); d=ImageDraw.Draw(im)
    d.rectangle([X(5),X(5),W-X(6),H-X(6)],outline=LINE,width=X(2))
    d.rectangle([X(0),X(0),W,X(96)],fill=col)
    pinked(d,0,W,X(96),X(14),col,X(26))
    d.text((X(48),X(48)),c['id'],font=D(52),fill=rgb(_P['paper']),anchor='lm')
    # 서류철 겉장에 찍힌 도장
    cx,cy,r=X(314),X(430),X(176)
    d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=WHITE,width=X(7))
    d.ellipse([cx-r+X(16),cy-r+X(16),cx+r-X(16),cy+r-X(16)],outline=WHITE,width=X(2))
    d.text((cx,cy-X(26)),name,font=F(50,'Medium'),fill=WHITE,anchor='mm')
    d.line([cx-X(84),cy+X(22),cx+X(84),cy+X(22)],fill=WHITE,width=X(2))
    d.text((cx,cy+X(62)),'쿠키 살인 사건',font=M(22),fill=WHITE,anchor='mm')
    d.text((X(314),X(754)),'티비에 코드를 넣어 연다',font=M(22),fill=GRAY,anchor='mm')
    d.rectangle([X(40),X(838),X(588),X(842)],fill=col)
    return im
GOLD=(198,170,110)
def ending_code_side(c):
    from cookie import draw_cookie
    im=sheet(c,KRAFT); d=ImageDraw.Draw(im)
    d.rectangle([X(5),X(5),W-X(6),H-X(6)],outline=LINE,width=X(2))
    d.text((X(48),X(92)),'엔딩',font=M(26),fill=GRAY,anchor='lm')
    draw_cookie(im, c['code'], X(315), X(360), X(300))
    d=ImageDraw.Draw(im)
    fz=60 if len(c['code'])<=4 else (52 if len(c['code'])==5 else 46)
    d.text((X(315),X(600)),c['code'],font=F(fz,'Medium'),fill=WHITE,anchor='mm')
    d.rectangle([X(230),X(648),X(400),X(652)],fill=GOLD)
    d.text((X(315),X(724)),'티비가 이 이름을 부르면 뒤집는다',font=F(24),fill=GRAY,anchor='mm')
    d.line([X(60),X(852),X(570),X(852)],fill=(60,64,68),width=X(2))
    for x in (60,566): d.ellipse([X(x-6),X(820),X(x+6),X(832)],fill=LINE)
    return im
def back_ending(c):
    im=sheet(c); d=ImageDraw.Draw(im)
    d.rectangle([X(5),X(5),W-X(6),H-X(6)],outline=LINE,width=X(2))
    d.rectangle([X(34),X(43),X(174),X(47)],fill=RED)
    d.text((X(40),X(92)),'엔딩 · '+c['code'],font=M(22),fill=GRAY,anchor='lm')
    d.text((X(40),X(160)),c['title'],font=F(40,'Medium'),fill=WHITE,anchor='lm')
    d.line([X(40),X(206),X(588),X(206)],fill=LINE,width=X(2))
    f,ls,lh=fit(d,c['back'],X(560),X(614),BODY,LEAD,who=c['id'])
    para(d,X(36),X(228),ls,f,lh,WHITE)
    d.rectangle([X(40),X(838),X(588),X(842)],fill=RED)
    return im
def stamp(im, text, cx, cy, r, color, angle=-11):
    """고무도장 자국 — 비스듬히 찍힌 원형 인장."""
    pad=int(r*1.5)
    lay=Image.new('RGBA',(pad*2,pad*2),(0,0,0,0)); sd=ImageDraw.Draw(lay)
    o=pad
    sd.ellipse([o-r,o-r,o+r,o+r],outline=color+(235,),width=X(6))
    sd.ellipse([o-r+X(13),o-r+X(13),o+r-X(13),o+r-X(13)],outline=color+(150,),width=X(2))
    f=F(40,'Medium'); w=sd.textlength(text,font=f)
    while w>2*r-X(46) and f.size>X(22):
        f=F(int(f.size/S)-3,'Medium'); w=sd.textlength(text,font=f)
    sd.text((o,o-X(8)),text,font=f,fill=color+(235,),anchor='mm')
    sd.line([o-w/2,o+X(26),o+w/2,o+X(26)],fill=color+(150,),width=X(2))
    sd.text((o,o+X(52)),'쿠키 살인 사건',font=M(17),fill=color+(150,),anchor='mm')
    lay=lay.rotate(angle,resample=Image.BICUBIC,center=(o,o))
    im.paste(lay,(cx-pad,cy-pad),lay)


def field(d, y, label, value, vfont=None):
    """양식 한 줄 — 라벨, 밑선, 값."""
    d.text((X(40),y),label,font=M(19),fill=GRAY,anchor='lm')
    d.line([X(40),y+X(21),X(588),y+X(21)],fill=LINE,width=X(1))
    f=vfont or F(27)
    d.text((X(166),y),value,font=f,fill=WHITE,anchor='lm')


def special_front(c):
    """증언·감정서의 앞면 — 라벨이 아니라 서류 겉장이다.

    A6 로 커지면 가운데 패널 하나는 허전하다. 1990년대 조서 겉장처럼 칸을 긋고
    항목을 적고, 한가운데 고무도장을 비스듬히 찍는다.
    """
    im=sheet(c); d=ImageDraw.Draw(im)
    col=ACT[c['id'][0]][1]
    d.rectangle([X(5),X(5),W-X(6),H-X(6)],outline=LINE,width=X(2))
    d.rectangle([X(34),X(43),X(174),X(47)],fill=col)

    d.text((X(40),X(88)),'사건 기록',font=M(22),fill=GRAY,anchor='lm')
    d.text((X(588),X(88)),c['id'],font=D(34),fill=WHITE,anchor='rm')

    # 막은 멀리서도 보여야 한다 — 분류 탭처럼 네모 안에 크게
    af=M(52,True); at='%d막'%c['act']
    aw=d.textlength(at,font=af); bx=X(40)+aw+X(34)
    d.rectangle([X(40),X(128),bx,X(208)],outline=WHITE,width=X(3))
    d.text(((X(40)+bx)//2,X(169)),at,font=af,fill=WHITE,anchor='mm')
    d.text((bx+X(22),X(172)),ACT['KBG'[c['act']-1]][0],font=F(30),fill=GRAY,anchor='lm')

    tf=F(46,'Medium')
    if d.textlength(c['title'],font=tf)>X(548): tf=F(36,'Medium')
    d.text((X(40),X(272)),c['title'],font=tf,fill=WHITE,anchor='lm')
    d.line([X(40),X(318),X(588),X(318)],fill=LINE,width=X(2))

    who='형사만 읽는다' if c.get('only')=='D' else '범인만 읽는다' if c.get('only')=='C' else '둘 다 읽는다'
    field(d,X(374),'문서 종류',c['sort'])
    field(d,X(440),'취급',who)

    stamp(im,c['sort'],X(314),X(624),X(128),WHITE)

    footer(d,'티비가 꺼내라고 할 때 뒤집는다',c['id'])
    d.rectangle([X(40),X(838),X(588),X(842)],fill=col)
    return im


def back_special(c):
    im=sheet(c); d=ImageDraw.Draw(im)
    d.rectangle([X(5),X(5),W-X(6),H-X(6)],outline=LINE,width=X(2))
    d.rectangle([X(34),X(43),X(174),X(47)],fill=VIO)
    d.text((X(40),X(92)),c['sort']+' / '+c['id'],font=M(22),fill=GRAY,anchor='lm')
    if c.get('only')=='D': d.text((X(588),X(92)),'형사만 읽는다',font=F(24,'Medium'),fill=WHITE,anchor='rm')
    d.text((X(40),X(160)),c['title'],font=F(38,'Medium'),fill=WHITE,anchor='lm')
    d.line([X(40),X(206),X(588),X(206)],fill=LINE,width=X(2))
    f,ls,lh=fit(d,c['body'],X(560),X(624),BODY,LEAD,who=c['id'])
    para(d,X(36),X(224),ls,f,lh,WHITE)
    d.rectangle([X(40),X(838),X(588),X(842)],fill=VIO)
    return im
def back(c):
    cid=c['id']
    if c['kind']=='special': return back_special(c)
    if c['kind']=='ending': return back_ending(c)
    return back_button(c)

CARDS=CARDS+load_specials()

def check_glyphs():
    """카드 글에 글꼴이 못 찍는 글자가 있으면 멈춘다 — 빈 네모로 인쇄되는 사고 방지."""
    sys.path.insert(0, str(ROOT/'design'))
    from make_fonts import check_coverage
    from make_fonts import source_strings
    used=set(source_strings(__file__))
    for c in CARDS:
        for v in c.values():
            if isinstance(v,str): used|=set(v)
    for kind in ('serif','mono'):
        for wt,f in TK['font'][kind]['ttf'].items():
            miss=check_coverage(ROOT/'design'/'fonts'/f, used)
            if miss:
                raise SystemExit('%s 에 없는 글자: %s\n  python3 design/make_fonts.py 를 다시 돌려라'
                                 % (f, ''.join(miss)))

def check_endings():
    """엔딩 카드의 쿠키 이름·제목이 티비 설계와 어긋나면 멈춘다 (옛 졼트브레드 사고 방지)."""
    src=(ROOT/'tv'/'source.html').read_text(encoding='utf-8')
    D=json.loads(re.search(r'const DEFAULT_DATA\s*=\s*(\{.*?\n\});',src,re.S).group(1))
    tv={e['id']:(e['code'],e['title']) for e in D.get('endings') or []}
    mine={c['id']:(c['code'],c['title']) for c in CARDS if c['kind']=='ending'}
    if tv!=mine:
        raise SystemExit('엔딩이 티비와 다르다\n  티비: %s\n  카드: %s'%(tv,mine))

if __name__=='__main__':
    check_endings(); check_glyphs()
    import atexit
    atexit.register(lambda: OVERFLOW and print('칸을 넘친 카드:', OVERFLOW))
    out=sys.argv[1]; os.makedirs(out,exist_ok=True)
    for c in CARDS:
        front(c).save('%s/%s_front.png'%(out,c['id'])); back(c).save('%s/%s_back.png'%(out,c['id']))
    print('ok',len(CARDS))
