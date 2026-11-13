import os,sys
sys.path.insert(0,os.path.dirname(__file__))
from common import W
T=os.path.join(W,'trans'); J=os.path.join(T,'jobs')
def lines(n): return [l for l in open(os.path.join(T,n),encoding='utf-8') if l.strip()]
def split(name,L,size):
    k=0
    for i in range(0,len(L),size):
        open(os.path.join(J,f'{name}_{k:02d}_in.tsv'),'w',encoding='utf-8',newline=chr(10)).writelines(L[i:i+size]); k+=1
    return k
print(split('e39',lines('src_e39.tsv'),620))
print(split('e40',lines('src_e40.tsv'),520))
print(split('elf',lines('src_elf.tsv'),1800))
print(split('ovl',lines('src_ovl.tsv'),700))
print(split('scen',lines('src_scen_terms.tsv')+lines('src_scen_desc.tsv'),900))
