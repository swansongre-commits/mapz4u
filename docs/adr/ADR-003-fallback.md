# ADR-003 — 폴백 구조: MODE / EMBED_TIER 분기

- 상태: 채택 · 2026-07-04

## 맥락
API 키 승인 지연·오프라인·모델 다운로드 실패가 무인 완주를 막을 수 있다. 파이프라인은 어떤 환경에서도 완결되어야 한다(§A-2 정지 금지).

## 결정
- **MODE 3단**: API → MIXED(NOKEY 보강) → SEED(모델 지식 생성). 소스별 독립 판정.
- **EMBED_TIER 3단**: 1 BGE-M3 → 2 MiniLM → 3 TF-IDF(char2-4gram).
- **인덱스 폴백**: FAISS 실패 시 sklearn NearestNeighbors.
- **스크린샷 폴백**: Playwright 실패 시 HTML 소스 리뷰.

## 이번 실행의 확정 분기
- MODE=**MIXED**: 키 서비스 전부 미활성(data4library=vitalizationErr, KCISA=404, 박물관표준 미구독, TourAPI=500). 키리스 OSM Overpass 실데이터 139건 + SEED 보강.
- EMBED_TIER=**3**: GPU 없음 + 멀티-GB 모델 다운로드의 무인 재현성 위험 → TF-IDF 채택(MAPS 자산도 TF-IDF 계보라 정합).
- 인덱스=**sklearn NN**(faiss 미설치).
- 스크린샷=**Playwright chromium 설치 성공** → 스크린샷 사용.

## 근거
결정 규칙(§C)을 코드/문서에 명시해, 환경이 달라져도 같은 절차로 다른 티어를 선택. 모든 폴백은 DECISION_LOG·pipeline_state에 기록.

## 결과
`state/env.json` 이 런타임 분기의 단일 소스. 재개 시 이 파일을 읽어 동일 티어 유지.
