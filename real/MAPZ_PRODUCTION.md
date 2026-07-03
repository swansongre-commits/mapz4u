# MAPZ_PRODUCTION.md — 실제 운영버전 확장 계획서 (v1.1, 폴더 분리 반영)

- **작성일**: 2026-07-04
- **전제**: `MAPZ_AUTOPILOT.md`(v2.0)로 진행 중인 MVP 무인 완주 실행은 "무인 파이프라인 구조가 작동하는가"를 검증하는 실험이며, 그 결과물은 하드코딩된 주제 5개·SEED 위주 데이터로 채워진 **로컬 전용 표본**이다.
- **이 문서의 목적**: 그 검증이 끝난 뒤, 같은 파이프라인 뼈대 위에 **실제 서비스로서 필요한 것**을 얹는 확장 계획. MVP 실행 중인 파이프라인을 지금 건드리지 않고, **완전히 분리된 폴더(`mapz/real/`)**에서 별도 트랙으로 진행한다.
- **핵심 결함(계기)**: 정보나루·공공데이터포털 API는 원래 "실제 많이 찾는 것을 데이터로 뽑기 위해" 받은 것인데, AUTOPILOT MVP는 주제 5개를 미리 하드코딩해 그 목적을 쓰지 못했다. 실운영버전은 이걸 **Phase 0.5로 정식 편입**해 바로잡는다.

---

## 0. 폴더 분리 원칙 (v1.1 신설 — 최우선 규칙)

### 0.1 MVP 산출물은 어떻게 되는가

**그대로 둔다. 손대지 않는다.** 현재 `mapz/` 루트(`data/`, `db/`, `app/`, `scripts/`, `state/`, `reports/`, `design/`, `docs/` 등)에 쌓인 MVP 결과물은 "무인 완주가 가능한가"라는 원래 질문의 답이자 검증 기록이므로 삭제·수정·덮어쓰기 금지. `reports/FINAL_REPORT.md`가 나오면 그 상태로 스냅샷 보존한다.

### 0.2 운영버전은 완전히 새 폴더에서

운영버전(본 문서가 다루는 모든 것)은 **`mapz/real/` 하위에 독립된 프로젝트처럼** 구성한다. `mapz/` 루트의 파일을 참조하거나 import하지 않는다 — 코드는 복사해서 새로 시작하고, 데이터는 처음부터 다시 수집한다(SEED가 아니라 실데이터로).

```
mapz/
├── (기존 MVP 산출물 — 그대로 유지, 건드리지 않음)
│   ├── data/  db/  app/  scripts/  state/  reports/  design/  docs/  .claude/
│
└── real/                              ← 운영버전 전용 루트 (v1.1 신설)
    ├── .claude/agents/
    ├── state/                          # pipeline_state.json, PROGRESS.md (운영판 별도)
    ├── data/{raw,clean,topics,maps_assets}/
    ├── db/                             # mapz_real.db
    ├── docs/adr/
    ├── design/{screenshots,review}/
    ├── app/{templates,static}/
    ├── scripts/
    ├── tests/
    ├── reports/
    ├── deploy/                         # Dockerfile, docker-compose.yml, nginx 설정 (§4 신설)
    └── admin/                          # 제휴 콘솔 (§6 신설)
```

### 0.3 경로 치환 규칙

본 문서 전체와 실행 시 생성되는 모든 스크립트·설정에서, MVP AUTOPILOT.md가 사용하던 상대경로 표기는 전부 `real/`을 접두어로 붙인다.

| MVP(mapz/ 루트 기준) | 운영(mapz/real/ 기준) |
|---|---|
| `data/raw/`, `data/clean/` | `real/data/raw/`, `real/data/clean/` |
| `db/mapz.db` | `real/db/mapz_real.db` |
| `app/main.py` | `real/app/main.py` |
| `scripts/collect_*.py` | `real/scripts/collect_*.py` |
| `state/pipeline_state.json` | `real/state/pipeline_state.json` |
| `reports/FINAL_REPORT.md` | `real/reports/FINAL_REPORT.md` |
| `.claude/agents/` | `real/.claude/agents/` (운영 전용 서브에이전트, MVP와 별도 정의 가능) |

Claude Code가 운영 트랙을 실행할 때는 **작업 디렉토리 자체를 `mapz/real/`로 진입**해서 진행하는 것을 원칙으로 한다(§9 실행 지시에 반영).

---

## 1. MVP와 실서비스의 차이 (재정리)

