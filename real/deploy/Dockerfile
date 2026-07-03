# MAPZ 운영버전 컨테이너 (real/ 트랙 전용)
FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성 최소화
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY deploy/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 앱·데이터·정적파일 복사 (MVP mapz/ 루트는 포함하지 않음)
COPY app/ /app/app/
COPY data/ /app/data/
COPY db/ /app/db/
COPY scripts/ /app/scripts/

ENV MAPZ_RATE_LIMIT=180
ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
