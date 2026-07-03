# MAPZ_ASSET_MANIFEST.md — MAPS→MAPZ 이관 자산 명세

- **작성일**: 2026-07-03
- **작성자**: Claude Code (MAPS 프로젝트 read-only 조회)
- **근거 문서**: `MAPS_ASSET_QUERY.md`(실행 지시서) · `MAPS_to_MAPZ_자산이관_판단표.md`(원칙)
- **범위**: MAPS 프로젝트 루트에서 조회·매핑·명령어 생성까지. **cp 실제 실행은 MAPZ 쪽 AUTOPILOT Phase 0에서 수행.**
- **핵심 결론(요약)**: 판단표가 상정한 **BGE-M3 sentence embedding·FAISS 인덱스·RRF 융합 로직·동사 태깅 체계는 MAPS에 실체가 없다.** MAPS의 벡터화 계층은 TF-IDF(scikit-learn) 기반이며, 매칭은 rank 점수합 방식이다. 따라서 이관 확정 자산은 실질적으로 **§1(원천 데이터)**, **§2(어린이 어휘 파생 자산)**, **§3(TF-IDF 파생 산출물, 참고용)** 세 갈래로 좁혀진다.

---

## Step 2. 6개 슬롯 매핑 (판단표 §1)

| 슬롯 | 찾아야 할 것 | 실제 파일(경로/파일명) | 크기 | 최종 수정일 | 비고 |
|---|---|---|---|---|---|
| 1. 직업 임베딩 (549건) | 직업 텍스트의 벡터 표현 | **해당 없음(sentence embedding 미구축)** — TF-IDF 파생 대체: `jobs_keywords.json`(549 문서×rank20 키워드/동의어) | 1.3 MB | 2026-05-29 | BGE-M3·SentenceTransformer 호출 코드/산출물 zero. 판단표가 상정한 벡터는 미존재 |
| 2. 학과 임베딩 (504건) | 학과 텍스트의 벡터 표현 | **해당 없음(sentence embedding 미구축)** — TF-IDF 파생 대체: `majors_keywords.json` | 1.2 MB | 2026-05-29 | 동일. 벡터가 아니라 키워드+동의어 사전 형태 |
| 3. FAISS 인덱스 | 최근접 탐색 색인 | **해당 없음** | — | — | `.faiss` `.index` `.pkl` `.npy` 파일 전수 zero (`find -maxdepth 3` 확인) |
| 4. 커리어넷 원천 데이터 | 직업/학과 원문(연봉·전망 등 원본 필드 포함) | `job_info.csv` (549행, 32필드) · `major_info.csv` (573행, 23필드) · `datacrawling/job_seq_list.csv` · `datacrawling/major_seq_list.csv` | 4.0 MB · 9.7 MB · 2.5 KB · 2.2 KB | 2026-05-29 · 2026-05-29 · 2026-06-27 · 2026-06-27 | **연봉·취업률·전망·성별비율·적성유형 필드 포함 → 가공 후 이관** (판단표 §1-4) |
| 5. 임베딩·RRF 파이프라인 코드 | BGE-M3 + RRF 융합 | **해당 없음(BGE-M3/RRF 없음)** — TF-IDF 파이프라인만: `build_keywords.py`, `datacrawling/ai학과직업추천_코드_통합버전.py`, `datacrawling/crawl_careernet_api.py` | 3.4 KB · 41 KB · 4.3 KB | 2026-05-29 · 2026-06-27 · 2026-06-27 | 원문 크롤 스크립트는 이관 후보(재수집용). TF-IDF 로직은 MAPZ가 BGE-M3로 새로 짜야 하므로 이관 실익 낮음 |
| 6. 동사 태깅 체계 | 직업/학과의 동사·활동 단위 분류 | **해당 없음** | — | — | `verb` `action` `동사` 태그 스키마 zero. 대신 `kid_blurbs.json`(어린이용 서술형 blurb 549개)이 §4.3 "동사 서술 변환"의 씨앗 자료로 대체 가능 → 슬롯 6-대체로 이관 검토 |

