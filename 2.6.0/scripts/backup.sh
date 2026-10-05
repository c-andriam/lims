#!/bin/sh
# Archive tout /data: tous les objets ZODB et les fichiers joints (blobs).
set -eu
: "${ENGINE:?Moteur requis}"
SERVICE="${SERVICE:-senaite}"
BACKUP_DIR="${BACKUP_DIR:-backups}"
IMAGE="${IMAGE:-docker.io/senaite/senaite:v2.6.0}"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON="${PYTHON:-python3}"

SOURCE=$("$ENGINE" inspect -f '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}' "$SERVICE")
[ -n "$SOURCE" ] || { echo 'ERREUR: aucun stockage /data' >&2; exit 1; }
# Refuse une sauvegarde si un autre serveur partage cette base.
for other in $("$ENGINE" ps --format '{{.Names}}'); do
    [ "$other" = "$SERVICE" ] && continue
    mount=$("$ENGINE" inspect -f '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}' "$other")
    if [ "$mount" = "$SOURCE" ]; then
        echo "ERREUR: $other utilise aussi la base. Arreter les autres serveurs." >&2
        exit 1
    fi
done
WAS_RUNNING=$("$ENGINE" inspect -f '{{.State.Running}}' "$SERVICE")
PARTIAL=""
cleanup() {
    status=$?
    trap - EXIT HUP INT TERM
    if [ "$WAS_RUNNING" = true ]; then
        "$ENGINE" start "$SERVICE" >/dev/null || status=1
    fi
    if [ "$status" -ne 0 ]; then
        echo "ERREUR: sauvegarde non validee. Fichier provisoire: $PARTIAL" >&2
    fi
    exit "$status"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM
if [ "$WAS_RUNNING" = true ]; then
    echo 'Arret temporaire de SENAITE pour une sauvegarde coherente...'
    "$ENGINE" stop --time 60 "$SERVICE" >/dev/null
fi
mkdir -p "$BACKUP_DIR"
BACKUP_DIR=$(CDPATH= cd -- "$BACKUP_DIR" && pwd)
FILE="senaite-data-$(date +%Y%m%d-%H%M%S)-$$.tar.gz"
PARTIAL="$BACKUP_DIR/$FILE.partial"
echo "Stockage sauvegarde: $SOURCE"
# La redirection est cote hote: pas de droits/labels requis sur /backup.
"$ENGINE" run --rm --volumes-from "$SERVICE:ro" --entrypoint /bin/tar "$IMAGE" czf - -C /data . > "$PARTIAL"
"$PYTHON" "$SCRIPT_DIR/validate-backup.py" "$PARTIAL"
mv "$PARTIAL" "$BACKUP_DIR/$FILE"
(cd "$BACKUP_DIR" && sha256sum "$FILE" > "$FILE.sha256")
echo "Sauvegarde complete: $BACKUP_DIR/$FILE"
