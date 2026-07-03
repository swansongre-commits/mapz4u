# 성능 스모크 (로컬 TestClient, 30회, p95)

| API | 평균ms | p95ms |
|---|---|---|
| /api/topics | 2.6 | 1.8 |
| /api/topics/dino | 2.8 | 3.1 |
| /api/search?q=쥬라기 | 4.1 | 4.6 |
| /api/map?topics=space | 3.8 | 4.2 |
| /api/discover | 2.0 | 2.2 |
| /healthz | 1.4 | 1.6 |

- 전체 최대 p95: **4.6ms** (목표 <500ms: True)