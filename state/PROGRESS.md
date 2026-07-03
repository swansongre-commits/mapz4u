# MAPZ PROGRESS

- **중단 사유(최신)**: 진행 중 (정상)
- **MODE**: MIXED · **EMBED_TIER**: 3 (TF-IDF) · **MAPS_ASSETS**: TRUE

## 진행 로그
- [2026-07-04] Phase 0 시작 — 폴더/venv/의존성 설치 완료, MAPS 자산 10개 반입, MODE=MIXED 판정, 서브에이전트 4종 생성
- [2026-07-04] Phase 0 게이트 G0 확인 대기 → 커밋
- [2026-07-04] Phase 1 완료 — 체험 189(상설 169[OSM 139 실데이터+SEED 40]+행사 20, 만료 3), 도서 50, 인물 5(반고정관념 4), 직업 25(자산 17+생성 8). G1 PASS. 행동엣지 미생성(API 미활성).
- [2026-07-04] Phase 2 완료 — 정제: 체험189/도서50/인물5/직업25, 스키마 100%, 주제당 상설 min=17(>=8). G2 PASS.
- [2026-07-04] Phase 3 완료 — TF-IDF 연계: 주제별 편성표(체험8/도서5/인물1/직업≤5) + 인접(우주↔로봇0.78 등) + 발견피드 쿼터. G3 PASS(빈슬롯0).
- [2026-07-04] Phase 4 완료 — SQLite db/mapz.db (experience189/book50/person5/job25/topic5, edge125), 벡터 인덱스 sklearn 폴백(faiss 미설치). G4 PASS(행수일치+무결성).
