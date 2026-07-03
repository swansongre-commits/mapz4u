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
