# MAPZ 아키텍처 (ARCHITECTURE.md)

- 작성일: 2026-07-04 · MODE: MIXED · EMBED_TIER: 3 · MAPS_ASSETS: TRUE
- 목표: 로컬 단일 머신, 외부 배포 없음. 무인 재현성 우선.

## 1. 시스템 개요

```
[수집 스크립트]  scripts/collect_*.py  ── OSM Overpass(실데이터) + SEED(§D-1)
        │  data/raw/*.json
        ▼
[검토] validate.py ── 스키마·좌표·중복·주제매핑 ──▶ data/clean/*.json
        ▼
[연계] build_linkage.py ── TF-IDF(char2-4gram) 코사인 ──▶ linkage.json + db/vectors.pkl
        ▼
[DB]  build_db.py ── SQLite db/mapz.db (5 노드 + edge) + db/index.pkl(sklearn NN)
        ▼
[앱]  app/main.py (FastAPI) ── 4 화면 + 6 API ── Jinja2 템플릿 + vanilla JS + Leaflet/OSM
```

## 2. 노드 5종 (그래프)
주제(topic) · 체험(experience) · 인물(person) · 직업(job) · 도서(book). 관계는 `edge` 테이블(semantic/adjacent/lineage).

## 3. 계층 분리 (MAPS 자산 경계)
- **Layer A**: 임베딩(엣지 전용, 화면 비노출). MAPS엔 벡터 실체 없어 커리어넷 원문/키워드에서 MAPZ가 TF-IDF 신규 색인.
- **Layer B**: 주제관 '이 세계의 어른들' — 직업을 동사 서술 인물 카드로(연봉·전망 제거). 초등 노출.
- **Layer C**: 정식 학과·직업(중등·부모). MVP 범위 밖(스키마 확장 여지만 확보: job.source_asset).

## 4. 신선도 규칙 (구현 불변식)
모든 목록 응답에서 `status != '운영중'` 또는 `period_end < today` 제외. 응답에 `last_verified`·`is_seed` 포함. "만료 정보 노출 0건"이 품질 제1지표.

## 5. 스택 (ADR 참조)
Python 3.10+ / FastAPI / SQLite / Jinja2 / vanilla JS / Leaflet + OpenStreetMap 타일(키 불필요).

## 6. API 명세 (Phase 7 구현 대상)

| 메서드 | 경로 | 역할 |
|---|---|---|
| GET | /api/topics | 5개 주제 + 이모지 타일 |
| GET | /api/topics/{id} | 주제관: 상설/행사/도서/인물카드/옆으로한칸 |
| GET | /api/search?q=&indoor=&free=&region= | 아이 언어 검색(동의어) + 부모 필터 |
| GET | /api/map?bbox=&topics= | 지도 마커(운영중만) |
| GET | /api/discover | 발견 피드(쿼터 편성, 인기순 금지) |
| GET | /healthz | 헬스체크 |

화면 라우트: `/`(검색) · `/topic/{id}`(주제관) · `/map`(지도) · `/discover`(발견 피드).

## 7. 데이터 흐름 재개(멱등)
각 스크립트는 입력 clean/raw 존재 시 재생성 가능. state/pipeline_state.json 으로 Phase 재개.
