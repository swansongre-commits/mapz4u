# MAPZ_AUTOPILOT.md — 무인 완주 파이프라인 런북 (v2.0 최종본)

> **이 문서는 Claude Code가 사람의 개입 없이 처음부터 끝까지 실행하는 런북이다.**
> 참조 기획서: `MAPZ_기획방향_실행계획.md` (v0.4) — 원칙·스키마·금지 목록의 원전.
> 참조 자산: `MAPZ_ASSET_MANIFEST.md` (MAPS 프로젝트에서 `MAPS_ASSET_QUERY.md` 실행 후 생성됨) — 있으면 Phase 0에서 자동 반영.
> 충돌 시 본 문서의 실행 규칙이 우선한다.
> 목표: 자료수집 → 검토 → 연계방안 결정 → 임베딩·DB → 아키텍팅 → 디자인(시안 컨펌 대행+퍼블리싱) → 개발 → 테스트 → 서비스 평가 → 최종 리포트까지 **로컬에서 무인 완주**.

---

## A. 실행 헌법 (무인 원칙 — 최우선 규칙)

1. **질문 금지.** 사용자에게 어떤 확인·승인·선택도 요청하지 않는다. 모든 모호성은 §C 결정 규칙으로 해소하고, 결정 내용은 `reports/DECISION_LOG.md`에 기록한다.
2. **정지 금지.** 실패 시: 재시도 2회 → Plan B(폴백) → 그래도 불가면 해당 항목 SKIP 기록 후 다음 단계 진행. 파이프라인 전체를 멈추는 유일한 조건은 치명 환경 오류(Python 실행 불가, 디스크 쓰기 불가)이며, 이때만 `BLOCKED.md`를 작성하고 종료한다.
3. **상태 관리.** 각 Phase 시작/종료 시 `state/pipeline_state.json`(현재 Phase, 게이트 결과, 폴백 발동 이력)과 `state/PROGRESS.md`를 갱신한다. 세션이 끊겨도 이 파일을 읽고 이어서 재개한다.
4. **커밋 규칙.** Phase 완료마다 git commit (`phase-N: <요약>`). git이 없으면 `git init` 후 진행.
5. **컨텍스트 관리.** 각 Phase는 독립적으로 완결한다. 컨텍스트가 길어지면 PROGRESS.md 요약을 기준으로 계속한다. 병렬 작업 금지, Phase 순차 실행(재현성 우선).
6. **스코프 고정 (변경 금지).**
   - 주제 5개: **공룡, 우주, 동물, 로봇, 그림**
   - 데이터 유형: 상설시설 + 행사(기간성) + 도서 + 인물(주제당 1명) + 직업(Layer A/B용)
   - 화면 4종: 검색 / 주제관 / 지도 둘러보기 / 발견 피드
   - 스택: Python 3.10+, FastAPI, SQLite, Jinja2, vanilla JS, **Leaflet + OpenStreetMap 타일(키 불필요)**
   - 실행 환경: 로컬 단일 머신, 외부 배포 없음
7. **제품 규칙 상속.** 기획서 v0.4의 제품 헌장 5조, 폐기·금지 목록, 도서 노드 규칙(§4.6), Layer B 변환 규칙을 코드·화면·데이터 전체에 적용한다. 위반은 Phase 8 lint에서 FAIL 처리된다.
8. **MAPS 자산은 재료이지 기능이 아니다.** `data/maps_assets/`에서 가져오는 것은 벡터·텍스트뿐이며, MAPS의 매칭·추천 로직·개인정보·UI는 이관하지 않는다 (원칙: `MAPS_to_MAPZ_자산이관_판단표.md`).

---

## B. 사전 조건 (사람이 하는 일 — 유일하게 남은 개입)

### B-1. 키·자산 상태 (현재 확정본)

| 항목 | 상태 |
|---|---|
| 공공데이터포털 계정 | 가입 완료, 일반인증키(Decoding) 발급 |
| 한국문화정보원_한눈에보는문화정보조회서비스 | 활용신청 완료 (승인 대기 가능) |
| 전국박물관미술관정보 표준데이터 | 파일 다운로드 대상 — 키 불필요, 활용신청 불필요 |
| 정보나루 | 가입 완료, 인증키 신청 완료/대기 |
| MAPS 임베딩 자산 | `MAPS_ASSET_QUERY.md`를 MAPS 프로젝트에서 별도 실행해 `MAPZ_ASSET_MANIFEST.md` 확보 필요 (아래 B-2) |

