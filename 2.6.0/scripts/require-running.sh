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

# Le container existe mais ne tourne pas.
#
# On RASSEMBLE LES INDICES D'ABORD, on conclut ensuite. La version
# precedente annoncait "le port est deja occupe" avant meme d'avoir
# regarde, puis affichait deux sections vides quand ce n'etait pas le
# cas -- ce qui envoyait chercher du cote d'un port libre.
#
# Deux sections etaient vides pour une raison technique, pas par
# hasard: dans `ss ... | grep ... | sed ...`, le code de retour est
# celui de SED, qui reussit meme sans rien recevoir. Le `|| echo
# "(personne)"` ne se declenchait donc jamais. D'ou la capture dans une
# variable ci-dessous, puis un test sur son contenu.

# --- Indice 1: qui ecoute sur le port publie
PROBE=""
LISTENERS=""
if command -v ss >/dev/null 2>&1; then
    PROBE="ss"
    LISTENERS="$(ss -tlnp 2>/dev/null | grep -w ":$PORT")"
elif command -v netstat >/dev/null 2>&1; then
    PROBE="netstat"
    LISTENERS="$(netstat -tlnp 2>/dev/null | grep -w ":$PORT")"
fi

# --- Indice 2: processus rootlessport laisses par un arret brutal
ORPHANS="$(ps -eo pid,etime,cmd 2>/dev/null | grep -i '[r]ootlessport')"

# --- Conclusion, fondee sur ce qui precede
if [ -n "$LISTENERS" ] || [ -n "$ORPHANS" ]; then
    echo "Le port $PORT est deja occupe: c'est la cause la plus" >&2
    echo "frequente en rootless, et les indices ci-dessous la" >&2
    echo "confirment." >&2
elif [ "$STATE" = "created" ]; then
    # 'created' n'est pas 'exited': le container n'a jamais demarre.
    # `make logs` sera donc vide, et l'erreur reelle ne s'affiche qu'au
    # moment ou l'on tente le demarrage.
    echo "Etat 'created': il a ete cree mais n'a JAMAIS demarre." >&2
    echo "Ses logs sont donc vides -- inutile de les chercher la." >&2
    echo "" >&2
    echo "Pour voir l'erreur reelle, tenter le demarrage a la main :" >&2
    echo "  $ENGINE start $SERVICE" >&2
else
    echo "Rien n'occupe le port $PORT et aucun processus orphelin" >&2
    echo "ne traine: la cause est ailleurs. Regarde 'make logs'." >&2
fi

echo "" >&2
echo "Qui ecoute sur $PORT :" >&2
if [ -z "$PROBE" ]; then
    echo "  (ni ss ni netstat sur cette machine: non verifiable)" >&2
elif [ -z "$LISTENERS" ]; then
    echo "  (personne)" >&2
else
    echo "$LISTENERS" | sed 's/^/  /' >&2
fi

echo "" >&2
echo "Processus rootlessport orphelins :" >&2
if [ -z "$ORPHANS" ]; then
    echo "  (aucun)" >&2
else
    echo "$ORPHANS" | sed 's/^/  /' >&2
fi

echo "" >&2
echo "Pour aller plus loin :" >&2
echo "  make doctor   etat complet: containers, ports, volumes" >&2
echo "  make logs     pourquoi le container s'est arrete" >&2

if [ -n "$LISTENERS" ]; then
    echo "" >&2
    echo "ATTENTION: si un AUTRE container occupe $PORT, c'est peut-etre" >&2
    echo "lui que voient les utilisateurs. Regarde quel volume il monte" >&2
    echo "sur /data (make doctor) avant de le supprimer." >&2
fi
echo "" >&2
exit 1
