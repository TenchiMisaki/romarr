#!/bin/sh
# Start and stop ROMarr as a Docker Engine container on ADM.
#
# The APK ships no Python: it runs ghcr.io/blizzhacker/romarr at the version
# the package is. Settings live in /share/Docker/romarr, so removing the app
# never deletes them.
NAME=romarr
VERSION=$(sed -n 's/.*"version": *"\([^"]*\)".*/\1/p' "${APKG_PKG_DIR:-/usr/local/AppCentral/romarr}/CONTROL/config.json" | head -1)
IMAGE="ghcr.io/blizzhacker/romarr:${VERSION}"
ENV_FILE="${ROMARR_ENV_FILE:-/share/Docker/romarr/romarr.env}"
DOCKER="${DOCKER:-docker}"

# KEY=value lines only; nothing in the file is executed, and unknown keys
# are ignored.
read_env() {
    while IFS='=' read -r key value; do
        case "$key" in
            PUID) CFG_PUID=$value ;;
            PGID) CFG_PGID=$value ;;
            TZ) CFG_TZ=$value ;;
            ROMARR_CONFIG) CFG_ROMARR_CONFIG=$value ;;
            ROMARR_ROMS) CFG_ROMARR_ROMS=$value ;;
            ROMARR_DOWNLOADS) CFG_ROMARR_DOWNLOADS=$value ;;
            ROMARR_HOST_PORT) CFG_ROMARR_HOST_PORT=$value ;;
        esac
    done < "$ENV_FILE"
    CFG_PUID=${CFG_PUID:-1000} CFG_PGID=${CFG_PGID:-100} CFG_TZ=${CFG_TZ:-Etc/UTC}
    CFG_ROMARR_HOST_PORT=${CFG_ROMARR_HOST_PORT:-6868}
}

container_id() {
    entry=$("$DOCKER" container inspect -f '{{.Id}} {{index .Config.Labels "org.romarr.package"}}' "$NAME" 2>/dev/null) || return 0
    case "$entry" in
        *" asustor") printf '%s\n' "${entry% *}" ;;
        *) echo "ROMarr: container $NAME is not owned by this package" >&2; return 1 ;;
    esac
}

start() {
    existing=$(container_id) || return 1
    read_env
    # The shipped default library folder is created; anything else the
    # operator named must already exist, so a typo cannot file games into a
    # new empty folder.
    [ "$CFG_ROMARR_ROMS" = /share/Media/Games ] && mkdir -p "$CFG_ROMARR_ROMS"
    for dir in "$CFG_ROMARR_ROMS" "$CFG_ROMARR_DOWNLOADS"; do
        if [ ! -d "$dir" ]; then
            echo "ROMarr: $dir does not exist; create it or edit $ENV_FILE"
            exit 1
        fi
    done
    if ! mkdir -p "$CFG_ROMARR_CONFIG"; then
        echo "ROMarr: unable to create config directory: $CFG_ROMARR_CONFIG" >&2
        return 1
    fi

    # docker start never applies new mounts or environment, so the existing
    # container is reused only when the image and every setting match the
    # fingerprint it was created with. Anything edited gets a new container.
    spec=$(printf '%s|' "$IMAGE" "$CFG_PUID" "$CFG_PGID" "$CFG_TZ" "$CFG_ROMARR_CONFIG" \
        "$CFG_ROMARR_ROMS" "$CFG_ROMARR_DOWNLOADS" "$CFG_ROMARR_HOST_PORT" | cksum | cut -d' ' -f1)
    if [ -n "$existing" ] && [ "$("$DOCKER" inspect -f '{{index .Config.Labels "org.romarr.spec"}}' "$existing" 2>/dev/null)" = "$spec" ]; then
        "$DOCKER" start "$existing" >/dev/null && return 0
    fi
    # Have the image before touching the old container: a registry outage
    # then leaves the previous one in place.
    "$DOCKER" image inspect "$IMAGE" >/dev/null 2>&1 || "$DOCKER" pull "$IMAGE" >/dev/null || \
        { echo "ROMarr: could not pull $IMAGE"; exit 1; }
    if [ -n "$existing" ]; then
        "$DOCKER" rm -f "$existing" >/dev/null || return 1
    fi
    "$DOCKER" run -d --name "$NAME" --restart unless-stopped \
        --label "org.romarr.package=asustor" --label "org.romarr.spec=$spec" \
        -p "${CFG_ROMARR_HOST_PORT}:6868" \
        -e PUID="$CFG_PUID" -e PGID="$CFG_PGID" -e UMASK=002 \
        -e TZ="$CFG_TZ" -e LIBRARY_PATH=/roms \
        -v "${CFG_ROMARR_CONFIG}:/config" \
        -v "${CFG_ROMARR_ROMS}:/roms" \
        -v "${CFG_ROMARR_DOWNLOADS}:${CFG_ROMARR_DOWNLOADS}" \
        "$IMAGE" >/dev/null || { echo "ROMarr: could not start $IMAGE"; exit 1; }
    echo "ROMarr: started $IMAGE"
}

stop() {
    existing=$(container_id) || return 1
    [ -z "$existing" ] || "$DOCKER" stop -t 30 "$existing" >/dev/null
}

case "$1" in
    start)
        start || exit 1
        ;;
    stop)
        stop || exit 1
        ;;
    reload|restart)
        stop && start || exit 1
        ;;
    *)
        echo "usage: $0 {start|stop|reload}"
        exit 1
        ;;
esac
exit 0