### B-2. 실행 순서 (2단계)

```bash
# 1단계 — MAPS 프로젝트 루트에서 (선행, 1회)
cd ~/projects/maps
claude
> "MAPS_ASSET_QUERY.md를 읽고 Step 1~4를 순서대로 실행해 MAPZ_ASSET_MANIFEST.md를 작성하라."
# 완료 후 MAPZ_ASSET_MANIFEST.md를 mapz/ 프로젝트 루트로 복사해 둘 것

# 2단계 — MAPZ 프로젝트 루트에서
cd ~/projects/mapz
# .env 파일에 아래 값 세팅 (없으면 SEED 모드로 자동 전환되어도 완주됨)
#   DATA_GO_KR_KEY=디코딩키
#   DATA4LIBRARY_KEY=정보나루인증키
claude --dangerously-skip-permissions
> "MAPZ_AUTOPILOT.md를 읽고 Phase 0부터 Phase 9까지 무인으로 완주하라. 질문 금지."
```

> 권한 프롬프트가 무인 실행을 끊지 않도록 위 플래그(또는 settings.json allowlist 사전 구성)가 필요하다. 이것이 유일한 인간 행위다.

### B-3. 사용량 한도로 중단됐을 때 재개하는 법

자동 재시도 루프는 두지 않는다(불필요한 복잡도). 대신 **끊긴 지점을 정확히 남기는 것**으로 대응한다.

- **세부 진행 기록**: Phase 시작/종료뿐 아니라, 자료수집처럼 시간이 오래 걸리는 Phase 내부에서도 하위 스텝 단위로 `state/PROGRESS.md`에 갱신한다. 예: `Phase 1 - 도서 수집 완료 / 체험(상설) 수집 중 (32/60건)`. 한도로 강제 종료되기 직전까지의 마지막 완료 스텝이 항상 파일에 남아 있어야 한다.
- **재개 명령**: 컴퓨터·Claude Code 앱은 켜둔 채로 있다가, 사용량이 리셋된 뒤 아래 한 줄만 다시 입력한다.
  ```bash
  claude --dangerously-skip-permissions
  > "state/PROGRESS.md와 pipeline_state.json을 확인하고, 멈춘 지점부터 MAPZ_AUTOPILOT.md 절차를 이어서 완주하라. 질문 금지."
  ```
- **재개 시 규칙**: 이미 완료된 Phase·스텝은 재실행하지 않는다(멱등성 — 이미 만든 파일·DB 레코드가 있으면 건너뛴다). 진행 중이던 스텝만 이어서 마무리하고 다음으로 넘어간다.
- **중단 원인 구분**: PROGRESS.md에 중단 사유를 한 줄 남긴다 — `사용량 한도`, `오류`, `정상 완료(다음 세션 대기)` 중 하나. 사람이 나중에 훑어볼 때 무엇 때문에 멈췄는지 바로 알 수 있게 한다.

---

## C. 전역 결정 규칙 (모호성 해소표)

| 상황 | 결정 |
|---|---|
| `MAPZ_ASSET_MANIFEST.md` 존재 | Phase 0에서 명시된 cp 명령 실행해 `data/maps_assets/`로 자산 반입, `MAPS_ASSETS=TRUE` |
| `MAPZ_ASSET_MANIFEST.md` 부재 | `MAPS_ASSETS=FALSE` — Layer A/B/C 직업·학과 텍스트는 모델 지식으로 자체 생성(§D-1 준용), DECISION_LOG에 사유 기록 |
| 문화정보원 API 키 있음 + 호출 성공 | `MODE=API` (해당 소스) |
| 문화정보원 API 승인 대기/실패, 정보나루·공공데이터포털 키 있음 | 가능한 소스만 API, 나머지는 **NOKEY**(§D-2 파일 다운로드·무키 소스)로 보강 → `MODE=MIXED` |
| 모든 키 실패/부재 | `MODE=SEED` — §D-1 시드 생성 규칙 |
| GPU 사용 가능 + sentence-transformers 설치 성공 | `EMBED_TIER=1` BGE-M3 |
| GPU 없음, 모델 다운로드 가능 | `EMBED_TIER=2` paraphrase-multilingual-MiniLM-L12-v2 |
| 오프라인 / 모델 다운로드 실패 | `EMBED_TIER=3` TF-IDF(char 2-4gram) + 코사인 |
| FAISS 설치 실패 | sklearn NearestNeighbors로 대체 |
| Playwright 브라우저 설치 실패 | 스크린샷 단계 SKIP, 디자인 리뷰는 HTML 소스 기반으로 수행 |
| 수치 판단 동률 | 사전순(가나다) 선택 후 로그 기록 |
| 라이브러리 버전 충돌 | 최신 안정판 고정 재설치 1회 → 실패 시 해당 기능 폴백 |

