#!/usr/bin/env bash
set -euo pipefail

image="${1:?Supply a locally built ROMarr image}"
source_file="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)/docker-compose.yml"
work="$(mktemp -d)"
project="romarr-smoke-$(basename -- "$work" | tr '[:upper:]' '[:lower:]' | tr . -)"
export ROMARR_ROMS="$work/library"
export ROMARR_DOWNLOADS="$work/downloads"
export ROMARR_SMOKE_IMAGE="$image"

compose() {
    if [[ -n "${ROMARR_COMPOSE_BIN:-}" ]]; then
        "$ROMARR_COMPOSE_BIN" --env-file /dev/null -p "$project" -f "$work/compose.yml" -f "$work/override.yml" "$@"
    else
        docker compose --env-file /dev/null -p "$project" -f "$work/compose.yml" -f "$work/override.yml" "$@"
    fi
}

# ShellCheck does not follow the EXIT trap into this handler.
# shellcheck disable=SC2317
cleanup() {
    local result=$?
    if (( result != 0 )); then
        compose logs --no-color || true
    fi
    compose down -v -t 2 || result=1
    rm -f -- "$work/compose.yml" "$work/override.yml" "$work/missing.log" "$work/library/fixture"
    if [[ -d "$work/library" ]]; then
        rmdir -- "$work/library" || result=1
    fi
    rmdir -- "$work/downloads" "$work" || result=1
    exit "$result"
}

cp -- "$source_file" "$work/compose.yml"
mkdir "$ROMARR_DOWNLOADS"
cat > "$work/override.yml" <<'YAML'
services:
  romarr:
    image: ${ROMARR_SMOKE_IMAGE:?supply a local image}
    container_name: !reset null
    ports: !reset []
    network_mode: none
    pull_policy: never
    restart: "no"
    volumes:
      - type: tmpfs
        target: /config
YAML
trap cleanup EXIT

compose config -q
if compose up -d --no-build --pull never > "$work/missing.log" 2>&1; then
    cat "$work/missing.log"
    printf 'ROMarr started with an absent library directory\n' >&2
    exit 1
fi
if ! grep -Fq "$ROMARR_ROMS" "$work/missing.log" ||
   ! grep -Eiq 'does not exist|no such file or directory' "$work/missing.log"; then
    cat "$work/missing.log"
    printf 'Startup failed for a reason other than the missing library directory\n' >&2
    exit 1
fi
test ! -e "$ROMARR_ROMS"
printf 'Missing library directory was rejected without creating it\n'

mkdir "$ROMARR_ROMS"
printf 'romarr-compose-smoke\n' > "$ROMARR_ROMS/fixture"
chmod 0755 "$ROMARR_ROMS"
chmod 0644 "$ROMARR_ROMS/fixture"
compose up -d --no-build --pull never

printf 'Health check: at most 12 attempts, 2 seconds apart, 2 consecutive passes required\n'
passes=0
for attempt in {1..12}; do
    printf 'Health attempt %s\n' "$attempt"
    if compose exec -T romarr python -c 'import json, pathlib, urllib.request; assert pathlib.Path("/roms/fixture").read_text().strip() == "romarr-compose-smoke"; assert json.load(urllib.request.urlopen("http://127.0.0.1:6868/api/health", timeout=2)) == {"ok": True}' 2>/dev/null; then
        passes=$((passes + 1))
        if (( passes == 2 )); then
            printf 'ROMarr started and read the existing library mount\n'
            exit 0
        fi
    else
        passes=0
    fi
    if (( attempt < 12 )); then
        sleep 2
    fi
done
printf 'ROMarr did not pass both health checks\n' >&2
exit 1
