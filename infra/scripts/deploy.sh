#!/usr/bin/env bash

if [ -z "${BASH_VERSION:-}" ]; then
  exec /usr/bin/env bash "$0" "$@"
fi

set -Eeuo pipefail

ACR_NAME="${1:?ACR name is required}"
APP_DIR="${2:-/opt/mohaeng-server}"
NEW_IMAGE_REF="${3:?Image reference is required}"
KAKAO_LOCAL_REST_API_KEY="${4:-}"
NAVER_LOCAL_CLIENT_ID="${5:-}"
NAVER_LOCAL_CLIENT_SECRET="${6:-}"
HEALTH_URL="http://127.0.0.1:8000/api/health"
IMAGE_TAG="${NEW_IMAGE_REF##*:}"

if [[ ! "$IMAGE_TAG" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Invalid Git commit SHA: $IMAGE_TAG" >&2
  exit 1
fi

exec 9>/var/lock/mohaeng-deploy.lock

if ! flock -n 9; then
  echo "Another deployment is already running." >&2
  exit 1
fi

CURRENT_CONTAINER_ID=""
PREVIOUS_IMAGE_ID=""
IMAGE_REF=""

on_error() {
  echo "DEPLOYMENT_FAILED" >&2
}

trap on_error ERR

cd "$APP_DIR"

if [ -z "$KAKAO_LOCAL_REST_API_KEY" ]; then
  echo "KAKAO_LOCAL_REST_API_KEY is required." >&2
  exit 1
fi

ENV_FILE="$APP_DIR/.env"
touch "$ENV_FILE"

if grep -q '^KAKAO_LOCAL_REST_API_KEY=' "$ENV_FILE"; then
  sed -i "s|^KAKAO_LOCAL_REST_API_KEY=.*|KAKAO_LOCAL_REST_API_KEY=$KAKAO_LOCAL_REST_API_KEY|" "$ENV_FILE"
else
  printf '\nKAKAO_LOCAL_REST_API_KEY=%s\n' "$KAKAO_LOCAL_REST_API_KEY" >> "$ENV_FILE"
fi

# 현재 컨테이너와 이미지 정보를 rollback 용도로 저장
CURRENT_CONTAINER_ID="$(docker compose ps -q fastapi 2>/dev/null || true)"

if [ -n "$CURRENT_CONTAINER_ID" ]; then
  PREVIOUS_IMAGE_ID="$(
    docker inspect --format='{{.Image}}' "$CURRENT_CONTAINER_ID"
  )"
  IMAGE_REF="$(
    docker inspect --format='{{.Config.Image}}' "$CURRENT_CONTAINER_ID"
  )"
fi

rollback() {
  if [ -z "$PREVIOUS_IMAGE_ID" ] || [ -z "$IMAGE_REF" ]; then
    echo "No previous image available for rollback." >&2
    return 1
  fi

  echo "Rolling back to previous image..."

  if ! docker tag "$PREVIOUS_IMAGE_ID" "$IMAGE_REF"; then
    echo "Failed to restore previous image tag." >&2
    return 1
  fi

  export DEPLOY_IMAGE="$IMAGE_REF"

  if ! docker compose up -d --no-deps --force-recreate fastapi; then
    echo "Failed to recreate the previous container." >&2
    return 1
  fi

  for ((attempt = 1; attempt <= 12; attempt++)); do
    if curl --fail --silent --show-error --connect-timeout 2 --max-time 4 "$HEALTH_URL" >/dev/null; then
      echo "ROLLBACK_SUCCEEDED"
      return 0
    fi

    sleep 5
  done

  echo "ROLLBACK_FAILED" >&2
  return 1
}

# VM Managed Identity로 ACR 인증
az login --identity --output none
az acr login --name "$ACR_NAME" --only-show-errors

export DEPLOY_IMAGE="$NEW_IMAGE_REF"

# 새 sha 이미지 다운로드
docker compose pull fastapi

# 새 이미지로 DB migration 실행
docker compose run --rm --no-deps fastapi alembic upgrade head

# 새 이미지로 컨테이너 교체
if ! docker compose up -d --no-deps --force-recreate fastapi; then
  echo "Container replacement failed." >&2
  rollback || true
  echo "DEPLOYMENT_FAILED" >&2
  exit 1
fi

# 최대 60초 동안 Health check
for ((attempt = 1; attempt <= 12; attempt++)); do
  if curl --fail --silent --show-error --connect-timeout 2 --max-time 4 "$HEALTH_URL" >/dev/null; then
    echo "DEPLOYMENT_SUCCEEDED"
    exit 0
  fi

  sleep 5
done

echo "Health check failed." >&2
docker compose logs --tail=100 fastapi || true

if ! rollback; then
  echo "Manual recovery is required." >&2
fi

echo "DEPLOYMENT_FAILED" >&2
exit 1