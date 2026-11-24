# -*- coding: utf-8 -*-
import os, sys, re, json, pathlib
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent

from PIL import Image, ImageDraw, ImageFont
S=2; W,H=630*S,880*S
FD='/usr/share/fonts/opentype/noto/'
def F(sz,w='Regular'): return ImageFont.truetype(FD+'NotoSansCJK-%s.ttc'%w, int(sz*S), index=1)
BG=(15,22,28); LINE=(58,70,80); PANEL=(26,36,43); WHITE=(242,238,230); GRAY=(150,162,170); DIM=(110,124,134)
ORA=(240,160,90); ORA2=(255,187,120); RED=(196,72,72)
ACT={'K':('현행범 현장',(214,128,74)),'B':('맥주집',(140,170,186)),'G':('반지하',(190,64,72)),'S':('자수서',(190,170,120)),'E':('엔딩',(190,170,120)),'X':('특수 카드',(150,140,190))}

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
 dict(id='E1',code='페이스트리',title='쿠키는 두 개',kind='ending',cond='진실 도달 + 범인이 S1을 냈다',
      back='범인이 전부를 자기 것이라 말한다. 반지하도, 그 뒤의 두 건도. 형사는 그 말이 거짓인 줄 알면서 조서에 서명한다.\n\n범인: "당신 동생 눈에는 달이 있어. 당신은 없고."\n\n▶ 엔딩 책자 S1을 번갈아 읽는다.'),
 dict(id='E2',code='쇼트브레드',title='하나만 했다',kind='ending',cond='진실 도달 + 범인이 S2를 냈다',
      back='범인이 맥주집 하나만 자기 것이라 말한다. 나머지는 전부 그 애의 것이라고. 형사는 동생의 이름을 적는다.\n\n병실. 동생이 눈을 떠 오빠를 본다. "일찍 왔네."\n\n▶ 엔딩 책자 S2를 번갈아 읽는다.'),
 dict(id='E3',code='진저브레드',title='문을 닫는다',kind='ending',cond='범인이 S를 내지 못했다 + 형사가 전부를 이 사람에게 묶었다',
      back='형사는 쿠키 살인 네 건과 미수를 전부 이 남자의 이름 아래 적는다. 동생의 이름은 어디에도 없다.\n\n범인: "그 애 이름이 뭐였죠?"\n\n형사는 답하지 않고 문을 닫는다.'),
 dict(id='E4',code='머랭',title='다른 패턴',kind='ending',cond='진실에 도달하지 못했다',
      back='취조가 끝났다. 누가 무엇을 했는지는 끝내 갈리지 않았다. 그녀는 열흘 뒤 퇴원했다.\n\n▶ 에필로그 신문 카드 「사블레」를 연다.'),
 dict(id='E5',code='비스코티',title='맛이 없게 생겼군',kind='ending',cond='진실 도달 + 범인이 S를 내지 못했다 + 형사가 스스로 동생을 기소했다',
      back='범인은 끝내 이름을 듣지 못했다. 형사는 누가 시키지 않았는데 동생의 이름을 적는다. 반지하, 그리고 그 뒤의 두 건.\n\n범인: "당신은 맛이 없게 생겼군."\n\n형사: "알아. 내 피를 뽑았잖아."'),
 dict(id='E6',code='사블레',title='에필로그 신문',kind='ending',cond='엔딩 4에서 연다',
      back='달림동 살인 — 쿠키는 없었다\n\n달림동에서 혼자 살던 20대 여성이 숨진 채 발견됐다. 현장에 쿠키는 없었다. 10월도 아니었다. 경찰은 쿠키 살인과 무관한 사건으로 보고 있다.'),
]
VIO=(168,158,205); VIO2=(198,190,230)
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

BACKSRC={'K1':9,'K2':10,'K3':11,'K4':12,'K5':13,'K6':14,'B1':15,'B2':16,'B3':17,'B4':23,'B5':24,'G1':25,'G2':26,'G3':27}

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
def fit(d,text,maxw,maxh,sizes,lead=1.5,w='Regular'):
    for sz in sizes:
        f=F(sz,w); ls=wrap(d,text,f,maxw); lh=sz*S*lead
        h=sum(lh if l else lh*0.5 for l in ls)
        if h<=maxh: return f,ls,lh
    return f,ls,lh
def para(d,x,y,ls,f,lh,fill):
    for l in ls:
        if l: d.text((x,y),l,font=f,fill=fill); y+=lh
        else: y+=lh*0.5
    return y
def X(v): return int(v*S)