---

## Step 3. 추가 분류 (판단표 §3 4문항 적용)

Step 1에서 발견한 나머지 파일. 판단 4문항 = ① 데이터인가/로직인가 ② 금지목록(등급·매칭·연봉·전망) 위반 ③ 개인정보 ④ MVP(공룡·우주·동물·로봇·그림) 필요.

### 3-A. 이관 확정 (그대로 또는 가공 후)

| 파일 | 유형 | 판정 | 사유 |
|---|---|---|---|
| `junior_jobs.json` (80 KB) | 데이터 | **가공 후 이관 (권장)** | 자녀·초중용으로 변환된 직업 549개(emoji + 어린이용 blurb + 관련 학과). MAPZ Layer B 변환 규칙의 **씨앗 데이터**. 학과명 필드는 제거 후 활용 |
| `kid_blurbs.json` (55 KB) | 데이터 | **그대로 이관** | 직업번호별 어린이용 서술 549건. 문장 자체가 이미 "~해요" 동사 서술체 → §4.3 어투 예시로 즉시 사용 가능. 등급·매칭·연봉·전망 요소 없음 |
| `synonyms_merged.json` (274 KB) | 데이터 | **그대로 이관** | 5,464개 고유 키워드의 쉬운말 동의어 사전. MAPZ 어린이 발화 매칭용 어휘 소스로 유용. 판정·매칭 요소 없음 |

### 3-B. V2 보류 (MVP 밖, 원본 존치)

| 파일 | 판정 | 사유 |
|---|---|---|
| `mapping_major.csv` (2.4 MB), `mapping_job.csv` (73 KB), `mapping_univ.json` (1.7 MB), `mapping_category.json` (18 KB) | V2 보류 | 학과-대학-과목 매핑. Layer C(중등·부모, 고1 과목 내비게이션)용. MVP에는 불필요 |
| `schools.db` (21 MB), `subjects_by_school*.json/.csv` (합 41 MB), `vocab_2022.json` (9 KB), `school_list.csv` (431 KB), `collection_status.*` (합 1 MB) | V2 보류 | 고교 개설과목. MVP(어린이 지도) 밖 |
| `achievement_standards.json` (596 KB), `성취기준.xlsx` (19 MB, gitignore) | V2 보류 | 초·중·고 성취기준 원본. MVP 밖 |
| `keywords_top20.csv` (231 KB), `keywords_unique.json` (135 KB), `keywords_list.txt` (101 KB), `doc_keyword_weights.json` (1.7 MB), `vectorizer_meta.json` (226 KB), `noun_df.json` (145 KB), `syn_batches/*.json` (16개) | V2 보류(참고용 별도 이관 검토) | TF-IDF 파생 산출물·사람 검수용. MAPZ가 BGE-M3로 재구축 시 참고 가능하나 MVP 필수 아님 |
| `설치모집단위 리스트.xlsx` (3.4 MB) | V2 보류 | 대학 모집단위 원본. Layer C용 |

### 3-C. 이관 제외 (로직·UI·환경·비MVP)

