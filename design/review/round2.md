# 디자인 리뷰 Round 2 (design-reviewer)

1. [PASS] 금지어 0건 — Round 1 지적 반영 확인. topic.html:67 `<p class="section-note">도서관에서 빌려 읽어요. 숙제가 아니라 이 세계를 더 볼 수 있는 책이에요.</p>` 로 교체되어 이전 금지어 "필독" 제거됨. topic_d/topic_m 스크린샷 '더 깊이' 섹션 렌더 텍스트에서 "필독"·"수준" 미검출. 4개 화면(search/topic/map/discover) 렌더 텍스트 전체에 등급·백분위·또래·비교해·필독·수준별·레벨테스트·지금 안 하면·늦기 전에·골든타임·선행·유형입니다 미검출.

2. [PASS] 인기순 단일 정렬 없음 — discover.html:10 `<div class="discover-note">🔀 인기순으로 줄 세우지 않아요...</div>` + `가까운 세계 — 동물` / `안 가본 먼 세계 — 우주` / `한 사람의 이야기` 쿼터 편성. 순위 숫자·인기 라벨 없음.

3. [PASS] 아이 진입 화면 그림 타일 우선 — search.html:13 `.tiles` 격자 5개 이모지 타일(🦕공룡/🚀우주/🐾동물/🤖로봇/🎨그림), style.css:29 `.tile .emoji{font-size:2.6rem}`.

4. [PASS] 터치 타깃 ≥ 44px — style.css:38 `.btn{min-height:44px;min-width:44px}`, :43 `.chip{min-height:44px}`, :21 `nav.tabs a{min-height:44px}`, :68 `.sidestep a{min-height:44px}`, :27 `.tile{min-height:120px}`, :37 `.searchbar input{min-height:48px}`.

5. [PASS] 명도 대비 AA 근사 — style.css:3 `--ink:#1F2328` on `--bg:#FBFAF7`(약 15:1), :4 `--primary:#2C6E63`+`--primary-ink:#FFFFFF` 버튼(큰 텍스트 AA 충족). 스크린샷 가독 양호.

6. [PASS] 자동재생·무한스크롤 없음 — 4개 HTML에 autoplay·캐러셀·무한 로딩 스크립트 부재. discover.html:10 `<button class="btn ghost">🔀 다른 것 섞어보기</button>` 명시적 사용자 클릭.

7. [PASS] 권장 연령이 등급/판정처럼 보이지 않음 — search.html:17 `<span class="age">권장 전연령 (참고)</span>`, style.css:52 `.age{color:var(--ink-faint);font-size:.82rem;font-weight:400}` 회색·소형·비강조.

8. [PASS] 최종확인일·시드 배지 노출 — 모든 카드에 `<span class="verified">최종 확인 2026-07-04</span>` + `<span class="badge-seed">표본(검증 필요)</span>`(style.css:54) 또는 `<span class="badge-live">실데이터</span>`(:56).

9. [PASS] 도서 소장/대출 가능 표기 자리 존재 — topic.html:70 `<div class="avail">🏫 소장 도서관·대출 가능 여부 조회 →</div>` + CTA `도서관 소장 조회`, style.css:78 `.avail{...}`. 도서 5권 각각 존재.

10. [PASS] 1차 CTA가 현실 전환이며 상단·강조 — 체험 카드 `.cta-row` 첫 버튼 `.btn`(primary 배경) `길찾기 →`(OpenStreetMap 링크), 보조는 `.btn.ghost` `주제 더보기`. 도서 카드는 `도서관 소장 조회`가 현실 전환 CTA.

SCORE: 10/10
VERDICT: APPROVED