| 영역 | MVP(`mapz/`, AUTOPILOT 현재) | 실서비스(`mapz/real/`, 본 문서) |
|---|---|---|
| 주제 | 5개 하드코딩 | **실데이터 기반 자동 추출**(§2), 확장 가능한 개수 |
| 데이터 | SEED(모델 지식 생성) 위주 | API/NOKEY 실데이터 우선, SEED는 결측 보강용으로 축소 |
| 배포 | 로컬(`localhost:8000`)만 | 실서버 배포, 도메인, HTTPS |
| 데이터 갱신 | 1회성 수집 후 종료 | 상시 스케줄러(Tier 1~4 운영) |
| 인증·보호 | 없음(로컬 요청만) | 요청 제한, 봇 방어, 필요 시 계정 체계 |
| 개인정보 | 설계 문서만 존재 | 법정대리인 동의 플로우 실제 구현 |
| 디자인 검증 | design-reviewer 자동 승인 | 위 + 실사용자 대상 검증(선택) |
| 목적 | "무인 완주가 되는가" 검증 | 실제 어린이·부모에게 서비스 제공 |

MVP 파이프라인의 Phase 0~9 구조(수집→검토→연계결정→DB→아키텍처→디자인→개발→테스트→평가) 자체는 그대로 재사용한다. 단, **실행 위치가 `mapz/real/`로 바뀌고**, 아래는 그 위에 추가·수정되는 것만 다룬다.

---

## 2. Phase 0.5 — 관심사 추출 (신설, 최우선 수정)

### 2.1 문제

AUTOPILOT MVP는 기획서 §7("관심사 사전 구축")의 절차를 생략하고 `common.py`에 주제 5개(공룡·우주·동물·로봇·그림)를 직접 박아 넣었다. 정보나루·문화정보원 API 키는 이 5개에 대한 체험·도서를 "채우는" 용도로만 쓰였고, 원래 목적이었던 "무엇이 실제로 인기 있는가를 찾아내는" 역할을 하지 못했다.

### 2.2 위치

`mapz/real/` 트랙의 Phase 0(환경 셋업) 직후, Phase 1(자료수집) 이전에 삽입한다. Phase 1은 이제 "Phase 0.5가 확정한 주제 목록"을 입력으로 받아 동작한다.

### 2.3 절차 (기획서 §7 그대로 실행)

1. **수요 코퍼스 수집**
   - 정보나루 인기대출도서 API — 연령대별(미취학/초저/초중고) 상위 대출 도서 목록, 각 도서 제목·주제어(KDC)
   - 알라딘/예스24 어린이 베스트셀러 (보강)
   - 네이버 데이터랩 검색 트렌드 (보강, 계절성 확인용)
   - EBS 내부 로그가 있으면 최우선 반영(가장 직접적인 신호)
2. **명사구 추출** — 도서 제목·부제에서 형태소 분석기(예: kiwipiepy, 없으면 정규식 기반 간이 추출)로 핵심 명사구 추출
3. **클러스터링 + 동의어 통합** — BGE-M3(또는 EMBED_TIER 폴백)로 임베딩 후 클러스터링, 동일 개념 병합(공룡=화석=쥬라기 등)
4. **연령대별 빈도 프로파일** 산출 — 각 관심사 후보의 미취학/초저/초중고 분포 확인
5. **연결 스코어링** — 각 후보 × {체험 가능성(문화정보원 API 매칭 건수), 도서 확보량, 인물 존재 여부} 로 2×2 매트릭스(기획서 §7) 적용
6. **주제 확정** — 수요 高·연결 高 우선으로 **상위 N개**(기본 12개, 운영 중 확장) 자동 채택. MVP의 5개(공룡·우주·동물·로봇·그림)는 폐기하지 않고 교차검증용 참고셋으로 `mapz/real/data/topics/mvp_reference.json`에 별도 보관

### 2.4 산출물 (경로: `mapz/real/` 기준)

- `real/data/topics/topics_v1.json` — 자동 추출된 주제 사전 (주제명, 동의어, 연령 프로파일, 빈도 점수, 연결 스코어)
- `real/reports/topic_extraction_report.md` — 추출 과정·근거 수치·MVP 5개와의 비교

### 2.5 게이트

주제 수 ≥ 8, 각 주제당 최소 데이터 확보 가능성(체험 3건 이상 매칭 예상) 확인. 미달 시 다음 순위 후보로 대체.

### 2.6 common.py 구조 (real/scripts/common.py — MVP와 별개 파일)

```python
"""MAPZ 운영버전 공용 유틸. mapz/real/ 하위 전용 — MVP(mapz/scripts/common.py)와 분리."""
import os, json
REAL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # mapz/real/
def rp(*a): return os.path.join(REAL_ROOT, *a)

def load_topics():
    path = rp("data", "topics", "topics_v1.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    # Phase 0.5 미실행/전량 실패 시에만 폴백 — MVP 참고셋 재사용
    ref = rp("data", "topics", "mvp_reference.json")
    if os.path.exists(ref):
        return json.load(open(ref, encoding="utf-8"))
    raise RuntimeError("Phase 0.5가 완료되지 않았고 MVP 참고셋도 없음 — 주제 사전 확정 불가")
```

