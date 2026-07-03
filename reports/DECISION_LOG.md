# MAPZ DECISION_LOG — 무인 자동 결정 기록

모든 모호성은 MAPZ_AUTOPILOT.md §C 결정 규칙으로 해소하며, 그 근거를 여기 남긴다.

## Phase 0 — 환경 셋업

| # | 상황 | 결정 | 근거(§C) |
|---|---|---|---|
| D0-1 | `MAPZ_ASSET_MANIFEST.md` 존재 + MAPS 원본(`D:/project/MAPS`) 접근 가능 | 매니페스트의 cp 명령 실행, 10개 파일 `data/maps_assets/`로 반입, `MAPS_ASSETS=TRUE` | §C 1행 |
| D0-2 | data4library 키 존재하나 `vitalizationErr`(미활성), KCISA 문화정보원 404, 박물관표준 서비스 미구독, TourAPI 500 | 키 기반 소스 전부 사용 불가 판정 | §C 문화정보원 대기/실패 행 |
| D0-3 | 키리스 OSM Overpass(overpass-api.de) 200 + 실제 KR 박물관 POI 반환 성공 | NOKEY 소스 1종 확보 → `MODE=MIXED` (SEED 완전 폴백 아님) | §C MIXED 행, §D-2 |
| D0-4 | GPU 없음, BGE-M3/MiniLM 다운로드는 멀티-GB로 무인 재현성 위험 | `EMBED_TIER=3` (TF-IDF char 2-4gram + 코사인, scikit-learn) 채택. MAPS 자산도 TF-IDF 계보라 정합 | §C EMBED_TIER 행(오프라인 폴백), 무인 원칙 §A-2 정지 금지 |
| D0-5 | 매니페스트 §4: MAPS에 BGE-M3/FAISS/RRF 실체 없음(TF-IDF뿐) | Layer A 임베딩 '재사용'은 벡터가 없으므로 커리어넷 원문/키워드에서 MAPZ가 신규 TF-IDF 색인. 행동 엣지(recommandList)는 라이브러리 API 미활성 → SEED 규칙대로 생성 안 함, 의미 엣지만 사용 | 매니페스트 미해결 #1·#3, §D-1 |
| D0-6 | job_info.csv에 연봉·전망 등 금지 필드 포함 | 로드 시 금지 컬럼 제외(화이트리스트 로드), Layer B 변환 규칙 적용(연봉·전망·요구학력 제거, 직업명→동사 서술) | 기획서 §4.3, 매니페스트 미해결 #4 |

**Phase 0 요약**: MODE=MIXED, EMBED_TIER=3, MAPS_ASSETS=TRUE. 행동 엣지 미생성(라이브러리 API 미활성 → SEED 준용, 의미 엣지만).

## Phase 3 — 연계방안 결정 (자동)

- 임베딩: TF-IDF char_wb 2-4gram (EMBED_TIER=3). 행동엣지 미생성 → RRF 미적용, 의미(코사인) 엣지만.
- 연결 스코어 = topic↔node 코사인 유사도.

### 주제별 편성 (체험8·도서5·인물1·직업≤5, Layer B 1)

| 주제 | 체험(상위) | 도서(상위) | 인물 | Layer B 카드 |
|---|---|---|---|---|
| 공룡 | 8건(당항포 자연사전시관…) | 5권(화석이 된 공룡…) | 메리 애닝 | 화석을 연구하는 사람 |
| 우주 | 8건(나로우주센터 우주과학관…) | 5권(허블 우주망원경…) | 이원철 | 별을 관측하는 사람 |
| 동물 | 8건(곤충박물관…) | 5권(바다 생물 도감…) | 제인 구달 | 동물을 돌보는 사람 |
| 로봇 | 8건(서울로봇인공지능과학관 체험존…) | 5권(생각하는 기계 인공지능…) | 장영실 | 로봇을 만드는 사람 |
| 그림 | 8건(금구원 조각전시관…) | 5권(명화 속 숨은 그림 찾기…) | 신사임당 | 그림 그리는 사람 |

### 옆으로 한 칸 (주제 인접 2개)

- 공룡 → 동물(0.4358), 그림(0.2987)
- 우주 → 로봇(0.7828), 동물(0.2947)
- 동물 → 공룡(0.4358), 그림(0.3922)
- 로봇 → 우주(0.7828), 동물(0.3556)
- 그림 → 동물(0.3922), 공룡(0.2987)

### 발견 피드 쿼터

- 기준 주제 공룡 / 인접 동물 / 먼 주제 우주 / 반고정관념 인물 메리 애닝
- 규칙: 인기순 정렬 금지 - 쿼터 편성(인접1+먼주제1+반고정관념인물1)

**G3: PASS** (빈 슬롯: 없음)

## Phase 6 — 디자인 (시안→컨펌 대행→퍼블리싱)

- 토큰: design/tokens.json (어린이 친화: 그림타일, 44px 터치, 고대비, 시스템폰트, 주제당 포인트 1색).
- 시안 4종 정적 HTML(design/draft_round1/) + Playwright 스크린샷(모바일390/데스크톱1280, design/screenshots/ 8장).
- design-reviewer 서브에이전트 채점:
  - **라운드1: 9/10 REVISE** — 1항 금지어 "필독" 노출(topic.html '더 깊이' 문구). (design/review/round1.md)
  - 수정: "…숙제가 아니라 이 세계를 더 볼 수 있는 책이에요."로 교체.
  - **라운드2: 10/10 APPROVED** (design/review/round2.md).
- 퍼블리싱 확정: app/static/style.css + app/templates/ 베이스.
- **G6 PASS**: 승인기록(round2.md) + 금지어 0 + 스크린샷 증빙.

## Phase 7 — 개발

- FastAPI app/main.py + 6 API + 4 화면(Jinja2). Starlette 1.3.1 TemplateResponse(request, name, context) 시그니처 적용.
- 신선도 불변식 구현: `status='운영중' AND (period_end IS NULL OR period_end>=today)`.
- **G7 PASS**: uvicorn 기동 + /healthz 200 + 4화면 200 (+ API 6종 200).

## Phase 8 — 테스트

- pytest 단위 12종 PASS: API 스키마 5종, 동의어("쥬라기"→공룡/"별"→우주), 신선도(만료 시드 3건 全응답 미노출), 필터(실내+무료).
- Playwright E2E: 4화면 로드 + 클릭흐름(타일→주제관→지도→발견) + **콘솔에러 0**.
- 금지어 lint(scripts/lint_forbidden.py): 렌더 텍스트노드 대상 9페이지 **위반 0건**.
- 커버리지: app/main.py **96%** (≥70%).
- **G8 PASS**: 금지어 0 + 신선도 PASS + E2E 콘솔에러 0.
