# 인증·보호 (운영 §5)

## 1. 일반 사용자
- **로그인 없이 사용**(헌장상 진입장벽 최소화 = 유지의 핵심). 계정 필요 기능은 V2 이후 선택 도입.

## 2. 요청 보호 (구현됨)
- **앱 레벨 rate limiting**: `app/main.py`의 미들웨어 — IP 기준 슬라이딩 윈도우, 기본 `MAPZ_RATE_LIMIT=180` req/min. 초과 시 429 반환. `/static` 제외.
- **프록시 레벨 rate limiting**: `deploy/nginx.conf` — `limit_req_zone` 10r/s + burst 20 (IP 기준). 2중 방어.
- 봇 트래픽: 현재 요청빈도 감시로 시작. 필요 시 User-Agent·패턴 기반 강화(운영 결정).

## 3. 관리자 (제휴 콘솔, §6)
- **일반 사용자와 완전 분리**: 별도 앱(`admin/admin_app.py`), 별도 포트(예: 8090), 외부 미노출(nginx에서 관리자망/VPN만 허용 권장).
- **HTTP Basic 인증**: `MAPZ_ADMIN_USER` / `MAPZ_ADMIN_PW` 환경변수. `secrets.compare_digest`로 타이밍 공격 방어. 미인증/오인증 401.
- 운영 배포 시 반드시 강한 `MAPZ_ADMIN_PW` 설정 + HTTPS 뒤에 배치.

## 4. 시크릿 관리
- `real/.env`로 API 키·관리자 비밀번호 관리 (MVP `.env`와 별도). 컨테이너에는 환경변수로 주입, 이미지에 미포함(`.dockerignore`).

## 5. 검증
- 관리자 인증: 무인증/오인증 401, 정인증 200 — 테스트 확인(state/admin.log).
- 앱 rate limit: 미들웨어 동작 확인(정상요청 200 유지).