---

## D-1. 시드 데이터 생성 규칙 (MODE=SEED 전용)

- Claude Code가 **실존하는 전국 국공립 시설 지식**으로 생성한다 (예: 국립중앙과학관, 국립과천과학관, 국립생태원, 국립중앙박물관 어린이박물관, 국립민속박물관, 지역 자연사·과학관 등). 좌표는 실제 시설 좌표로.
- 모든 시드 레코드는 `is_seed=true`, `last_verified=실행일`, 출처 `"seed:model-knowledge"` 표기. 화면에는 "표본 데이터(검증 필요)" 배지를 노출한다.
- 최소 건수: 체험 60건(주제당 12: 상설 8 + 행사 4), 도서 50건(주제당 10, 실존 어린이책 위주), 인물 5명(주제당 1: 반고정관념 최소 2명 포함), 직업 25건(주제당 5, 동사 서술).
- 행사 기간은 실행일 기준 −10일 ~ +60일로 분산 생성한다 (만료 필터 테스트가 유의미하도록 만료 건 3건 포함).
- 행동 엣지(함께 빌린 책)는 SEED 모드에서 생성하지 않는다 — 의미 엣지만 사용하고 DECISION_LOG에 명시.

## D-2. NOKEY 보강 소스 (MODE=MIXED에서 활용, 키 불필요)

| 소스 | 내용 | 방법 |
|---|---|---|
| 공공데이터포털 '전국박물관미술관정보 표준데이터' | 상설시설 명칭·좌표·기본정보 | CSV 파일 직접 다운로드 (활용신청 불필요) |
| OSM Overpass API | 전국 박물관·과학관·미술관 POI | 무키 쿼리 (`tourism=museum`, `tourism=gallery` 등) |
| 기관 홈페이지 | 국공립 전시·프로그램 공지 | 크롤링 (Tier 2) |
| 국립중앙도서관 사서추천·국립어린이청소년도서관 | 추천 도서 목록 | 페이지 크롤링 |
| Wikidata·위키백과 | 인물 데이터 | 무키 API |

---

## Phase 0 — 환경 셋업 & 셀프체크 & 자산 반입

1. 폴더 구조 생성:
```
mapz/
├── .claude/agents/    ├── state/        ├── data/{raw,clean,seed,maps_assets}/
├── db/                ├── docs/adr/     ├── design/{screenshots,review}/
├── app/{templates,static}/  ├── scripts/  ├── tests/   └── reports/
```
2. `python -m venv .venv` → 활성화 → 설치: `fastapi uvicorn jinja2 requests beautifulsoup4 pandas scikit-learn pytest httpx playwright` (+ 조건부: `sentence-transformers faiss-cpu`). `playwright install chromium` 시도.
3. **MAPS 자산 반입**: 프로젝트 루트에서 `MAPZ_ASSET_MANIFEST.md` 탐색. 있으면 명시된 `cp` 명령 실행 → `data/maps_assets/`에 반입, `MAPS_ASSETS=TRUE` 기록. 없으면 `MAPS_ASSETS=FALSE` 기록하고 진행(§C 규칙).
4. `.env` 파일 존재 여부와 `DATA_GO_KR_KEY`, `DATA4LIBRARY_KEY` 값 검증(더미/공백 아닌지) → `state/env.json`에 MODE 판정 기록(§C 표 기준).
5. 환경 감지 → `state/env.json`에 추가 기록: EMBED_TIER, 네트워크, GPU.
6. **서브에이전트 4종 생성** — §K의 스펙을 `.claude/agents/`에 파일로 저장: `design-reviewer.md`, `persona-parent.md`, `persona-psych.md`, `persona-career.md`.
7. `state/pipeline_state.json` 초기화, git init+commit.