def base(c):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.rectangle([X(5),X(5),W-X(6),H-X(6)],outline=LINE,width=X(2))
    d.rectangle([X(34),X(43),X(174),X(47)],fill=ORA)
    act=ACT[c['id'][0]][0]
    d.text((X(40),X(92)),'CASE FILE / '+act,font=F(24),fill=(200,206,210),anchor='lm')
    d.text((X(588),X(92)),c['id'],font=F(27,'Medium'),fill=ORA2,anchor='rm')
    tf=F(46,'Medium')
    if d.textlength(c['title'],font=tf)>X(548): tf=F(38,'Medium')
    d.text((X(40),X(172)),c['title'],font=tf,fill=WHITE,anchor='lm')
    d.line([X(40),X(220),X(588),X(220)],fill=LINE,width=X(2))
    return im,d
def footer(d,label,big,color=ORA2):
    d.line([X(40),X(739),X(588),X(739)],fill=LINE,width=X(2))
    d.text((X(40),X(770)),label,font=F(22),fill=GRAY,anchor='lm')
    d.text((X(588),X(790)),big,font=F(58,'Medium'),fill=color,anchor='rm')
    d.rectangle([X(40),X(838),X(588),X(842)],fill=ORA)
def hintblock(d,hint):
    d.text((X(40),X(622)),'HINT',font=F(19,'Medium'),fill=ORA,anchor='lm')
    d.line([X(100),X(622),X(588),X(622)],fill=(44,56,66),width=X(1))
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
        d.text((cx,X(478)),'PHOTO EVIDENCE',font=F(27),fill=(214,218,220),anchor='mm')
        f,ls,lh=fit(d,c['desc'],X(500),X(70),[23,21],1.4)
        y=X(526)
        for l in ls: d.text((cx,y),l,font=f,fill=GRAY,anchor='mm'); y+=lh
        hintblock(d,c['hint']); footer(d,'증거 식별 코드',c['code'])
    elif k=='text':
        f,ls,lh=fit(d,c['body'],X(540),X(340),[27,25,24,23,22,21,20],1.55)
        para(d,X(46),X(256),ls,f,lh,(226,226,222))
        hintblock(d,c['hint']); footer(d,'증거 식별 코드',c['code'])
    elif k=='choice':
        f,ls,lh=fit(d,c['body'],X(540),X(300),[27,25],1.6)
        para(d,X(46),X(262),ls,f,lh,(226,226,222))
        footer(d,c['foot'],c['id'])
    return im

def back_button(c):
    name,col=ACT[c['id'][0]]
    im=Image.new('RGB',(W,H),(26,29,33)); d=ImageDraw.Draw(im)
    for y in range(0,H,X(4)): d.line([0,y,W,y],fill=(24,27,31),width=1)
    d.text((X(48),X(92)),c['id'],font=F(44),fill=(150,150,146),anchor='lm')
    d.rounded_rectangle([X(76),X(204),X(566),X(676)],radius=X(60),fill=(12,13,15))
    d.rounded_rectangle([X(62),X(188),X(552),X(660)],radius=X(60),fill=(54,54,54),outline=(128,124,110),width=X(9))
    d.rounded_rectangle([X(80),X(206),X(534),X(642)],radius=X(46),outline=(92,90,82),width=X(2))
    d.ellipse([X(108),X(282),X(156),X(330)],fill=col)
    d.text((X(307),X(408)),name,font=F(52,'Medium'),fill=WHITE,anchor='mm')
    d.rectangle([X(146),X(552),X(478),X(558)],fill=col)
    d.line([X(60),X(852),X(570),X(852)],fill=(60,64,68),width=X(2))
    for x in (60,566): d.ellipse([X(x-6),X(820),X(x+6),X(832)],fill=(110,110,106))
    return im
GOLD=(198,170,110)
def ending_code_side(c):
    from cookie import draw_cookie
    im=Image.new('RGB',(W,H),(26,29,33)); d=ImageDraw.Draw(im)
    for y in range(0,H,X(4)): d.line([0,y,W,y],fill=(24,27,31),width=1)
    d.text((X(48),X(92)),'ENDING',font=F(30),fill=(150,150,146),anchor='lm')
    draw_cookie(im, c['code'], X(315), X(360), X(300))
    d=ImageDraw.Draw(im)
    fz=60 if len(c['code'])<=4 else (52 if len(c['code'])==5 else 46)
    d.text((X(315),X(600)),c['code'],font=F(fz,'Medium'),fill=WHITE,anchor='mm')
    d.rectangle([X(230),X(648),X(400),X(652)],fill=GOLD)
    d.text((X(315),X(724)),'티비가 이 이름을 부르면 뒤집는다',font=F(24),fill=(130,130,126),anchor='mm')
    d.line([X(60),X(852),X(570),X(852)],fill=(60,64,68),width=X(2))
    for x in (60,566): d.ellipse([X(x-6),X(820),X(x+6),X(832)],fill=(110,110,106))
    return im
