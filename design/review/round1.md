# 디자인 리뷰 Round 1 (design-reviewer)

1. [FAIL] 금지어 검사 — topic.html:67 `<p class="section-note">도서관에서 빌려 읽어요. 필독·수준 같은 건 없어요.</p>` 의 렌더 텍스트에 금지어 **"필독"**이 그대로 노출됨(topic_d 스크린샷 '더 깊이' 섹션에서 육안 확인). 금지어를 부정하는 문장이라도 렌더 텍스트에 단어가 존재하면 규칙상 FAIL. 그 외 화면(search/map/discover)의 렌더 텍스트에는 등급·백분위·또래·비교해·수준별·레벨테스트·지금 안 하면·늦기 전에·골든타임·선행·유형입니다 등 미검출.
   → 수정 지시: 해당 문구를 금지어를 인용하지 않는 표현으로 교체. 예) "도서관에서 빌려 읽어요. 숙제가 아니라 이 세계를 더 볼 수 있는 책이에요."

2. [PASS] 인기순 단일 정렬 없음 — discover.html:10 `<div class="discover-note">🔀 인기순으로 줄 세우지 않아요. 가까운 세계 하나, 안 가본 먼 세계 하나, 그리고 한 사람의 이야기를 골고루 섞어요.</div>` + `<h2>가까운 세계 — 동물</h2>` / `<h2>안 가본 먼 세계 — 우주</h2>` / `<h2>한 사람의 이야기</h2>` 쿼터 편성 구조. 순위 숫자·인기 라벨 없음. discover_m 스크린샷에서 확인.

3. [PASS] 아이 진입 화면 그림 타일 우선 — search.html:13 `.tiles` 격자에 `<span class="emoji">🦕</span>` 등 5개 이모지 타일(공룡/우주/동물/로봇/그림), style.css:29 `.tile .emoji{font-size:2.6rem}` 로 그림이 지배적. search_m 스크린샷에서 큰 이모지 타일 격자 확인.

4. [PASS] 터치 타깃 ≥ 44px — style.css:38 `.btn{min-height:44px;min-width:44px}`, :43 `.chip{min-height:44px}`, :21 `nav.tabs a{min-height:44px}`, :68 `.sidestep a{min-height:44px}`, :27 `.tile{min-height:120px}`, :37 `.searchbar input{min-height:48px}`. 버튼/칩/타일/탭 모두 44px 이상.

5. [PASS] 명도 대비 AA 근사 — style.css:3 본문 `--ink:#1F2328` on `--bg:#FBFAF7`(대비 약 15:1), :4 `--primary:#2C6E63`+`--primary-ink:#FFFFFF` 버튼(약 4.9:1로 큰 텍스트 AA 충족). search_m/topic_d 스크린샷상 본문·버튼 가독 양호. (참고: `--age`/`--verified`의 `--ink-faint:#8A9099`는 참고용 소형 부가정보로 의도적 저대비.)

6. [PASS] 자동재생·무한스크롤 없음 — 4개 HTML 전체에 `<video autoplay>`·캐러셀·무한 로딩 스크립트 부재. discover.html:10 셔플은 `<button class="btn ghost">🔀 다른 것 섞어보기</button>` 명시적 사용자 클릭 방식(자동 아님).

7. [PASS] 권장 연령이 등급/판정처럼 보이지 않음 — search.html:17 `<span class="age">권장 전연령 (참고)</span>`, style.css:52 `.age{color:var(--ink-faint);font-size:.82rem;font-weight:400}` 회색·소형·비강조 참고 표기. topic.html:69 도서도 `권장 7-10세 (참고)` 동일 스타일. 등급 배지·판정 색상 아님.

8. [PASS] 최종확인일·시드 배지 노출 — 모든 카드에 `<span class="verified">최종 확인 2026-07-04</span>` 존재, `<span class="badge-seed">표본(검증 필요)</span>`(style.css:54) 또는 `<span class="badge-live">실데이터</span>`(:56) 노출. footer에도 신선도 문구 상시 표기.

9. [PASS] 도서 소장/대출 가능 표기 자리 존재 — topic.html:70 `<div class="avail">🏫 소장 도서관·대출 가능 여부 조회 →</div>` + :71 CTA `<a class="btn ghost">도서관 소장 조회</a>`, style.css:78 `.avail{...color:var(--focus)}`. 도서 5권 각각에 존재.

10. [PASS] 1차 CTA가 현실 전환이며 상단·강조 — 체험 카드 `.cta-row` 첫 버튼이 강조 스타일 `.btn`(primary 배경)의 `길찾기 →`(search.html:19 OpenStreetMap 링크), 두 번째는 `.btn.ghost`(topic.html:20 '주제 더보기') 보조. 도서 카드는 `도서관 소장 조회`가 현실 전환 CTA. 순위·상단 배치 정상.

SCORE: 9/10
VERDICT: REVISE
