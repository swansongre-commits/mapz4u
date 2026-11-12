# MAPZ 운영버전 - 사내 개발서버(ringi-dev) 전용 이미지
# Render용 deploy/Dockerfile 과 다른 점: DB와 연계 인덱스를 이미지 빌드 중에 data/clean 에서 새로 만든다.
# 빌드 맥락(context)은 real/ 이다.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY deploy/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app/ /app/app/
COPY data/ /app/data/
COPY scripts/ /app/scripts/

# 외부 API 호출 없이 커밋된 정제 데이터만으로 연계·DB·신선도를 재생성한다
RUN mkdir -p /app/db /app/state /app/reports \
    && python scripts/build_linkage.py \
    && python scripts/build_db.py \
    && python scripts/freshness.py

ENV MAPZ_RATE_LIMIT=180
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