**게이트 G0**: venv에서 `python -c "import fastapi"` 성공. FAIL 시 BLOCKED.md.

---

## Phase 1 — 자료수집

| 대상 | MODE=API/MIXED | MODE=SEED |
|---|---|---|
| 체험(상설) | 전국박물관미술관 표준데이터 **CSV 직접 다운로드**(키 불필요) → 주제 5개 관련 시설 필터, 부족 시 OSM Overpass 보강 | §D-1 생성 |
| 체험(행사) | 한국문화정보원_한눈에보는문화정보조회서비스 API (DATA_GO_KR_KEY) → 실패/승인대기 시 TourAPI 또는 NOKEY 크롤링 보강 | §D-1 생성 |
| 도서 | 정보나루: 인기대출(연령 8~13) + 사서추천 → 주제 키워드 필터, 소장/대출가능은 조회 API 확인 | §D-1 생성 |
| 행동 엣지 | 정보나루 recommandList — 수집 도서 ISBN별 '함께 빌린 책' | 생성 안 함 |
| 인물 | 모델 지식으로 생성 (역사 인물 — API 불필요), 보강 시 Wikidata | 동일 |
| 직업·학과 | `MAPS_ASSETS=TRUE`면 `data/maps_assets/`에서 로드, `FALSE`면 모델 지식 생성(동사 서술) | 동일 |

- 각 수집기는 `scripts/collect_*.py`로 작성·실행. 원본은 `data/raw/`에 JSON 저장.
- API/파일/크롤링 결과가 최소 건수에 미달하면 시드로 **보강**(혼합 허용, is_seed 구분 유지).

**게이트 G1**: 체험 ≥ 60, 도서 ≥ 50, 인물 = 5, 직업 ≥ 25. 미달 시 시드 보강 후 재검사.

---

## Phase 2 — 검토 (데이터 품질 게이트)

`scripts/validate.py` 작성·실행:
- 필수 필드 존재(명칭·좌표·주제태그·last_verified·status), 스키마 적합률 ≥ 95%
- 좌표 유효성: 위도 33~39, 경도 124~132 (한국 bbox), 위반 레코드 제외
- 중복 제거: (명칭 정규화 + 좌표 반올림 3자리) 키
- 주제 태그: 관리 사전(5개 주제 + 동의어: 공룡=화석=쥬라기, 우주=천문=별, 동물=생태=곤충, 로봇=코딩=기계, 그림=미술=만들기)에 매핑, 미매핑은 재분류 1회 시도 후 제외
- 주제당 체험 ≥ 8 유지

산출: `data/clean/*.json`, `reports/data_quality.md` (건수·제외 사유 통계, MODE·소스별 구성비 포함).

**게이트 G2**: 적합률 ≥ 95% AND 주제당 ≥ 8. 미달 시 시드 보강 1회 → 재실행. 2회 실패 시 미달 주제를 4개로 축소하고 DECISION_LOG 기록(주제 3개 미만이 되면 BLOCKED).

---

## Phase 3 — 연계방안 결정 (자동)

1. 임베딩(EMBED_TIER)으로 {주제, 체험, 도서, 인물, 직업} 텍스트 벡터화. `MAPS_ASSETS=TRUE`면 직업·학과 벡터는 반입된 임베딩 재사용(재계산 생략), 나머지는 신규 계산.
2. 연결 스코어 = 코사인 유사도. 행동 엣지(recommandList)가 있으면 **RRF 융합**: `score = Σ 1/(60+rank)` (의미 랭크 + 행동 랭크). `MAPS_ASSETS=TRUE`이고 반입 코드에 RRF 로직이 있으면 그대로 재사용.
3. 자동 결정 규칙:
   - 주제별 편성: 체험 상위 8건(상설 우선), 도서 상위 5권, 인물 1명, 직업 3~5건(Layer B 카드 1건 선정)
   - '옆으로 한 칸': 주제 간 인접도 행렬 → 각 주제당 인접 주제 2개 확정
   - 발견 피드 쿼터: 최근 주제 인접 1 + 먼 주제(인접도 최하) 1 + 반고정관념 인물 카드 1
