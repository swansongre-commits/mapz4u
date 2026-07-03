# MAPZ 운영버전 아키텍처 (real/)

- 작성일 2026-07-04 · 트랙: 운영(`mapz/real/`), MVP(`mapz/`)와 완전 분리(코드 복사, import 없음)
- 데이터: **실데이터 우선** — TourAPI(문화시설·축제) + 정보나루(인기대출 파일). SEED는 결측 보강용(이번 실행 0건).

## 1. 파이프라인 (Phase 0 → 0.5 → 1 → … → 9)

```
[Phase 0.5 관심사추출] extract_topics.py
   수요=정보나루 실대출 4000행 + 연결=TourAPI 2680시설 → 2×2 → topics_v1.json (12주제)
        │
[Phase 1 수집] collect_tourapi.py(실시설2680/축제171) → collect_experiences.py(태깅)
   collect_books.py(정보나루 실대출) · collect_people.py(12) · collect_jobs.py(maps자산)
        │
[Phase 2 검토] validate.py → data/clean/*.json
[Phase 3 연계] build_linkage.py (TF-IDF 코사인, 편성+인접+발견쿼터)
[Phase 4 DB]  build_db.py → db/mapz_real.db (+recheck_queue) + index.pkl
[Phase 7 앱]  app/main.py (FastAPI, 동적12주제, rate-limit, 출처footer)
[운영 §3] refresh.py(일배치) · freshness.py(재확인큐·만료감시)
[운영 §4] deploy/(Docker+nginx)  [§5] rate-limit  [§6] admin/(제휴콘솔)  [§7] docs/legal
```

## 2. MVP와의 차이 (구현된 것)
- 주제: 5개 하드코딩 → **실데이터 자동추출 12개**(공룡·로봇 탈락, 그림·역사·과학 부상).
- 데이터: SEED 위주 → **TourAPI/정보나루 실데이터**(체험 100% 실데이터).
- 갱신: 1회성 → **refresh 배치 + 재확인 큐(90일) + 만료 감시 대시보드**.
- 배포: 로컬 → **Docker Compose + nginx**(정적서빙·rate limit·TLS 슬롯).
- 인증: 없음 → **앱/프록시 2중 rate limit + 관리자 Basic 인증(제휴콘솔)**.

## 3. 동적 주제 처리
- `common.load_topics()`는 하드코딩 없이 `topics_v1.json`만 로드(없으면 명시적 에러 → "조용한 하드코딩 대체" 원천 차단, §2.6).
- 앱은 DB `topic` 테이블에서 주제·색상(12색 팔레트)·수요·연결 점수를 읽어 화면 구성.

## 4. 신선도 불변식 (동일 유지)
`status='운영중' AND (period_end IS NULL OR period_end>=today)` — 만료 자동 숨김. TourAPI 축제 307건은 수집 단계에서 종료분 제외(실기간 기반).

## 5. 재현성
각 스크립트 멱등. `refresh.py`가 전 단계 재실행. 주제·데이터가 바뀌어도 코드 불변(동적).
