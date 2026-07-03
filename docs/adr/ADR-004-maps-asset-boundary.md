# ADR-004 — MAPS 자산 재사용 경계 (Layer A/B/C 분리, 재료-기능 분리)

- 상태: 채택 · 2026-07-04

## 맥락
MAPS(고교·진로 백엔드)의 자산을 MAPZ에 반입하되, MAPS의 매칭·추천 로직·개인정보·UI는 이관하면 안 된다(§A-8, 판단표). 매니페스트 조사 결과 MAPS엔 BGE-M3 임베딩·FAISS·RRF 실체가 없고 TF-IDF 파생물뿐이었다.

## 결정
반입 = **데이터(벡터·텍스트)만**. 기능(매칭·추천·등급·UI)은 불반입.
- **반입**: 커리어넷 원문 CSV(연봉·전망 컬럼은 로드 시 제외), junior_jobs/kid_blurbs(어린이 서술), synonyms_merged(동의어), tfidf_ref(참고).
- **불반입**: recommender.py·career_recommender.py·streamlit UI·content.db(등급/매칭 스키마 우려).
- **경계**:
  - Layer A(임베딩) = 엣지 전용, 화면 비노출. 벡터 부재로 MAPZ가 TF-IDF 신규 색인.
  - Layer B = 직업을 동사 서술 인물 카드로 변환(연봉·전망·요구학력 제거). `job` 테이블 `source_asset` 컬럼으로 반입/생성 추적.
  - Layer C = MVP 밖(확장 여지만).

## 근거
헌장 2·3조(판정·불안 금지)와 §A-8(재료이지 기능이 아니다). 금지 필드(연봉·전망)를 데이터 로드 단계에서 차단해 화면까지 누출 0.

## 결과
`data/maps_assets/` 10파일 반입, 직업 25건 중 17건 자산 유래(source_asset='maps_assets'), 8건 생성. Layer B 카드 5종은 어린이 대면 품질을 위해 생성 동사 서술로 고정.
