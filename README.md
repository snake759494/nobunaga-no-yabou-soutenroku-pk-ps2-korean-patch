# 노부나가의 야망 창천록 with 파워업 키트 (PS2) 비공식 한글패치

PS2 일본판 **信長の野望・蒼天録 with パワーアップキット (노부나가의 야망 창천록 PK, SLPM-65455)** 비공식 한국어 패치입니다. 이 저장소에는 제작 도구와 기술 문서만 있고, 패치 파일(xdelta)은 [Releases](../../releases)에서 받을 수 있습니다. 게임 원본·일본어 원문·번역 대본은 포함하지 않습니다.

## 적용 방법
1. 아래 해시와 일치하는 **원본 `.iso`** (Redump 형식)를 준비합니다. CSO·CHD 등으로 변환한 이미지에는 적용할 수 없습니다.
2. xdeltaUI 같은 도구로 원본 ISO에 `NobunagaSoutenrokuPK_KO_v1.2.xdelta`를 적용합니다.
   - 명령줄: `xdelta3 -d -s "Nobunaga no Yabou - Soutenroku with Power-Up Kit (Japan).iso" NobunagaSoutenrokuPK_KO_v1.2.xdelta "Nobunaga no Yabou - Soutenroku with Power-Up Kit (Korean).iso"`
3. 만들어진 ISO를 PCSX2 등에서 실행합니다.

| 항목 | 값 |
| --- | --- |
| 원본 ISO 크기 | 1,231,945,728 바이트 |
| 원본 ISO MD5 | `9bd9661bb2ca97813dff0bfbaa9a012d` |
| 원본 ISO SHA-256 | `6a969867d5615b01148a6cbdce63d4513e7977d25cb2ca0a6141e8665f674f0b` |
| xdelta SHA-256 | `9a7d1cdd32b5645ce03e0f7ff311ea4be0facb155e18b7f7f5f6ea82158f68aa` |
| 결과 ISO 크기 | 1,484,273,664 바이트 |
| 결과 ISO SHA-256 | `4febc3253316aa5dfdf266e504f3a562ccaf38287354371aa752fb98802c15bb` |
| 한글판 게임 CRC (PCSX2) | `7305465F` |

## 주의
- 원본이나 다른 버전에서 만든 상태저장은 불러오지 마세요(데이터 위치가 달라 멈춥니다). 메모리 카드 세이브는 그대로 쓸 수 있습니다.
- 한글 데이터가 늘어나 결과 ISO가 원본보다 약 240MB 큽니다.
- xdelta는 압축하지 않은 형식(`-0`)입니다(약 111MB).

## 한글화 내용
- 대사·이벤트·도움말·무장 열전·가보 설명·메뉴·시나리오 데이터(무장·성·국·가문·관위·가보 이름) 전체 직접 번역
- 인명·지명은 일본어 발음 한글 표기, 칸이 좁은 곳은 2음절 합자 글리프로 처리
- 타이틀 로고, 평정·군략 명령 버튼, 계절 그림(봄·여름·가을·겨울), 합전 화면 머리띠 등 그림 글자 약 380곳 한글화
- 서울한강체(그림 글자)·나눔스퀘어 네오(게임 글꼴)

## 문서
- [CHANGELOG.md](CHANGELOG.md), [docs/BUILD.md](docs/BUILD.md), [docs/FONT_CREDITS.md](docs/FONT_CREDITS.md), [RIGHTS.md](RIGHTS.md)
