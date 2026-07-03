# API 명세 ↔ Phase 7 구현 1:1 대응표 (G5)

각 API가 `app/main.py`의 핸들러와 1:1로 대응하고, Phase 8 테스트가 이를 검증한다.

| # | API 명세 | 구현 핸들러(app/main.py) | 화면/소비처 | 신선도 규칙 | Phase 8 테스트 |
|---|---|---|---|---|---|
| 1 | `GET /api/topics` | `api_topics()` | 검색 상단 주제 타일, 발견 | — | test_api_topics |
| 2 | `GET /api/topics/{id}` | `api_topic_detail(id)` | 주제관 | status/period_end 필터 | test_api_topic_detail |
| 3 | `GET /api/search?q=&indoor=&free=&region=` | `api_search(...)` | 검색 | 만료 제외 | test_search_synonym, test_search_filter |
| 4 | `GET /api/map?bbox=&topics=` | `api_map(...)` | 지도 | 운영중만 | test_api_map_live_only |
| 5 | `GET /api/discover` | `api_discover()` | 발견 피드 | 쿼터 편성·인기순 금지 | test_discover_quota |
| 6 | `GET /healthz` | `healthz()` | 모니터링 | — | test_healthz |
| — | `GET /` `/topic/{id}` `/map` `/discover` (HTML) | `page_*()` | 4 화면 | 렌더 시 만료 제외 | test_e2e_pages(Playwright) |

## 신선도 불변식 (모든 목록 API 공통)
`WHERE status='운영중' AND (period_end IS NULL OR period_end >= :today)` — 만료 행사(시드 만료 3건)는 어떤 응답에도 나오지 않는다(Phase 8 신선도 테스트, 이월 불가).

## 응답 공통 필드
`last_verified`, `is_seed` 포함. `is_seed=1` 이면 화면에 "표본(검증 필요)" 배지.
