#!/bin/sh
# Restaure une sauvegarde dans le volume de donnees de SENAITE.
#
# Appele par `make restore FILE=... CONFIRM=yes`. Variables attendues:
#   ENGINE   podman ou docker
#   SERVICE  nom du container
#   FILE     chemin de l'archive
#   CONFIRM  doit valoir "yes"
#
# Trois garde-fous, parce qu'une restauration est irreversible:
#   1. CONFIRM=yes explicite;
#   2. refus si le container tourne encore -- ecraser une ZODB sous un
#      serveur actif la corrompt;
#   3. resolution du vrai nom du volume, comme dans backup.sh.

set -eu

ENGINE="${ENGINE:-}"
SERVICE="${SERVICE:-senaite}"
FILE="${FILE:-}"
CONFIRM="${CONFIRM:-}"

if [ -z "$ENGINE" ]; then
    echo "ERREUR: ni podman ni docker n'est installe." >&2
    exit 1
fi

if [ -z "$FILE" ]; then
    echo "ERREUR: precise l'archive a restaurer." >&2
    echo "  make restore FILE=backups/xxx.tar.gz CONFIRM=yes" >&2
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "ERREUR: '$FILE' introuvable." >&2
    exit 1
fi

if [ "$CONFIRM" != "yes" ]; then
    echo "Une restauration ECRASE toutes les donnees actuelles."
    echo "L'operation est irreversible."
    echo ""
    echo "Archive     : $FILE"
    echo "Contenu     :"
    tar tzf "$FILE" | head -10
    echo ""
    echo "Si c'est bien ce que tu veux, relance avec:"
    echo "  make restore FILE=$FILE CONFIRM=yes"
    exit 1
fi

RUNNING="$("$ENGINE" inspect -f '{{.State.Running}}' "$SERVICE" 2>/dev/null || echo unknown)"
if [ "$RUNNING" = "true" ]; then
    echo "ERREUR: le container '$SERVICE' tourne encore." >&2
    echo "Restaurer une ZODB sous un serveur actif la corrompt." >&2
    echo "Arrete-le d'abord: make down" >&2
    exit 1
fi

VOLUME="$("$ENGINE" inspect \
    -f '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' \
    "$SERVICE" 2>/dev/null || true)"

if [ -z "$VOLUME" ]; then
    echo "ERREUR: aucun volume monte sur /data pour '$SERVICE'." >&2
    echo "Si le container a ete supprime (make down), recree-le" >&2
    echo "avec 'make up' puis 'make down' avant de restaurer." >&2
    exit 1
fi

BASENAME="$(basename "$FILE")"
DIRNAME="$(cd "$(dirname "$FILE")" && pwd)"

echo "Volume cible : $VOLUME"
echo "Archive      : $FILE"
echo ""

"$ENGINE" run --rm \
    -v "$VOLUME":/data \
    -v "$DIRNAME":/backup:ro \
    alpine sh -c "rm -rf /data/..?* /data/.[!.]* /data/* 2>/dev/null; tar xzf /backup/$BASENAME -C /data"

echo "Restauration terminee. Redemarre avec: make up"
