# MAPZ persona-career 평가 (진로교육)

평가일: 2026-07-04 · 평가자: persona-career
대상: reports/rendered/{topic,discover,search}.html, data/clean/{linkage,jobs,people}.json, reports/DECISION_LOG.md, scripts/build_db.py

## 루브릭 10항

1. **[PASS]** 동사 태그 저장·표시. jobs.json:10 `"verb_tags":["탐구하다"]` + jobs.json:5 `verb_desc`, topic.html:166 카드에 "땅속에 묻힌 옛 생물의 흔적을 찾아…밝혀내요"(동사 서술) 노출. people.json:9 `verb_desc`도 topic.html:156 "하는 일:"로 표시.

2. **[PASS]** '옆으로 한 칸' 비무작위 — 유사도 로그 존재. linkage.json:571-631 `adjacency`에 점수(dino→animal 0.4358, art 0.2987), linkage.json:633-664 `adjacency_matrix` 전체 기록. topic.html:31-33 상위 2개(동물·그림) 렌더가 점수순과 일치. DECISION_LOG.md:33-39 편성 근거 명시.

3. **[PASS]** Layer A/B 분리. topic.html에 직업 명사 카드는 Layer B 1장(topic.html:165 "화석을 연구하는 사람")만 노출, hidden 직업(지질학연구원 등 jobs.json:17,96)은 미렌더. Layer A(TF-IDF 임베딩/벡터, build_db.py:95-105 index.pkl)는 화면 비노출. layer 필드로 B/hidden 구분(linkage.json:92-113).

4. **[PASS]** 직업 계보 one-to-many(매칭 반대 방향). people.json:15-20 `job_lineage`가 인물 1→직업 4(고생물학자·화석 발굴가·박물관 큐레이터·지질학자). topic.html:157 "이 이야기에서 뻗어나가는 일들 (하나가 여럿으로)" + topic.html:159 4개 태그 렌더. build_db.py:88-90 person→jobname lineage 엣지.

5. **[PASS]** 스키마 확장성 — 커리어넷 필드 수용. build_db.py:24-25 `CREATE TABLE job(... source_asset TEXT ...)`, jobs.json:14 `"source_asset":"generated"` / :28 `"maps_assets"`로 출처 자산 구분 저장, 커리어넷 원문 유입 여지 확보.

6. **[PASS]** DECISION_LOG 추적성. DECISION_LOG.md:23-46 주제별 편성표·인접 점수·발견 쿼터 근거, :14 Layer B 변환(연봉·전망·요구학력 제거) 규칙까지 기록.

7. **[PASS]** 신선도 규칙 구현. build_db.py:28-29 status/period_end 인덱스 + DECISION_LOG.md:62 불변식 `status='운영중' AND (period_end IS NULL OR period_end>=today)`, :67 만료 시드 3건 미노출 테스트 PASS.

8. **[PASS]** 데이터 출처 표기. build_db.py:17-18,21,24 `source`/`is_seed` 컬럼, topic.html:45 `badge-live 실데이터` / :99 `badge-seed 표본(검증 필요)` 배지 + `verified 최종 확인 2026-07-04` 렌더.

9. **[PASS]** 이력층 접속 여지. verb_tags가 배열 구조(jobs.json:150-153 ["돌보다","탐구하다"])라 동사 축적·이력 확장 가능. person job_lineage 엣지(build_db.py:88-90)도 미래 계보 확장 구조.

10. **[PASS]** 공영 중립성 — 구매 링크 없음·도서관 대출 우선. topic.html:116 "도서관에서 빌려 읽어요", :121 "🏫 소장 도서관·대출 가능 여부 조회", :123 "도서관 소장 조회" CTA만 존재. 구매/쇼핑 링크 0건. topic.html:167 "연봉·전망 같은 건 보여주지 않아요", footer "공영 중립".

## 개선 제안
1. hidden 직업의 verb_desc가 커리어넷 원문 절단형("…해요")으로 어색(jobs.json:19 "암석 분포해요", :190 "새로운 품종의 채소해요"). Layer B 동사 서술 규칙을 hidden층에도 적용해 문장 완결성 확보.
2. discover.html 쿼터가 근접·먼 세계 각 1장만 노출(discover.html:26-51) — 표본이 얇아 "골고루 섞기" 취지가 빈약. 슬롯당 2~3장으로 늘려 발견 밀도 보강.
3. `source_asset`이 "generated"/"maps_assets" 2값뿐 — 커리어넷 실제 유입 대비 출처 URL·수집일 필드를 job 테이블에 선반영해 이력층 근거 강화.

SCORE: 10/10
VERDICT: PASS
