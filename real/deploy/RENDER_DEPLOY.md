# MAPZ 운영버전 배포 가이드 (Render.com)

MAPS가 Streamlit Cloud(GitHub 연결형)로 배포된 것과 같은 패턴을, FastAPI에 맞는 Render.com으로 적용.

## 결과 주소
- 무료 서브도메인: **https://mapz4u.onrender.com** (서비스명을 `mapz4u`로 만들면 자동)
- 커스텀 도메인(선택): `mapz4u.com`/`mapz4u.kr` 구매 시 Render Custom Domain에 연결

## 동작 방식
- Render가 GitHub 저장소를 클론 → `render.yaml`(Blueprint) 인식
- **빌드**: `data/clean/*.json`(커밋됨)에서 `build_linkage.py` + `build_db.py`로 SQLite DB 재생성 → **외부 API 호출 0**
- **실행**: `uvicorn app.main:app` (헬스체크 `/healthz`)
- `rootDir: real` 이라 MVP(`mapz/`)는 배포에 미포함

## 환경변수 (Render 대시보드에서 입력)
| 키 | 값 | 필수 |
|---|---|---|
| MAPZ_ADMIN_PW | (강한 비밀번호) | 제휴콘솔 배포 시 |
| MAPZ_RATE_LIMIT | 180 | render.yaml에 기본값 |
| PYTHON_VERSION | 3.12.6 | render.yaml에 기본값 |

## 제휴 콘솔(§6)은 별도
`admin/admin_app.py`는 별도 서비스로 분리 배포(외부 미노출·관리자망 권장). MVP 배포에는 미포함.