4. 모든 확정 목록과 근거 수치를 `reports/DECISION_LOG.md`에 기록.

**게이트 G3**: 5개 주제 모두 편성표 완성(빈 슬롯 0). 빈 슬롯은 차순위로 채움.

---

## Phase 4 — 임베딩·DB 구축

`scripts/build_db.py` — SQLite `db/mapz.db` 생성. DDL(요지):

```sql
CREATE TABLE topic(id TEXT PRIMARY KEY, name TEXT, synonyms TEXT, emoji TEXT);
CREATE TABLE experience(id TEXT PRIMARY KEY, name TEXT, type TEXT, topic_tags TEXT,
  verb_tags TEXT, lat REAL, lng REAL, region TEXT, period_start TEXT, period_end TEXT,
  hours TEXT, age_note TEXT, duration_min INT, cost TEXT, reservation_url TEXT,
  indoor INT, parking TEXT, stroller TEXT, crowd_note TEXT, related_books TEXT,
  source TEXT, is_seed INT, last_verified TEXT, status TEXT);
CREATE TABLE book(isbn TEXT PRIMARY KEY, title TEXT, author TEXT, publisher TEXT,
  pub_year INT, kdc TEXT, topic_tags TEXT, age_band TEXT, availability TEXT,
  source TEXT, is_seed INT, last_verified TEXT);
CREATE TABLE person(id TEXT PRIMARY KEY, name TEXT, era TEXT, verb_desc TEXT,
  story_trial TEXT, sites TEXT, job_lineage TEXT, anti_stereotype INT, topic_tags TEXT);
CREATE TABLE job(id TEXT PRIMARY KEY, name TEXT, verb_desc TEXT, layer TEXT, topic_tags TEXT,
  source_asset TEXT);  -- 'maps_assets' 또는 'generated'
CREATE TABLE edge(src_type TEXT, src_id TEXT, dst_type TEXT, dst_id TEXT,
  edge_type TEXT, score REAL, source TEXT);
```

- 벡터는 FAISS 인덱스(`db/faiss.index`) 또는 sklearn 폴백으로 저장, 로딩 유틸 포함.
- 인덱스: topic_tags, status, period_end.

**게이트 G4**: 모든 테이블 행수 = clean 데이터 건수 일치, 조인 무결성 쿼리 통과.

---

## Phase 5 — 아키텍팅

`docs/ARCHITECTURE.md` + ADR 4건 자동 작성:
- ADR-001 스택 선정(FastAPI+SQLite — 로컬 무인 재현성), ADR-002 지도(Leaflet+OSM — 키 무의존), ADR-003 폴백 구조(EMBED_TIER/MODE 분기), ADR-004 MAPS 자산 재사용 경계(Layer A/B/C 분리, 재료-기능 분리 원칙).

API 설계(구현 대상):
```
GET /api/topics                 # 5개 주제 + 이모지 타일
GET /api/topics/{id}            # 주제관: 상설/행사/도서/인물카드/옆으로한칸
GET /api/search?q=&indoor=&free=&region=   # 아이 언어 검색(동의어) + 부모 필터
GET /api/map?bbox=&topics=      # 지도 마커(운영중만)
GET /api/discover               # 발견 피드(쿼터 편성, 인기순 금지)
GET /healthz
```
규칙: 모든 목록 응답에서 `status!='운영중'` 또는 `period_end<today` 제외(신선도), `last_verified`·`is_seed` 필드 포함.

**게이트 G5**: 문서 존재 + API 명세와 Phase 7 구현의 1:1 대응표 작성.

---

## Phase 6 — 디자인 (시안 → 컨펌 대행 → 퍼블리싱)

1. `design/tokens.json` 생성 — 어린이 친화 원칙: 큰 그림 타일(이모지/인라인 SVG, 외부 이미지 무의존), 터치 타깃 ≥ 44px, 고대비, 시스템 폰트 스택, 절제된 팔레트(주제당 포인트 1색).
2. 4개 화면의 **정적 HTML 시안**을 `design/draft_round1/`에 작성.
3. Playwright로 화면별 스크린샷(모바일 390px + 데스크톱 1280px) → `design/screenshots/`.
4. **design-reviewer 서브에이전트 호출** — §K 체크리스트 10항 채점, `design/review/round1.md` 작성.
5. 판정: **9/10 이상 PASS → 승인.** 미달 시 지적사항 반영해 재시안 → 재리뷰 (최대 3라운드). 3라운드 후에도 미달이면 최고점 시안 채택 + 사유 기록.
6. 승인 시안을 `app/static/style.css` + `app/templates/` 베이스로 **퍼블리싱 확정**, 승인 기록을 DECISION_LOG에 남긴다.

