#!/bin/sh
# Sauvegarde le volume de donnees de SENAITE.
#
# Appele par `make backup`. Variables attendues:
#   ENGINE   podman ou docker
#   SERVICE  nom du container
#
# Pourquoi ce script plutot qu'une recette Makefile
# -------------------------------------------------
# La logique tient en une vingtaine de lignes de shell avec des
# conditions et des variables. Ecrite dans un Makefile, chaque ligne
# doit se terminer par un antislash et chaque $ doit etre double: une
# erreur d'echappement y passe inapercue. Sur une commande qui touche
# aux donnees de production, ce risque ne vaut pas la peine.
#
# Le piege que ce script evite
# ----------------------------
# compose ne cree pas un volume nomme "senaite-data" mais
# "<projet>_senaite-data". Monter "senaite-data" en dur ne provoque
# aucune erreur: le moteur cree un volume vide et on archive... rien.
# On obtient une sauvegarde d'apparence normale, sans donnees.
# On resout donc le vrai nom depuis le container.

set -eu

ENGINE="${ENGINE:-}"
SERVICE="${SERVICE:-senaite}"
BACKUP_DIR="${BACKUP_DIR:-backups}"

# Une base SENAITE reellement utilisee pese plusieurs Mio. En dessous,
# c'est probablement une base vide ou un volume qui n'est pas le bon.
MIN_SIZE_BYTES=102400

if [ -z "$ENGINE" ]; then
    echo "ERREUR: ni podman ni docker n'est installe." >&2
    exit 1
fi

resolve_volume() {
    "$ENGINE" inspect \
        -f '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' \
        "$SERVICE" 2>/dev/null || true
}

VOLUME="$(resolve_volume)"
if [ -z "$VOLUME" ]; then
    echo "ERREUR: aucun volume monte sur /data pour le container '$SERVICE'." >&2
    echo "Le container doit exister. Lance-le avec: make up" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"
FILE="senaite-data-$(date +%Y%m%d-%H%M%S).tar.gz"

echo "Container     : $SERVICE"
echo "Volume source : $VOLUME"
echo "Archive       : $BACKUP_DIR/$FILE"
echo ""

"$ENGINE" run --rm \
    -v "$VOLUME":/data:ro \
    -v "$(pwd)/$BACKUP_DIR":/backup \
    alpine tar czf "/backup/$FILE" -C /data .

SIZE="$(wc -c < "$BACKUP_DIR/$FILE" | tr -d ' ')"
echo "Taille        : $((SIZE / 1024)) Kio"

if [ "$SIZE" -lt "$MIN_SIZE_BYTES" ]; then
    echo ""
    echo "ATTENTION: archive suspecte (moins de 100 Kio)."
    echo "Une base SENAITE utilisee pese plusieurs Mio."
    echo "Contenu de l'archive:"
    tar tzf "$BACKUP_DIR/$FILE" | head -20
    echo ""
    echo "Ne te fie pas a cette sauvegarde tant que tu n'as pas verifie"
    echo "qu'elle contient bien filestorage/ et blobstorage/."
    exit 1
fi

echo ""
echo "Sauvegarde terminee."
