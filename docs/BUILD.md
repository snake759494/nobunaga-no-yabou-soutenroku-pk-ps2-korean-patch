# 빌드 방법

## 준비
- Python 3.11 이상, `numpy` `opencv-python` `Pillow`
- 원본 ISO, 글꼴(NanumSquareNeo-dEb.ttf, SeoulHangangEB.ttf)을 프로젝트 폴더에 둡니다.
- 번역 대본(`work/trans/`)은 저장소에 없습니다. 같은 형식으로 직접 만들어야 합니다.

## 구조
- 실행 파일(SLPM_654.55) 안에 UI 문자열·글꼴 코드표·NBX 차례(0x2A7370, 137개)가 있습니다.
- 게임 데이터는 `NB10.NBX` 하나에 모여 있습니다. 39번은 대사, 40번은 열전·설명, 5~16번은 시나리오, 36번은 글꼴, 나머지 다수는 TIM2 그림입니다.
- 한글은 Shift-JIS 0x889F부터 가나다 순서로 코드를 배정해 원래 한자 자리 글리프를 덮어씁니다. 바이트 순 정렬이 그대로 가나다 순이 됩니다.
- 칸이 좁은 이름은 2음절 합자 글리프(lig.txt)를 씁니다. 새 합자가 필요하면 빌드가 스스로 다시 실행됩니다.
- NBX가 원본보다 커지므로 ISO 끝으로 옮기고 디렉터리 레코드와 실행 파일의 파일 표를 고칩니다.

## 도구
| 파일 | 역할 |
| --- | --- |
| `extract_all.py` `nbx.py` `isols.py` | ISO·NBX 추출 |
| `scen.py` `script.py` `elftext.py` `sjscan.py` | 시나리오·대사·실행 파일 문자열 읽기/쓰기 |
| `make_jobs.py` `check_job.py` | 번역 작업 파일 생성·검사 |
| `fontlib.py` `glyph.py` | 글꼴 코드표·글리프 생성 |
| `tim2.py` `imgpatch.py` `relabel.py` `titles.py` `logo.py` | TIM2 그림 글자 한글화 |
| `build.py` | 전체 빌드 → 한글판 ISO |
| `emu.py` `seq.py` | PCSX2(PINE) 자동 조작·스크린샷 검수 |

## 실행
```
python work/tools/extract_all.py
python work/tools/build.py
xdelta3 -0 -e -f -s 원본.iso 한글판.iso 패치.xdelta
```
