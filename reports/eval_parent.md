# MAPZ 학부모(persona-parent) 평가 — eval_parent.md

평가일: 2026-07-04 · 대상: reports/rendered/{search,topic,map,discover}.html + design/screenshots/*.png + data/clean/linkage.json + DECISION_LOG.md

## 루브릭 10항 채점

1. **[PASS]** 30초 내 '이번 주말 갈 곳' 도달 — search.html:22-25 검색바 + search.html:47-86 "가까운 체험처 미리보기" 카드(계룡산자연사박물관 등)가 첫 화면에 즉시 노출. map.html:40 "운영 중 체험처 (186곳)" + design/screenshots/map_d.png "이번 주말·실내·무료" 섹션으로 지도 진입도 단순.

2. **[FAIL]** 실내·무료 필터 실제 작동 — search.html:27-30 실내/무료 칩(`data-f="indoor"` `data-f="free"`)이 존재하나, search.html 전체에 `<script>` 블록·클릭 핸들러·쿼리파라미터가 전혀 없음(Grep `<script>` = No matches). 칩이 `aria-pressed="false"` 정적 상태로만 렌더되어 눌러도 목록이 필터링되지 않음. (대조: map.html:89 `.topic-toggle`는 addEventListener로 실제 작동.) 부모가 "무료만" 걸러 보려는 핵심 동작이 검색 화면에서 무효.

3. **[PASS]** 만료 정보 미노출 — map.html:24 "지난 행사는 지도에 나오지 않아요(신선도)", DECISION_LOG.md:62 불변식 `status='운영중' AND (period_end IS NULL OR period_end>=today)` 구현, DECISION_LOG.md:67 만료 시드 3건 全응답 미노출 테스트 PASS. 렌더 4화면에 종료 행사 카드 없음.

4. **[PASS]** 허탕 방지 정보 — search.html:53 `예약 필요`, topic.html:43 `자유 관람`, 모든 카드에 search.html:55 `최종 확인 2026-07-04`(verified) 표기. 운영시간(search.html:52 `🕒 09:30-18:00`)도 노출.

5. **[PASS]** 비용 표시 — search.html:51 `💰 성인 9000원 어린이 6000원`, 데이터 없는 OSM건은 topic.html:41 `💰 현장 확인`으로 정직하게 표기. 무료 대상은 discover.html 등에서 비용 필드 일관 노출.

6. **[PASS]** 길찾기 1탭 — 모든 카드 search.html:56 `<a class="btn" href="https://www.openstreetmap.org/?mlat=...#map=17/...">길찾기 →</a>`, 실좌표 OSM 딥링크로 1탭 전환. map.html 마커 팝업에도 동일 링크(map.html script `bindPopup ...길찾기`).

7. **[PASS]** 도서 대출/소장 정보 표기 — topic.html:121 `🏫 소장 도서관·대출 가능 여부 조회 →` + topic.html:123 `<a class="btn ghost">도서관 소장 조회</a>` CTA + 저자·출판사·권장연령 표기. (주의: CTA href="#"로 실제 이동 미연결 — 표기는 있으나 조회 기능 미완.)

8. **[PASS]** 광고·불안 문구 0건 — 4화면 어디에도 광고 배너·"필독/마감임박/서두르세요" 류 없음. DECISION_LOG.md:69 금지어 lint 위반 0건. 인물 카드도 topic.html:167 "연봉·전망 같은 건 보여주지 않아요"로 불안 요소 배제.

9. **[PASS]** 시드 배지 정직성 — 검증필요 데이터는 search.html:55 `표본(검증 필요)`(badge-seed), 실데이터는 topic.html:45 `실데이터`(badge-live)로 구분 표기. 푸터(search.html:90-91)도 "표본(검증 필요) 데이터 포함 … 정직하게 알려요" 명시. linkage.json score까지 근거 보유.

10. **[PASS]** 아이 혼자 봐도 안전 — 결제유도 없음, 외부링크는 OSM 지도/도서관 조회로 target="_blank" rel="noopener" 처리(search.html:56). 자극적 이미지·랭킹경쟁 없음, discover.html:22 "인기순으로 줄 세우지 않아요" + discover.html:61 "끝이 있는 화면"으로 무한스크롤·중독 설계 배제.

## 개선 제안
1. **(치명)** search.html 실내/무료/지역/이번주 칩에 JS 핸들러 또는 GET 쿼리(`?f=free`) 연동을 붙여 실제 필터링되게 할 것. 현재 부모 핵심 동작이 죽어 있음.
2. topic.html 도서 "도서관 소장 조회" CTA의 `href="#"`를 실제 소장/대출 조회 링크(예: 도서관정보나루/지역도서관 검색 URL)로 연결.
3. topic/discover의 OSM 실데이터 카드가 "현장 확인·운영시간 확인"만 표기 → 허탕 방지를 위해 대표 전화·공식 홈페이지 링크 1개라도 보강하면 신뢰도 상승.

SCORE: 9/10
VERDICT: PASS

## 라운드2 재검증 (2026-07-04)

라운드1 FAIL이던 **2항(실내·무료 필터)** 만 재검증. 나머지 9항은 라운드1 결과 유지.

2. **[PASS]** 실내·무료 필터 실제 작동 — 갱신된 search.html:26 필터가 정적 칩에서 실제 GET 폼(`<form class="chips" method="get" action="/" id="filterForm">`)으로 교체됨. search.html:29 `<input type="checkbox" name="indoor" value="1" hidden onchange="this.form.submit()">`, :31 `name="free"`, :33 `name="week"` 및 :34 `name="region"` 텍스트 입력이 모두 onchange 자동 제출로 서버에 쿼리 전달. app/main.py page_search가 indoor/free/region/week를 수신해 api_search로 실제 필터링(코디네이터 확인: 무료 18건 전부 무비용, 실내 182건 전부 실내, 서울 12건 전부 서울)하고 회귀 테스트 test_search_page_filters_work 통과. 부모 핵심 동작(무료만/실내만 걸러 보기) 복구됨. 부수 개선: 도서 CTA href="#" → 국립중앙도서관 제목검색 실링크로 교체(라운드1 개선제안 2 반영).

**갱신 결과**: 2항 FAIL → PASS. 10항 全 PASS.

SCORE: 10/10
VERDICT: PASS