| 파일 | 사유 |
|---|---|
| `app.py`, `views/highschool.py`, `views/junior.py`, `views/landing.py`, `views/legacy.py` | Streamlit UI 코드. 판단표 §2-5 |
| `recommender.py`, `career_recommender.py`, `tokenizer.py`, `llm_extract.py` | 매칭·추천 로직. 판단표 §2-1 |
| `build_*.py`, `parse_*.py`, `crawl_curriculum.py`, `fetch_curriculum.py`, `merge_years.py`, `run_pipeline.py`, `content_db.py` | 산출물 빌드 스크립트. 원본 재현 필요 시 개별 검토 |
| `compounds.json`, `compound_rules.json`, `broken_split.json`, `stopwords.json`, `comp_freq.json`, `comp_items.json` | 한국어 토크나이저 부속 사전. tokenizer.py 없이 단독 이관 실익 없음 |
| `content.db` (5.0 MB) | MAPS 고교용 통합 DB. 등급·매칭 관련 스키마 포함 우려 → 이관 제외 |
| `.env`, `.env.example`, `.streamlit/*`, `requirements.txt`, `__pycache__/`, `*.log`, `curriculum_files/` (3.3 GB) | 환경·캐시·대용량 원본. 이관 실익 없음 |
| `MAPS_*.md/pdf/docx`, `README.md`, `CLAUDE.md`, `SERVICE_REVIEW.md`, `UX_REDESIGN_BRIEF.md`, `CODEX_HANDOFF_UX_PLAN.md`, `HANDOFF_고교개설과목.md`, `DB_SCHEMA_재구조화.md`, `PLANNING_REVIEW_REPORT.md`, `QUICKWINS_APPROVED_SPEC.md` | MAPS 도메인 문서. MAPZ에는 별도 문서 체계. 필요 시 사람이 발췌 인용 |
| `학과직업추천_전체.zip` (4.1 MB, gitignore) | 초기 아카이브 |

---

## 3. 복사 명령 목록 (MAPZ Phase 0에서 실행)

> 원본 보존(이동 아님). 목적지는 `mapz/data/maps_assets/` 하위 카테고리로 분리. **PowerShell/Bash 어느 쪽에서도 동작하는 형태로 작성.**

### 3-1. 슬롯 4 — 커리어넷 원천 데이터 (가공 후 이관 조건)

```bash
# 원문 CSV 2종 + seq 목록 (재수집 재현용)
cp "D:/project/MAPS/job_info.csv"                        "<mapz>/data/maps_assets/raw/job_info.csv"
cp "D:/project/MAPS/major_info.csv"                      "<mapz>/data/maps_assets/raw/major_info.csv"
cp "D:/project/MAPS/datacrawling/job_seq_list.csv"       "<mapz>/data/maps_assets/raw/job_seq_list.csv"
cp "D:/project/MAPS/datacrawling/major_seq_list.csv"     "<mapz>/data/maps_assets/raw/major_seq_list.csv"
# 재수집 스크립트 (커리어넷 API) — 로직이지만 데이터 재현 목적, 헌장 중립
cp "D:/project/MAPS/datacrawling/crawl_careernet_api.py" "<mapz>/data/maps_assets/raw/crawl_careernet_api.py"
```

### 3-2. 슬롯 6-대체 + 3-A — 어린이 어휘/서술 자산

```bash
cp "D:/project/MAPS/junior_jobs.json"       "<mapz>/data/maps_assets/kid_lexicon/junior_jobs.json"
cp "D:/project/MAPS/kid_blurbs.json"        "<mapz>/data/maps_assets/kid_lexicon/kid_blurbs.json"
cp "D:/project/MAPS/synonyms_merged.json"   "<mapz>/data/maps_assets/kid_lexicon/synonyms_merged.json"
```

### 3-3. 슬롯 1·2 — TF-IDF 파생 산출물 (BGE-M3 재구축 참고용, 선택)

> **MAPZ가 BGE-M3로 새 임베딩을 구축할 예정이라면 스킵 가능.** rank 20 키워드/동의어 구조가 "직업 성격 요약"으로 재활용 여지가 있을 때만 이관.

```bash
cp "D:/project/MAPS/jobs_keywords.json"     "<mapz>/data/maps_assets/tfidf_ref/jobs_keywords.json"
cp "D:/project/MAPS/majors_keywords.json"   "<mapz>/data/maps_assets/tfidf_ref/majors_keywords.json"
```

### 3-4. 이관 없음 (참고)

- 슬롯 3(FAISS): 파일 자체가 없어 복사 대상 없음.
- 슬롯 5(BGE-M3+RRF): 코드 없음. `build_keywords.py` 등 TF-IDF 파이프라인은 MAPZ 헌장의 BGE-M3+RRF와 알고리즘이 달라 이관 실익 없음.
- 3-B V2 보류 파일들: MVP 통과 후 재검토. 원본은 MAPS 프로젝트에 그대로 유지.

