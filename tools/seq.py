"""python seq.py 이름 [버튼|초]... → 각 버튼 뒤 스크린샷 → work/shots/이름.png 시트"""
import sys,time,os; sys.path.insert(0,os.path.dirname(__file__)); import emu
from PIL import Image
name=sys.argv[1]; ims=[]
def shot():
    for _ in range(3):
        try:
            p=emu.savewait(9)
            if p:
                import io; return Image.open(io.BytesIO(emu.member(p,'Screenshot.png'))).convert('RGB')
        except Exception as ex: time.sleep(1)
for a in sys.argv[2:]:
    try: time.sleep(float(a)); continue
    except ValueError: pass
    if a=='@': im=shot(); ims.append(im) if im else None; continue
    emu.press(a,200); time.sleep(1.5); im=shot()
    if im: ims.append(im)
W=4; S=Image.new('RGB',(320*W,240*((len(ims)+W-1)//W)))
for n,im in enumerate(ims): S.paste(im.resize((320,240)),((n%W)*320,(n//W)*240))
S.save(os.path.join(emu.R,'work','shots',name+'.png')); print(len(ims))
