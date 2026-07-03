# ADR-001 — 스택 선정: FastAPI + SQLite

- 상태: 채택 · 2026-07-04

## 맥락
로컬 단일 머신에서 사람 개입 없이 재현 가능한 어린이 체험지도 웹서비스가 필요하다. 외부 배포·대규모 트래픽은 비목표.

## 결정
- 백엔드: **FastAPI** (경량, 자동 문서화, httpx/pytest 친화)
- 저장소: **SQLite**(`db/mapz.db`) — 단일 파일, 무설치, 재현성 최상
- 템플릿: **Jinja2** + **vanilla JS**(빌드 스텝 없음)

## 근거
- 무인 재현성: 별도 DB 서버·컨테이너 불필요, 파일 복사로 이식.
- MVP 규모(노드 수백 건)에 SQLite 충분, 인덱스로 신선도 쿼리 대응.
- FastAPI는 스키마 검증·테스트(pytest+httpx)가 쉬워 Phase 8 게이트에 유리.

## 대안
- Django(과중), Flask(문서화·검증 수작업), Postgres(로컬 무인엔 과설비). 모두 재현성·경량성에서 열위.

## 결과
`app/main.py` 단일 진입점, `uvicorn app.main:app --port 8000` 로 기동.