---

## 4. 미해결 항목 (사람 확인 필요)

1. **BGE-M3 임베딩·FAISS 인덱스 부재 확정**
   판단표 §1의 슬롯 1·2·3·5는 MAPS 실체가 없다. **MAPZ가 처음부터 구축해야 한다.** 이관이 아니라 신규 개발 결정을 요함. → 확인 요청: MAPZ Phase 0에서 "MAPS로부터의 임베딩 재사용" 항목을 아예 삭제하고 "커리어넷 원문에서 신규 색인"으로 계획을 갱신할지.

2. **`major_info.csv`의 573행 vs. 판단표의 "학과 504건" 불일치**
   원문 CSV는 573행(헤더 제외)인데 MAPS 산출 `majors_keywords.json`은 504건이다. 정제 과정에서 통합/제거된 학과가 있다. MAPZ가 원문을 재사용할 때 어느 기준(원문 573 vs 정제 504)을 쓸지 확인 필요.

3. **동사 태깅 체계의 대체 자원 승인**
   슬롯 6은 부재 확정. 그 자리에 `kid_blurbs.json`(어린이 서술형 blurb 549개, 이미 "~해요" 동사체)을 §4.3 동사 태그 설계의 씨앗으로 쓸지, 아니면 O*NET 신규 설계로 갈지 결정 필요.

4. **연봉·전망 필드 제거 방식**
   `job_info.csv`에는 `직업현황_직업전망`, `직업현황_임금수준 및 직업만족도`, `학과전망_취업률`, `학과전망_졸업 후 첫 직장 월평균 임금` 등 금지 필드가 포함된다. MAPZ Phase 0에서 파일 이관 시 **컬럼 삭제본을 만들어 저장할지, 원문 그대로 두고 로드 시 필터할지** 정책 결정 필요.

5. **`content.db` 검토 여부**
   MAPS 통합 SQLite(5 MB). 스키마에 등급/매칭 흔적이 있을 가능성이 있어 자동 제외했으나, MAPZ가 커리어넷 원문 대신 이 DB를 소스로 쓰면 편할 수 있다. 사람이 스키마를 훑어보고 이관 여부 재결정할 여지 있음.

---

## 부록 A. Step 1 원자료 (조회 결과)

- 프로젝트 루트: `D:/project/MAPS/`
- 후보 확장자 검색 결과(`.faiss/.index/.pkl/.npy/.json/.csv/.py`, maxdepth=3): 위 파일 목록 참조
- `.gitignore` 확인: 대용량 은닉 = `curriculum_files/`(3.3 GB, 원본 첨부, MAPZ 불필요), `datacrawling/major_info.csv`·`datacrawling/job_info.csv`·`datacrawling/raw/`(재수집 산출물), `성취기준.xlsx`(19 MB, MVP 밖), `학과직업추천_전체.zip`(4.1 MB)
- 키워드 grep 결과:
  - `BGE-M3|bge-m3|SentenceTransformer|sentence_transformers|RRF|reciprocal_rank`: 실제 소스 hit **0건**. 두 계획 MD(`MAPS_ASSET_QUERY.md`, `MAPS_to_MAPZ_자산이관_판단표.md`)만 매칭
  - `FAISS|faiss|Annoy|hnsw`: 실제 소스 hit **0건**
  - `동사|verb|action|activity_tag|verb_tag`: 태그 스키마 hit 0건(문서에서 "임베딩 유사도" 언급 1건, 자연문 "동사 서술" 언급 등 문서 레벨만)
- 임베딩류 파생물의 실체는 **TF-IDF(scikit-learn `TfidfVectorizer`)** 기반임을 `datacrawling/ai학과직업추천_코드_통합버전.py`의 `tfidf_matrix = vec.fit_transform(...)` 라인으로 확인
