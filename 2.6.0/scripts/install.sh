#!/bin/sh
# Installation reproductible, sauvegarde avant activation du profil.
set -eu
: "${ENGINE:?Moteur requis}"
: "${COMPOSE:?Compose requis}"
SERVICE="${SERVICE:-senaite}"
INSTANCE_DIR="${INSTANCE_DIR:-/home/senaite/senaitelims}"
command -v curl >/dev/null
# Reutilise l'image locale; telecharge uniquement si absente.
if ! "$ENGINE" image inspect docker.io/senaite/senaite:v2.6.0 >/dev/null 2>&1; then
    $COMPOSE pull
fi
if "$ENGINE" container inspect "$SERVICE" >/dev/null 2>&1; then
    $COMPOSE stop "$SERVICE"
fi
# Cree le conteneur sans ouvrir la base, puis sauvegarde meme un volume
# deja present sur une machine dont le conteneur avait ete supprime.
$COMPOSE up --no-start
if "$ENGINE" run --rm --volumes-from "$SERVICE:ro" --entrypoint /bin/sh docker.io/senaite/senaite:v2.6.0 -c '[ -f /data/filestorage/Data.fs ] && [ "$(wc -c < /data/filestorage/Data.fs)" -gt 4 ]'; then
    ENGINE="$ENGINE" SERVICE="$SERVICE" sh scripts/backup.sh
fi
ENGINE="$ENGINE" TARGET=addons QUIET=1 sh scripts/fix-perms.sh
ENGINE="$ENGINE" TARGET=custom.cfg QUIET=1 sh scripts/fix-perms.sh
make test-pure
make i18n
# Le conteneur ponctuel utilise le meme volume; aucun serveur n'ecrit en parallele.
$COMPOSE run --rm --no-deps "$SERVICE" run /opt/trimeta-scripts/apply-profile.py
$COMPOSE up -d
ENGINE="$ENGINE" TARGET=addons QUIET=1 sh scripts/fix-perms.sh
ENGINE="$ENGINE" TARGET=custom.cfg QUIET=1 sh scripts/fix-perms.sh
sh scripts/wait-ready.sh
printf 'Installation et profil Trimeta termines.\n'
