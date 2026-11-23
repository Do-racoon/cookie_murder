# 쿠키 살인 사건

2인 대립형 취조 머더미스터리 (범인 vs 형사) · GM 없음 · 약 70분 · 카드 22장
「두 사람의 알리바이」 2인 머미 공모전 출품작.

## 폴더

| 경로 | 내용 |
|---|---|
| `tv/index.html` | 티비 — 테이블 가운데 한 대를 둘이 같이 보는 웹페이지. 사진이 파일 안에 들어 있어 인터넷 없이 열린다 |
| `tv/source.html` | 티비 원본 (아티팩트와 같은 파일). 고친 뒤 `python3 tools/build.py`로 `tv/index.html`·`docs/tv.html`을 만든다 |
| `tv/img/` | 티비 사진 원본 |
| `tools/build.py` | 티비 파일을 만드는 스크립트 |
| `cards/` | 카드 22장 인쇄본 — 양면 PDF(63×88mm, A4 3×3 여섯 쪽) · 앞뒤 전체 비교 그림 · 낱장 PNG 44개 · 그림을 만든 파이썬 파일(`cards.py` `cookie.py` `make_pdf.py`) |
| `docs/` | 문서 모음 — 소개서·기획서·타임라인·핸드아웃·카드·룰북·테스트 코드·관계도·그림·티비 목업. `docs/index.html`을 연다 |
| `text/` | 핸드아웃과 기획서 원문 (Markdown) |
| `submission-2026-11-22/` | 11/22 공모전에 실제로 낸 파일 11개 그대로 — 소개서·롤카드·규칙서·정답봉투·엔딩책자(docx), 기획서 전체(html), 티비(html), 카드 인쇄 PDF와 시안 그림. 이후 수정 미반영 |

## 원본

여러 세션이 `main` 하나를 같이 고친다. 순서와 규칙은 `CLAUDE.md`에 있다.

- 티비: https://claude.ai/artifact/RkudTwWyMKxMF91p3AChwb
- 문서 모음: https://claude.ai/artifact/4HW4bDiY5ph6icqAFJB98o
- 기획서: https://claude.ai/artifact/6Y9qw651X7NJzR1vhJgRUC
- 핸드아웃: https://claude.ai/artifact/AEMKyaaiZ69Zb7jWomtaBv

## GitHub Pages

Settings → Pages → Branch `main`, 폴더 `/ (root)`. 그러면 `/tv/`가 티비, `/docs/`가 문서 모음이 된다.
