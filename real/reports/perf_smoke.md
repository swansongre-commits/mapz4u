# 운영 성능 스모크 (TestClient, 30회, p95)

| API | 평균ms | p95ms |
|---|---|---|
| /api/topics | 2.8 | 2.0 |
| /api/topics/art | 3.8 | 3.8 |
| /api/search?q=우주 | 15.7 | 16.5 |
| /api/map?topics=history | 23.9 | 24.4 |
| /api/discover | 2.3 | 2.7 |
| /healthz | 1.5 | 1.5 |

- 최대 p95: **24.4ms** (목표 <500ms: True) · 실데이터 1568체험 기준