**원칙**: 운영판 `common.py`는 MVP의 `mapz/scripts/common.py`를 import하지 않는다. 완전히 새 파일로 둔다. 하드코딩 주제 딕셔너리 자체를 두지 않고, Phase 0.5 산출물이 없으면 명시적으로 에러를 내서 "하드코딩으로 조용히 대체되는" 상황을 원천 차단한다.

---

## 3. 데이터 갱신 — 1회성에서 상시 운영으로

### 3.1 MVP의 한계

AUTOPILOT Phase 1은 파이프라인 실행 시점에 딱 1회 수집하고 끝난다. 체험 정보는 부패한다(기획서 H2)는 원칙과 정면으로 배치된다.

### 3.2 운영 설계 (모든 스크립트는 `mapz/real/scripts/` 하위)

| Tier | 주기 | 담당 |
|---|---|---|
| Tier 1 (공공 API) | 일 1회 배치 | `real/scripts/collect_*.py`를 cron/스케줄러로 등록 |
| Tier 2 (기관 홈페이지 크롤링) | 주 2~3회 | 변경 감지 diff, 실패 시 알림 |
| Tier 3 (제휴 콘솔) | 실시간(공급자 입력) | `real/admin/`(§6) |
| Tier 4 (사용자 제보) | 실시간 | "다녀왔어요"/오류 제보 API, 반영은 익일 배치에 병합 |

### 3.3 신선도 감시

- 만료 자동 숨김은 MVP에서 이미 구현된 로직을 참고해 `real/app/`에 재구현(코드 복사, import 아님) — 유지
- **추가**: `last_verified` 경과일이 90일 초과한 레코드는 자동으로 "재확인 필요" 큐(`real/db/`)에 등록, 배치 시 우선 재수집
- 신선도 대시보드(MVP Phase 8-6 미니 대시보드 참고)를 `real/`에서 상시 모니터링용으로 재구현 — 알림(이메일/슬랙 등) 연동은 운영팀 결정 사항

---

## 4. 배포 (신설 디렉토리: `mapz/real/deploy/`)

### 4.1 최소 배포 구성

- **서버**: 클라우드 VM 또는 사내 서버 1대 (FastAPI + SQLite로 시작 — 트래픽 보고 PostgreSQL 전환 검토)
- **프로세스 관리**: `systemd` 또는 `docker compose`로 상시 구동, 재시작 정책 설정
- **도메인·HTTPS**: 도메인 연결(§1.1 상표·도메인 확인과 연동), Let's Encrypt 등으로 TLS
- **역방향 프록시**: nginx — 정적 파일 서빙, 요청 로깅, 기본 rate limit

### 4.2 배포 파이프라인

- `mapz/real/`에서 검증된 앱을 그대로 컨테이너화 (MVP `mapz/app/`은 참조하지 않음)
- `real/deploy/Dockerfile`, `real/deploy/docker-compose.yml` 신규 작성 (DB 볼륨 마운트, `.env` 시크릿 분리 — `real/.env`로 MVP `.env`와도 별도 관리)
- 배포 전 체크: `real/tests/`의 Phase 8 테스트(금지어 lint, 신선도 테스트, E2E) 재실행 → 통과해야 배포

### 4.3 스케일링 원칙

- 정적 데이터 조회 위주라 트래픽 증가에 상대적으로 강함(캐싱 우선 고려: 주제관·발견피드는 배치 갱신 주기와 맞춰 캐시)
- MVP의 Anti-KPI 원칙(체류시간 미측정) 유지 — 배포 후에도 트래픽 최적화가 헌장을 침해하지 않도록 주의(예: 알고리즘 최적화가 인기순 정렬로 회귀하지 않게)

---

## 5. 인증·보호

- **일반 사용자**: 로그인 없이 사용 가능(헌장상 진입장벽 최소화가 유지의 핵심). 계정이 필요한 기능(예: "우리 아이 탐험 지도" 저장)은 V2 이후 선택적 도입
- **요청 보호**: rate limiting(IP 기준), 봇 트래픽 방어(간단한 요청 패턴 감시로 시작, 필요시 강화)
- **관리자(제휴 콘솔, §6) 전용 인증**: 별도 관리자 계정 체계, 일반 사용자와 완전 분리. 코드 위치 `real/admin/`

---

## 6. 제휴 콘솔 (Tier 3, 신설 — `mapz/real/admin/`)

