#!/bin/sh
# Validation avant toute ecriture; stockage reel du container, nomme ou lie.
set -eu
: "${ENGINE:?Moteur requis}"
SERVICE="${SERVICE:-senaite}"
FILE="${FILE:-}"
CONFIRM="${CONFIRM:-}"
IMAGE="${IMAGE:-docker.io/senaite/senaite:v2.6.0}"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
[ -n "$FILE" ] && [ -f "$FILE" ] || { echo 'ERREUR: FILE requis et archive existante attendue' >&2; exit 1; }
FILE=$(realpath -- "$FILE")
"${PYTHON:-python3}" "$SCRIPT_DIR/validate-backup.py" "$FILE"
if [ -f "$FILE.sha256" ]; then
    (cd "$(dirname "$FILE")" && sha256sum -c "$(basename "$FILE").sha256")
fi
[ "$CONFIRM" = yes ] || { echo 'La restauration remplace les donnees. Utiliser CONFIRM=yes.' >&2; exit 1; }
RUNNING=$("$ENGINE" inspect -f '{{.State.Running}}' "$SERVICE")
[ "$RUNNING" = false ] || { echo 'ERREUR: arreter avec make stop (pas make down).' >&2; exit 1; }
SOURCE=$("$ENGINE" inspect -f '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}' "$SERVICE")
[ -n "$SOURCE" ] || { echo 'ERREUR: aucun stockage /data' >&2; exit 1; }
for other in $("$ENGINE" ps --format '{{.Names}}'); do
    mount=$("$ENGINE" inspect -f '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}' "$other")
    [ "$mount" != "$SOURCE" ] || { echo "ERREUR: $other utilise encore la base" >&2; exit 1; }
done
# Conserve une sauvegarde de secours de la cible avant remplacement.
ENGINE="$ENGINE" SERVICE="$SERVICE" sh "$SCRIPT_DIR/backup.sh"
echo "Restauration vers $SOURCE"
# Les arguments ne sont jamais interpoles dans le shell du container.
"$ENGINE" run --rm -i --volumes-from "$SERVICE" --entrypoint /bin/sh "$IMAGE" -eu -c '
    find /data -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
    tar xzf - -C /data
' < "$FILE"
echo 'Restauration terminee. Redemarrer avec make up.'
