"""번역 결과 검증: python check_job.py 입력.tsv 출력.tsv
입력: key \t cap \t 일본어   /  출력: key \t 한국어
- 키 누락/중복, 자리표시 <hex> 일치, 가나·한자 잔존, 허용 문자, 용량(바이트), 줄 폭"""
import sys,re,os,unicodedata
HERE=os.path.dirname(os.path.abspath(__file__))
KEEP=open(os.path.join(HERE,'..','trans','font_keep.txt'),encoding='utf-8').read()
PH=re.compile(r'<[0-9a-f]+>')
def width(line):
    w=0; line2=PH.sub('',line); w+=4*len(PH.findall(line))
    for ch in line2: w+= 1 if ord(ch)>=0x80 else 0.5
    return w
def nbytes(s):
    n=0
    for ch in PH.sub('',s):
        n+= 2 if ord(ch)>=0x80 else 1
    return n+sum(len(p)//2-1 for p in PH.findall(s))
def bad_chars(s,jp=''):
    out=set()
    for ch in PH.sub('',s.replace('\n','')):
        o=ord(ch)
        if 0xac00<=o<=0xd7a3: continue
        if 0x20<=o<0x7f and (ch not in '%\<>' or (ch=='%' and '%' in jp)): continue
        if ch in KEEP and not ('ぁ'<=ch<='ヶ'): continue
        out.add(ch)
    return out
def load(p,n):
    d={}
    for l in open(p,encoding='utf-8'):
        l=l.rstrip('\r\n')
        if not l: continue
        x=l.replace(chr(92)+'n',chr(10)).split('\t')
        if len(x)<n: x+=['']*(n-len(x))
        d.setdefault(x[0],[]).append(x[1:])
    return d
def main(a,b,quiet=False):
    I=load(a,3); O=load(b,2); err=[]; warn=[]
    for k,v in I.items():
        cap,jp=int(v[0][0]),v[0][1]
        if k not in O: err.append((k,'누락')); continue
        if len(O[k])>1: err.append((k,'중복'))
        ko=O[k][0][0]
        if sorted(PH.findall(jp))!=sorted(PH.findall(ko)): err.append((k,'자리표시 불일치 %s / %s'%(PH.findall(jp),PH.findall(ko))))
        bc=bad_chars(ko,jp)
        if bc: err.append((k,'허용 안 되는 문자 '+''.join(sorted(bc))))
        if not ko.strip(): err.append((k,'빈 번역'))
        if k[:2] in ('E:','S:','G:','T:','D:') and nbytes(ko)>cap: err.append((k,'용량 초과 %d>%d'%(nbytes(ko),cap)))
        if k.startswith('39:'):
            L=ko.split('\n')
            if len(L)>max(4,jp.count('\n')+1): warn.append((k,'줄 수 %d'%len(L)))
            for l in L:
                if width(l)>20: warn.append((k,'줄 폭 %.1f > 20: %s'%(width(l),l)))
        if k.startswith('40:') and jp.count('\n')>=3:
            if width(ko.replace('\n',''))>70: warn.append((k,'열전 길이 %.1f > 70'%width(ko.replace('\n',''))))
    for k in O:
        if k not in I: err.append((k,'입력에 없는 키'))
    if not quiet:
        for k,m in err: print('오류',k,m)
        for k,m in warn: print('경고',k,m)
        print('오류 %d  경고 %d  (전체 %d)'%(len(err),len(warn),len(I)))
    return err,warn
if __name__=='__main__': main(sys.argv[1],sys.argv[2])
