#!/bin/sh
# Leave settings on the share and remove only a package-owned container.
NAME=romarr
DOCKER="${DOCKER:-docker}"
container_id() {
    entry=$("$DOCKER" container inspect -f '{{.Id}} {{index .Config.Labels "org.romarr.package"}}' "$NAME" 2>/dev/null) || return 0
    case "$entry" in
        *" asustor") printf '%s\n' "${entry% *}" ;;
        *) echo "ROMarr: container $NAME is not owned by this package" >&2; return 1 ;;
    esac
}

existing=$(container_id) || exit 1
[ -z "$existing" ] || "$DOCKER" rm -f "$existing" >/dev/null