**게이트 G6**: 승인 기록 존재 + 금지어 0 + 스크린샷(또는 소스 리뷰) 증빙.

---

## Phase 7 — 개발

FastAPI 앱(`app/main.py`) + 화면 4종 구현. 화면별 필수 요소:
- **검색**: 검색창(동의어 매칭) + 필터 칩(실내/무료/지역/이번 주) + 결과 카드(최종확인일·시드 배지·길찾기 링크=OSM 좌표 링크)
- **주제관**: 히어로 타일 / 상설 체험 8 / 이번 달 행사 / '더 깊이' 도서 5(대출가능·소장 표기 자리) / '이 세계의 어른들' 인물 카드 1(시행착오담+직업 계보) / '옆으로 한 칸' 2
- **지도**: Leaflet, 주제 레이어 토글, 운영중만 표시, 마커 팝업에 핵심 메타
- **발견 피드**: 쿼터 편성(§Phase3), 셔플 버튼, 인기순 정렬 없음
- 공통: 자동재생·무한스크롤 없음, 권장 연령은 회색 참고 표기, 1차 CTA는 '길찾기/소장 조회'(현실 전환)

**게이트 G7**: `uvicorn` 기동 + `/healthz` 200 + 4개 화면 200.

---

## Phase 8 — 테스트 (수정 루프 최대 3회)

1. **pytest 단위**(`tests/`): API 5종 응답 스키마, 동의어 검색("쥬라기"→공룡), **신선도 테스트(만료 행사 미노출 — 시드의 만료 3건이 절대 응답에 없어야 함)**, 필터 조합.
2. **Playwright E2E**: 4화면 로드, 검색→주제관→지도 흐름 클릭, 콘솔 에러 0.
3. **금지어 lint**(`scripts/lint_forbidden.py`): 렌더링된 HTML 텍스트 노드 대상 — `등급, 백분위, 또래, 비교해, 필독, 수준별, 레벨테스트, 지금 안 하면, 늦기 전에, 골든타임, 선행, 유형입니다` → **0건 게이트**. ("권장 연령" 표기는 허용 예외.)
4. 커버리지: 핵심 로직(검색·신선도·편성) ≥ 70%.

FAIL 시: 원인 수정 → 재실행 (라운드당 기록). 3회 후 잔여 FAIL은 FINAL_REPORT의 '미해결 결함'으로 이월(단, 금지어 lint와 신선도 테스트는 이월 불가 — 통과할 때까지 수정).

**게이트 G8**: 금지어 0 + 신선도 테스트 PASS + E2E 콘솔 에러 0.

---

## Phase 9 — 서비스 평가 & 최종 리포트

1. **페르소나 3인 평가** — persona-parent / persona-psych / persona-career 서브에이전트가 각자 §K 루브릭 10항으로 스크린샷+렌더링 HTML을 채점, `reports/eval_{persona}.md` 작성 (PASS/FAIL + 개선 제안).
2. **헌장 감사**: 헌장 5조 각각에 대해 구현 증거(코드/화면 위치) 매핑 표 작성.
3. **성능 스모크**: 주요 API 응답시간 측정(로컬 기준 p95 < 500ms 목표, 참고치).
4. **`reports/FINAL_REPORT.md`** 작성:
   - 파이프라인 요약(각 Phase 소요·게이트 결과·폴백 발동 이력 — MODE/EMBED_TIER/MAPS_ASSETS 포함)
   - 데이터 통계, 자동 결정 하이라이트, 디자인 리뷰 라운드 결과
   - 테스트 결과, 페르소나 3인 점수표, 미해결 결함·개선 백로그
   - **무인 실행 회고**: 사람이 개입했어야 할 뻔한 지점 목록 (이번 실험의 진짜 산출물)
