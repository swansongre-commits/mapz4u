# MAPZ Streamlit 배포 가이드 (mapz4u.streamlit.app)

MAPS와 동일한 **Streamlit Community Cloud** 방식. FastAPI 버전(app/main.py)과 별개로,
같은 SQLite DB·실데이터를 읽는 Streamlit 프론트엔드(`streamlit_app.py`)를 배포한다.

## 결과 주소
- **https://mapz4u.streamlit.app** (앱 생성 시 subdomain을 `mapz4u`로 지정)

## 파일 구성
- 메인 파일: `real/streamlit_app.py`
- 의존성: `real/requirements.txt` (streamlit, folium, streamlit-folium)
- 테마: `real/.streamlit/config.toml`
- 데이터: `real/db/mapz_real.db`(커밋됨) + `real/data/clean/*.json`(커밋됨) → 클라우드에서 그대로 사용

## 배포 절차 (사용자)
1. GitHub에 저장소 push (아래 §사용자 체크리스트)
2. https://share.streamlit.io → **GitHub으로 로그인**
3. **New app** → 저장소 선택
   - Branch: `main` (또는 사용 브랜치)
   - **Main file path: `real/streamlit_app.py`**
   - **Advanced → App URL(subdomain): `mapz4u`** → https://mapz4u.streamlit.app
4. **Deploy** 클릭 → 2~4분 후 오픈
   - 시크릿(Secrets) 불필요 — 앱은 커밋된 DB만 읽음(외부 키 없음)

## 특징
- 무료·상시(Streamlit Cloud는 유휴 시 sleep, 접속 시 자동 wake)
- 기능: 검색·필터, 12주제 타일, 주제관(체험·도서·인물·직업 팝오버), 지도(folium 1,568곳), 발견 피드, 네이버 지도 링크 — 전부 동작
- 헌장 준수: 금지어 0, 인기순 없음, 연봉·전망 미노출, 신선도 필터

## 제휴 콘솔(§6)은 별도
`admin/admin_app.py`(FastAPI)는 Streamlit Cloud에 안 올라감 → 필요 시 Render 등 별도 배포.
