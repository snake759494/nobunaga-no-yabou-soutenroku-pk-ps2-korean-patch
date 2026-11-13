"""NBX 39·40번 스크립트 토큰화.
코드 구간(원문 그대로 보존)과 글 구간으로 나눈다.
- 0x20 미만(0x0A 제외)·'%' 에서 코드 시작, 이후 0x20 미만(0x0A 제외)·ASCII(0x21~0x7E)·특수 인자 바이트를 계속 먹는다.
- {02}: 분류 바이트 1개 + (분류 0~11 이면 다음 바이트 >= 0x32 일 때 멤버 1개).
  분류: 0x6F~0x77, 1~99(10의 배수 제외), 0x79~0xB3 = 멤버 읽음 / 0xBF~0xD1 = 안 읽음 / 0xD3~ = 함수(인자는 뒤따르는 식).
- {01}: 'C','J' + u16 (4바이트), 'S','R' + 식, 'M','F' 단독.
- {1b}/{1a}: + 1바이트 (P/B/F/C 면 +1). {1c}: + 1바이트 ('[' 면 +1).
"""
import struct
def member_cat(x):
    return (0x6f<=x<=0x77) or (1<=x<=99 and x%10) or (0x79<=x<=0xb3 and (x-0x79)%10!=9)
def is_lead(c): return 0x81<=c<=0x9f or 0xe0<=c<=0xfc
def code_end(s,i):
    """s[i] 에서 시작하는 코드 구간의 끝"""
    n=len(s)
    while i<n:
        c=s[i]
        if c==0x02:
            i+=1
            if i<n:
                x=s[i]; i+=1
                if member_cat(x) and i<n and s[i]>=0x32 and not (s[i]==0x81 and False): i+=1
            continue
        if c==0x01:
            if i+1<n and s[i+1] in b'CJ': i+=4
            else: i+=2
            continue
        if c in (0x1b,0x1a):
            if i+1<n and s[i+1] in b'HKk': return i  # 모드 전환은 글 구간에서 처리
            i+=2
            if s[i-1] in b'PBFC': i+=1
            continue
        if c==0x1c:
            i+=2
            if s[i-1]==0x5b: i+=1
            continue
        if c<0x20 and c!=0x0a: i+=1; continue
        if 0x21<=c<=0x7e: i+=1; continue
        break
    return i
def tokens(s):
    """[(kind, bytes)] kind: 'c' 코드, 't' 글(SJIS·반각가나·\n·모드전환·공백)"""
    out=[]; i=0; n=len(s)
    while i<n:
        c=s[i]
        if (c<0x20 and c!=0x0a and not (c==0x1b and i+1<n and s[i+1] in b'HKk')) or c==0x25 or (0x21<=c<=0x7e):
            j=code_end(s,i)
            if j==i: j=i+1
            out.append(['c',s[i:j]]); i=j; continue
        j=i
        while j<n:
            c=s[j]
            if c==0x1b and j+1<n and s[j+1] in b'HKk': j+=2; continue
            if c==0x0a or c==0x20 or 0xa1<=c<=0xdf: j+=1; continue
            if is_lead(c) and j+1<n: j+=2; continue
            break
        if j==i: j=i+1
        out.append(['t',s[i:j]]); i=j
    # 인접 병합
    m=[]
    for k,v in out:
        if m and m[-1][0]==k: m[-1][1]+=v
        else: m.append([k,v])
    return m
def strings(b):
    n=struct.unpack('<H',b[:2])[0]
    o=list(struct.unpack('<%dI'%n,b[2:2+4*n]))+[len(b)]
    return [b[o[k]:o[k+1]] for k in range(n)]
def pack(strs):
    n=len(strs); hdr=2+4*n; offs=[]; p=hdr
    for s in strs: offs.append(p); p+=len(s)
    return struct.pack('<H',n)+struct.pack('<%dI'%n,*offs)+b''.join(strs)

STRUCT=(0x03,0x04,0x05,0x06)
def inline(v):
    if any(c in STRUCT for c in v): return False
    if v[:1]==b'\x01' and v[1:2] not in (b'C',): return False
    return True
HW='｡｢｣､･ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ'
import unicodedata
def kana_text(t,mode):
    """글 구간 바이트 → 사람이 읽는 일본어 (반각 가나는 모드에 따라 히라/가타)"""
    out=[]; i=0
    while i<len(t):
        c=t[i]
        if c==0x1b: mode=chr(t[i+1]); i+=2; continue
        if c==0x0a: out.append(chr(92)+'n'); i+=1; continue
        if 0xa1<=c<=0xdf:
            ch=unicodedata.normalize('NFKC',bytes([c]).decode('cp932'))
            if mode=='H' and 'ァ'<=ch<='ヶ': ch=chr(ord(ch)-0x60)
            out.append(ch); i+=1; continue
        if is_lead(c): out.append(t[i:i+2].decode('cp932','replace')); i+=2; continue
        out.append(chr(c)); i+=1
    s=''.join(out)
    # 반각 탁점 결합
    s=unicodedata.normalize('NFC',s.replace('゛','゙').replace('゜','゚'))
    return s,mode
def units(s,mode='H'):
    """[(kind,...)]: ('c',bytes) 구조 코드 / ('u',[parts], jp) 번역 단위. parts: ('t',bytes)|('c',bytes)"""
    T=tokens(s); out=[]; cur=[]
    def flush():
        if cur:
            if any(k=='t' and v.strip(b' \n\x1bHKk') for k,v in cur):
                out.append(('u',list(cur)))
            else:
                for k,v in cur: out.append(('c',v))
            cur.clear()
    for k,v in T:
        if k=='t' or inline(v): cur.append((k,v))
        else: flush(); out.append(('c',v))
    flush()
    res=[]
    for x in out:
        if x[0]=='u':
            jp=[]
            for k,v in x[1]:
                if k=='t': t,mode=kana_text(v,mode); jp.append(t)
                else: jp.append('<%s>'%v.hex())
            res.append(('u',x[1],''.join(jp)))
        else: res.append(x)
    return res
