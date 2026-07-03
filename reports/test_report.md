# Phase 8 — 테스트 리포트

- 실행일: 2026-07-04 · 수정 루프: 1라운드(TemplateResponse 시그니처 수정)로 전체 통과

## 1. pytest 단위 (tests/test_api.py) — 12/12 PASS
| 테스트 | 검증 | 결과 |
|---|---|---|
| test_healthz | /healthz 200 | PASS |
| test_api_topics | 주제 5개 + 스키마 | PASS |
| test_api_topic_detail | 주제관 편성 + last_verified/is_seed + Layer B | PASS |
| test_api_topic_unknown | 미존재 주제 404 | PASS |
| test_search_synonym | "쥬라기"→공룡 매핑 | PASS |
| test_search_synonym_star | "별"→우주 매핑 | PASS |
| test_search_filter_indoor_free | 실내+무료 필터 | PASS |
| test_freshness_no_expired_anywhere | 만료 시드 3건 全응답 미노출 | PASS |
| test_freshness_status_operating_only | 운영중+미만료만 | PASS |
| test_api_map_live_only | 지도 주제 필터 | PASS |
| test_discover_quota_no_popularity | 발견=쿼터(인기순 없음) | PASS |
| test_pages_render_200 | 4화면 렌더 200 | PASS |

## 2. Playwright E2E (scripts/e2e.py)
- 4화면(검색/주제관/지도/발견) 로드 status=200
- 클릭 흐름: 주제 타일→주제관(space) / 내비→지도 / 내비→발견 모두 성공
- 페이지 예외(uncaught JS): 0
- 콘솔 에러: 0 (Leaflet CDN·OSM 타일 포함 클린)
- **E2E PASS**

## 3. 금지어 lint (scripts/lint_forbidden.py)
- 대상: 렌더링 HTML 텍스트 노드(script/style 제외), 9개 페이지
- 금지어 12종 위반 **0건** → LINT PASS
- (라운드1 '필독' 1건은 디자인 단계에서 이미 수정)

## 4. 커버리지
- app/main.py: **96%** (135 stmts, 6 miss) — 핵심 로직(검색·신선도·편성) ≥70% 충족

## 게이트 G8: PASS (금지어 0 + 신선도 PASS + E2E 콘솔에러 0)
미해결 결함: 없음.
