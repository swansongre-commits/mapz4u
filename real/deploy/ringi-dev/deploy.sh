#!/usr/bin/env bash
# MAPZ 운영버전을 사내 개발서버에 올린다. http://ringi-dev.o-r.kr:33105/
# 접속 정보는 D:\project\00.global\사내-개발서버.md, 비밀번호는 허브 .env 의 RINGI_DEV_SSH_PASSWORD
# (SSH_ASKPASS로만 넘기고 명령줄·로그에 남기지 않는다).
# 사용법: Git Bash 에서  sh real/deploy/ringi-dev/deploy.sh
set -euo pipefail

REAL=$(cd "$(dirname "$0")/../.." && pwd)        # .../MAPZ/real
ASKPASS=${RINGI_DEV_ASKPASS:-/d/project/00.global/04.scripts/ringi-dev/askpass.sh}
test -s "$ASKPASS" || { echo "askpass 스크립트를 찾을 수 없습니다: $ASKPASS"; exit 1; }
HOST=ringi_dev@220.88.137.240
PORT=33322
REMOTE=mapz

for f in data/clean/experiences.json data/clean/books.json data/clean/people.json \
         data/clean/jobs.json data/topics/topics_v1.json app/main.py; do
  test -s "$REAL/$f" || { echo "필요한 파일이 없습니다: real/$f"; exit 1; }
done

PKG=$(mktemp -d)/mapz-app.tgz
tar -czf "$PKG" -C "$REAL" app data/clean data/topics scripts deploy
echo "묶음 크기: $(du -h "$PKG" | cut -f1)"

export SSH_ASKPASS="$ASKPASS" SSH_ASKPASS_REQUIRE=force DISPLAY=:0
SSHOPT=(-o StrictHostKeyChecking=accept-new -o NumberOfPasswordPrompts=1 \
        -o PreferredAuthentications=password,keyboard-interactive)

ssh -p $PORT "${SSHOPT[@]}" $HOST "mkdir -p ~/$REMOTE"
scp -q -P $PORT "${SSHOPT[@]}" "$PKG" "$REAL/deploy/ringi-dev/docker-compose.yml" "$HOST:$REMOTE/"
ssh -p $PORT "${SSHOPT[@]}" $HOST "cd ~/$REMOTE \
  && rm -rf app && mkdir app && tar -xzf mapz-app.tgz -C app && rm mapz-app.tgz \
  && docker compose up -d --build 2>&1 | tail -3 \
  && sleep 5 \
  && curl -s -o /dev/null -w 'healthz %{http_code}\n' http://localhost:33105/healthz"
rm -f "$PKG"
echo "배포 끝: http://ringi-dev.o-r.kr:33105/"