def back_ending(c):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.rectangle([X(5),X(5),W-X(6),H-X(6)],outline=LINE,width=X(2))
    d.rectangle([X(34),X(43),X(174),X(47)],fill=RED)
    d.text((X(40),X(92)),'ENDING / '+c['code'],font=F(24),fill=(200,206,210),anchor='lm')
    d.text((X(40),X(160)),c['title'],font=F(40,'Medium'),fill=WHITE,anchor='lm')
    d.line([X(40),X(206),X(588),X(206)],fill=LINE,width=X(2))
    f,ls,lh=fit(d,c['back'],X(540),X(590),[27,26,25,24,23,22],1.6)
    para(d,X(46),X(240),ls,f,lh,(232,230,224))
    d.rectangle([X(40),X(838),X(588),X(842)],fill=RED)
    return im
def special_front(c):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.rectangle([X(5),X(5),W-X(6),H-X(6)],outline=LINE,width=X(2))
    d.rectangle([X(34),X(43),X(174),X(47)],fill=VIO)
    d.text((X(40),X(92)),'SPECIAL / '+c['sort'],font=F(24),fill=(200,206,210),anchor='lm')
    d.text((X(588),X(92)),c['id'],font=F(27,'Medium'),fill=VIO2,anchor='rm')
    tf=F(46,'Medium')
    if d.textlength(c['title'],font=tf)>X(548): tf=F(36,'Medium')
    d.text((X(40),X(172)),c['title'],font=tf,fill=WHITE,anchor='lm')
    d.line([X(40),X(220),X(588),X(220)],fill=LINE,width=X(2))
    d.rounded_rectangle([X(40),X(262),X(588),X(560)],radius=X(18),fill=PANEL)
    cx=X(314)
    d.text((cx,X(330)),'\u25a3',font=F(72),fill=VIO2,anchor='mm')
    d.text((cx,X(408)),c['sort'],font=F(40,'Medium'),fill=WHITE,anchor='mm')
    d.text((cx,X(462)),'%d막'%c['act'],font=F(24),fill=GRAY,anchor='mm')
    who='형사만 읽는다' if c.get('only')=='D' else '범인만 읽는다' if c.get('only')=='C' else '둘 다 읽는다'
    d.text((cx,X(514)),who,font=F(27,'Medium'),fill=VIO2 if c.get('only') else GRAY,anchor='mm')
    d.text((X(40),X(606)),'꺼내는 자리',font=F(19,'Medium'),fill=VIO,anchor='lm')
    d.line([X(170),X(606),X(588),X(606)],fill=(44,56,66),width=X(1))
    f,ls,lh=fit(d,c['where'],X(548),X(84),[27,25,23,21],1.45)
    para(d,X(40),X(628),ls,f,lh,WHITE)
    footer(d,'티비가 꺼내라고 할 때 뒤집는다',c['id'],VIO2)
    d.rectangle([X(40),X(838),X(588),X(842)],fill=VIO)
    return im
def back_special(c):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.rectangle([X(5),X(5),W-X(6),H-X(6)],outline=LINE,width=X(2))
    d.rectangle([X(34),X(43),X(174),X(47)],fill=VIO)
    d.text((X(40),X(92)),c['sort']+' / '+c['id'],font=F(24),fill=(200,206,210),anchor='lm')
    if c.get('only')=='D': d.text((X(588),X(92)),'형사만 읽는다',font=F(24,'Medium'),fill=VIO2,anchor='rm')
    d.text((X(40),X(160)),c['title'],font=F(38,'Medium'),fill=WHITE,anchor='lm')
    d.line([X(40),X(206),X(588),X(206)],fill=LINE,width=X(2))
    f,ls,lh=fit(d,c['body'],X(540),X(600),[25,24,23,22,21,20,19,18],1.55)
    para(d,X(46),X(236),ls,f,lh,(232,230,224))
    d.rectangle([X(40),X(838),X(588),X(842)],fill=VIO)
    return im
def back(c):
    cid=c['id']
    if cid in BACKSRC: return Image.open(str(HERE/'ext'/('c-%03d.png'%BACKSRC[cid]))).convert('RGB').resize((W,H),Image.LANCZOS)
    if c['kind']=='special': return back_special(c)
    if c['kind']=='ending': return back_ending(c)
    return back_button(c)

CARDS=CARDS+load_specials()

if __name__=='__main__':
    out=sys.argv[1]; os.makedirs(out,exist_ok=True)
    for c in CARDS:
        front(c).save('%s/%s_front.png'%(out,c['id'])); back(c).save('%s/%s_back.png'%(out,c['id']))
    print('ok',len(CARDS))
