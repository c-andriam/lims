#!/bin/sh
# Verifie que le container tourne, et explique quoi faire sinon.
#
# Utilise comme prerequis de redeploy-addon et test, et comme
# verification apres `make up`. Sans lui, podman renvoie
# "container state improper", qui ne dit ni pourquoi ni quoi faire.
#
# Variables attendues:
#   ENGINE   podman ou docker
#   SERVICE  nom du container
#   PORT     port publie

set -u

ENGINE="${ENGINE:-}"
SERVICE="${SERVICE:-senaite}"
PORT="${PORT:-8080}"

if [ -z "$ENGINE" ]; then
    echo "ERREUR: ni podman ni docker n'est installe." >&2
    exit 1
fi

STATE="$("$ENGINE" inspect -f '{{.State.Status}}' "$SERVICE" 2>/dev/null \
    || echo absent)"

if [ "$STATE" = "running" ]; then
    exit 0
fi

echo "" >&2
echo "ERREUR: le container '$SERVICE' ne tourne pas (etat: $STATE)." >&2
echo "" >&2

if [ "$STATE" = "absent" ]; then
    echo "Il n'existe pas encore. Cree-le avec:" >&2
    echo "  make up" >&2
    echo "" >&2
    exit 1
fi

# Le container existe mais refuse de demarrer. La cause de loin la plus
# frequente en rootless est un port deja occupe: soit par un autre
# container, soit par un processus rootlessport orphelin que podman a
# laisse derriere lui apres un arret brutal.
echo "Il existe mais ne demarre pas. Cause la plus frequente: le port" >&2
echo "$PORT est deja occupe." >&2
echo "" >&2
echo "Qui ecoute sur $PORT :" >&2
if command -v ss >/dev/null 2>&1; then
    ss -tlnp 2>/dev/null | grep -w ":$PORT" | sed 's/^/  /' >&2 \
        || echo "  (personne -- la cause est ailleurs, voir make logs)" >&2
elif command -v netstat >/dev/null 2>&1; then
    netstat -tlnp 2>/dev/null | grep -w ":$PORT" | sed 's/^/  /' >&2 \
        || echo "  (personne -- la cause est ailleurs, voir make logs)" >&2
fi

echo "" >&2
echo "Processus rootlessport orphelins :" >&2
ps -eo pid,etime,cmd 2>/dev/null | grep -i '[r]ootlessport' \
    | sed 's/^/  /' >&2 || echo "  (aucun)" >&2

echo "" >&2
echo "Pour aller plus loin :" >&2
echo "  make doctor   etat complet: containers, ports, volumes" >&2
echo "  make logs     pourquoi le container s'est arrete" >&2
echo "" >&2
echo "ATTENTION: si un AUTRE container occupe $PORT, c'est peut-etre" >&2
echo "lui que voient les utilisateurs. Regarde quel volume il monte" >&2
echo "sur /data (make doctor) avant de le supprimer." >&2
echo "" >&2
exit 1
