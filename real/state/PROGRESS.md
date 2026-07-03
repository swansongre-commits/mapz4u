# MAPZ 운영버전(real/) PROGRESS

- **상태**: COMPLETE (정상 완료)
- **데이터**: 실데이터(TourAPI + 정보나루 파일), SEED 0건
- **주제**: Phase 0.5 실데이터 추출 12개

## 로그
- [2026-07-04] real/ 구조 생성, common.py(하드코딩 주제 없음)
- [2026-07-04] TourAPI KorService2 실데이터: 문화시설 2680 + 축제 171
- [2026-07-04] 정보나루 인기대출 파일 4개(연령대별 4000행) 수신·파싱
- [2026-07-04] Phase 0.5 실데이터 추출 → 12주제 (공룡·로봇 탈락, 그림·역사·과학 부상) G0.5 PASS
- [2026-07-04] 수집(체험1568/도서76/인물12/직업59) → 검토 G2 PASS → 연계 G3 PASS → DB G4 PASS
- [2026-07-04] 앱(동적12주제·rate-limit·출처footer) 4화면+6API 200 → 테스트 G8 PASS(pytest11/lint0/E2E/커버리지93)
- [2026-07-04] §3 갱신배치+신선도(만료노출0) · §4 Docker+nginx · §5 2중 rate-limit · §6 제휴콘솔(인증검증) · §7 법적문서
- [2026-07-04] **COMPLETE** — 실행: uvicorn app.main:app --port 8000
