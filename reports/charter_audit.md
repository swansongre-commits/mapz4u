# 제품 헌장 감사 (5조) — 구현 증거 매핑

| 조 | 헌장 | 구현 증거(코드/화면 위치) | 판정 |
|---|---|---|---|
| 1조 | 배제를 늦춘다 (결정을 돕지 않는다) | 매칭·추천 알고리즘 없음. '옆으로 한 칸' 확산 편성(`scripts/build_linkage.py` adjacency, `app/templates/topic.html` .sidestep) + 발견피드 쿼터(`app/main.py::api_discover`) → 좁히지 않고 넓힘 | PASS |
| 2조 | 판정하지 않는다 (등급·백분위·또래·유형 금지) | 금지어 lint 0건(`scripts/lint_forbidden.py`), 권장연령 회색 참고표기(`app/static/style.css .age`, "권장 …(참고)"), 인기순 단일정렬 없음(`api_discover` sort='quota(no-popularity)') | PASS |
| 3조 | 불안으로 팔지 않는다 | 광고·불안 카피 0(lint+페르소나), 도서 CTA는 '도서관 소장 조회'만(구매링크 후순위, `macros.html book_card`), footer 정직 표기 | PASS |
| 4조 | 화면은 예고편이다 (현실 전환) | 1차 CTA=길찾기(OSM 좌표 딥링크, `app/main.py::exp_row maplink`, `macros.html exp_card .btn`), 도서=소장 조회. 지도 팝업도 길찾기 링크 | PASS |
| 5조 | 기록은 아이의 것이다 (비수집·삭제권) | 무계정 익명 이용(로그인·세션·쿠키 코드 0), DB에 사용자/이력/개인정보 테이블 0(topic/experience/book/person/job/edge만), 행동엣지(대출 동시발생) 미생성 | PASS |

## 부수 원칙 감사
- **신선도(H2)**: `status='운영중' AND period_end>=today` 불변식 — 만료 시드 3건 全응답 미노출(test_freshness). 응답에 last_verified 노출.
- **재료-기능 분리(§A-8/ADR-004)**: MAPS 자산은 데이터만 반입(직업 17건 source_asset='maps_assets'), 매칭·추천·UI 코드 불반입.
- **도서 중립성(§4.6)**: 도서관 대출 우선, 구매링크 후순위(구매링크 아예 없음).

전 조 PASS. 위반 0.