- 기관·지자체가 직접 체험 정보를 등록·갱신하는 관리자 화면 (MVP 범위 밖, 운영 단계 신규 개발)
- 최소 기능: 로그인, 체험 항목 CRUD, 상태(운영중/종료) 토글, 최종수정일 자동 갱신
- 장기 목표: Tier 1·2 의존도를 낮추고 정보 신선도 책임을 공급자에게 이전(기획서 원칙)

---

## 7. 법적·개인정보 요건 실구현

기획서 §10에 설계만 있던 항목을 실제 구현으로 전환한다. 관련 문서·코드는 `real/docs/legal/`에 모은다.

- **법정대리인 동의 플로우**: 계정 기능(§5) 도입 시점에 맞춰 구현. 그 전까지는 개인정보 비수집 원칙(익명 이용)으로 회피 가능
- **공공데이터 출처 표시**: 각 데이터 유형별 출처 고지를 화면 footer 또는 정보 카드에 명시(공공누리 조건 준수)
- **위치기반서비스사업 신고**: 지도 기능이 위치정보법상 신고 대상인지 실제 법무 검토 필요 — [ ] 사람 확인 필요 항목으로 유지
- **약관·개인정보처리방침**: 실 서비스 오픈 전 필수 문서, 법무 검토 필요 — [ ] 사람 확인 필요

---

## 8. 주제 확장 로드맵

| 단계 | 주제 수 | 근거 |
|---|---|---|
| MVP(`mapz/`, 완료) | 5개(고정) | 파이프라인 작동 검증용 |
| 운영 1차(`mapz/real/`) | Phase 0.5 자동 추출 상위 12개 | 실수요 반영 |
| 운영 2차 | 25~30개 | 커버리지 확대, 사각지대(먼 세계) 편성 강화 |
| 장기 | 지속 확장(자동) | Phase 0.5를 정기 배치화(예: 분기 1회 재추출)해 트렌드 반영 |

---

## 9. Claude Code 실행 지시 (운영 트랙 착수용)

> 이 섹션은 MVP 파이프라인 완주 후, **`mapz/real/` 폴더에서** 별도 세션으로 실행한다. **현재 `mapz/` 루트의 MVP 산출물에는 접근·수정하지 않는다.**

```bash
# MVP 완주 확인(mapz/reports/FINAL_REPORT.md 존재) 후
mkdir -p ~/projects/mapz/real
cp MAPZ_PRODUCTION.md ~/projects/mapz/real/
cd ~/projects/mapz/real

claude --dangerously-skip-permissions
> "현재 디렉토리(mapz/real/)를 작업 루트로 삼아 MAPZ_PRODUCTION.md를 읽고 진행하라.
   mapz/ 상위 루트에 있는 MVP 산출물(data/, db/, app/, scripts/, state/, reports/ 등)은
   절대 읽거나 수정하지 말 것 — 참조가 필요하면 기획서(MAPZ_기획방향_실행계획.md)와
   본 문서만 참고한다.
   먼저 §0의 폴더 구조대로 mapz/real/ 하위 디렉토리를 생성하고,
   §2 Phase 0.5(관심사 추출)를 실행해 실데이터 기반 주제 사전을 확정하라.
   이후 §3~§8의 항목을 우선순위(0.5 → 데이터 갱신 → 배포 → 인증 → 제휴콘솔 → 법적요건)로
   순차 진행하라. 법적 검토가 필요한 항목([ ] 표기)은 사람 확인 대기로 남기고 넘어가되,
   나머지는 무인으로 진행하라."
```

**권장**: git 저장소도 분리한다. `mapz/`(MVP)는 기존 커밋 이력을 그대로 두고, `mapz/real/`은 독립된 `git init`으로 새 이력을 시작하거나, 상위 저장소에 하위 디렉토리로 포함하되 `.gitignore`로 서로 침범하지 않게 관리한다.

---

## 10. 요약 — 무엇이 바뀌는가

한 줄로: **MVP(`mapz/`)는 "5개 주제로 파이프라인이 도는가"를 봤고, 운영버전(`mapz/real/`)은 "정보나루·공공데이터가 실제로 찾아낸 진짜 관심사로, 상시 갱신되며, 배포되어 실사용자가 쓸 수 있는가"를 만든다.** 두 트랙은 폴더로 완전히 분리되어 서로의 파일을 읽거나 덮어쓰지 않는다. 파이프라인 뼈대(Phase 0~9) 개념은 재사용하되 코드는 복사해서 새로 시작하고, Phase 0.5 신설이 가장 중요한 수정이며 나머지(배포·인증·법적요건)는 그 위에 순차적으로 얹는 구조다.