5. 최종 commit + `PROGRESS.md`에 "COMPLETE" 기록. 실행 안내 1줄: `uvicorn app.main:app --port 8000`.

**완료 정의(DoD)**: G0~G8 전부 기록 + 로컬 기동 가능한 서비스 + FINAL_REPORT.md 존재.

---

## K. 서브에이전트 스펙 (Phase 0에서 `.claude/agents/`에 저장)

**design-reviewer** — 역할: 디자인 시안 컨펌 대행. 체크 10항: ①금지어 0 ②인기순 단일 정렬 없음(쿼터 확인) ③아이 진입 화면은 그림 타일 우선·텍스트 최소 ④터치 타깃 ≥ 44px ⑤명도 대비 AA 근사 ⑥자동재생·무한스크롤 없음 ⑦권장 연령이 등급처럼 보이지 않음 ⑧최종확인일·시드 배지 노출 ⑨도서에 소장/대출 표기 자리 ⑩1차 CTA가 현실 전환(길찾기/소장). 출력: 항목별 PASS/FAIL + 수정 지시. 9/10 이상 승인.

**persona-parent(학부모)** — 30초 내 '이번 주말 갈 곳' 도달 가능 / 실내·무료 필터 작동 / 만료 정보 없음 / 허탕 방지 정보(예약·휴관·최종확인일) / 비용 표시 / 길찾기 1탭 / 도서의 대출 정보 / 광고·불안 문구 0 / 시드 배지의 정직성 / 아이 혼자 봐도 안전.

**persona-psych(아동심리)** — 헌장 1·2조 준수 / 유형 라벨 0 / 아이 선택지 2~3개 구조('옆으로 한 칸') / 외적 보상(포인트·랭킹) 0 / 반고정관념 편성 존재 / 인물 서사가 시행착오담 / 성과화 문구 0 / 세션 종료 지점 존재 / 권장 연령의 참고화 / 직업 정보에 연봉·전망 노출 0.

**persona-career(진로)** — 동사 태그 저장·표시 / 옆으로 한 칸 인접 품질(무작위 아님, 근거 로그) / Layer A/B 분리 준수(초등 화면에 직업 명사 최소) / 직업 계보 one-to-many / 스키마의 확장성(커리어넷 필드 수용 여지) / DECISION_LOG 추적 가능성 / 신선도 규칙 구현 / 데이터 출처 표기 / 이력층 접속 여지(동사 로그) / 공영 중립성(구매 링크 후순위).

---

## 부록 A. 예상 리스크와 사전 응답

| 리스크 | 본 문서의 응답 |
|---|---|
| API 승인 대기로 무인성 붕괴 | MODE=MIXED(NOKEY 소스 보강) 및 MODE=SEED 완주 경로 상시 보장 |
| 장시간 실행 중 컨텍스트 소진 | Phase 독립 완결 + state 재개 |
| 디자인 '컨펌' 주체 부재 | design-reviewer 대행 + 3라운드 상한 |
| 테스트 무한 루프 | 수정 3회 상한 + 이월 규칙(단 안전 게이트 2종은 예외) |
| 시드 데이터의 사실성 | is_seed 배지 + "검증 필요" 정직 표기 |
| 평가의 자기참조(만든 자가 채점) | 루브릭 고정 + 증거(스크린샷·코드 위치) 첨부 의무 |
| MAPS 자산 미확보 | `MAPS_ASSETS=FALSE` 경로로 완주, DECISION_LOG에 사유 기록 (V2에서 재반입 가능) |

## 부록 B. v1.0 → v2.0 변경 이력

- MAPS 자산 반입을 Phase 0 정식 단계로 편입 (§B-2, Phase 0-3)
- `MAPS_ASSET_QUERY.md` / `MAPZ_ASSET_MANIFEST.md` 연동 규칙 추가
- MODE를 2단(API/SEED)에서 **3단(API/MIXED/SEED)**으로 확장, NOKEY 보강 소스 표(§D-2) 신설
- 문화정보원_한눈에보는문화정보조회서비스로 행사 데이터 소스 확정, 전국박물관미술관정보는 파일 다운로드로 명확화(Phase 1 표 갱신)
- ADR-004(MAPS 자산 재사용 경계) 추가
- job 테이블에 `source_asset` 컬럼 추가(반입 vs 생성 구분 추적성)
