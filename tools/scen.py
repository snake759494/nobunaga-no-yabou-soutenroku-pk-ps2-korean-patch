"""시나리오(NBX 5~16) 의 '한자 칸 + 가나 읽기 칸' 쌍과 개요 문장."""
import re,sys,os
sys.path.insert(0,os.path.dirname(__file__))
from common import *
def is_hira(b):
    if len(b)%2 or not b: return False
    for i in range(0,len(b),2):
        c=b[i]<<8|b[i+1]
        if not (0x829f<=c<=0x82f1 or c==0x815b): return False
    return True
def sj_run(s,i):
    """i 에서 시작하는 SJIS 2바이트/반각 문자열 끝 (NUL 앞)"""
    j=i
    while j<len(s) and s[j]!=0:
        c=s[j]
        if (0x81<=c<=0x9f or 0xe0<=c<=0xfc) and j+1<len(s) and 0x40<=s[j+1]<=0xfc: j+=2
        elif 0x20<=c<0x7f or 0xa1<=c<=0xdf: j+=1
        else: return None
    return j
def pairs(s,lo=0x5a0,hi=None):
    """(kanji_off, cap, kanji_bytes, kana_off, kana_bytes)"""
    hi=hi or len(s); out=[]; i=lo
    while i<hi-4:
        c=s[i]
        if (0x81<=c<=0x9f or 0xe0<=c<=0xfc) and s[i-1]==0 or (i>0 and s[i-1] in (0xfe,0x01,0x02,0xff) and (0x81<=c<=0x9f or 0xe0<=c<=0xfc)):
            j=sj_run(s,i)
            if j and j>i+1:
                k=j
                while k<hi and s[k]==0: k+=1
                if k-j>=1 and k<hi:
                    m=sj_run(s,k)
                    if m and is_hira(s[k:m]) and not is_hira(s[i:j]):
                        out.append((i,k-i-1,s[i:j],k,s[k:m])); i=m; continue
        i+=1
    return out
if __name__=='__main__':
    e=elf(); s=entry(5,e); P=pairs(s)
    print(len(P))
    import collections
    print(collections.Counter(p[1] for p in P))
