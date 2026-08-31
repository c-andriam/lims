#!/bin/sh
# Recompile l'add-on dans le container, puis rend les droits.
#
# Pourquoi un script et non deux lignes de Makefile
# -------------------------------------------------
# La reparation des droits doit avoir lieu MEME SI buildout echoue.
# C'est precisement quand il echoue qu'elle est le plus necessaire:
# la partie `precompiler` de buildout ecrit des .pyc dans addons/ --
# monte depuis l'hote -- sous l'identite de l'utilisateur du container,
# et ce, avant meme d'arriver aux parties qui plantent.
#
# Un `make` s'arrete a la premiere recette en echec: la reparation etait
# donc sautee exactement dans le cas ou elle servait. Symptome observe:
# un buildout tue par manque de memoire, suivi d'un `git pull` refuse
# pour "Permission denied" sur 130 fichiers.
#
# Note sur PYTHONDONTWRITEBYTECODE
# --------------------------------
# La variable posee dans compose.yml empeche Python d'ecrire des .pyc
# A L'IMPORT. Elle n'a aucun effet sur la partie `precompiler`, qui les
# genere explicitement. Les deux mecanismes sont complementaires, pas
# redondants: l'un supprime la cause permanente, l'autre nettoie apres
# chaque deploiement.
#
# Variables attendues:
#   ENGINE        podman ou docker
#   SERVICE       nom du container
#   INSTANCE_DIR  racine du buildout dans le container

set -u

ENGINE="${ENGINE:-}"
SERVICE="${SERVICE:-senaite}"
INSTANCE_DIR="${INSTANCE_DIR:-/home/senaite/senaitelims}"

if [ -z "$ENGINE" ]; then
    echo "ERREUR: ni podman ni docker n'est installe." >&2
    exit 1
fi

echo "Compilation de l'add-on dans le container..."
"$ENGINE" exec -i "$SERVICE" bash -c "cd $INSTANCE_DIR && buildout -c custom.cfg"
STATUS=$?

# --- Toujours, quel que soit le sort de buildout.
echo ""
ENGINE="$ENGINE" TARGET=addons QUIET=1 sh scripts/fix-perms.sh

if [ "$STATUS" -eq 0 ]; then
    exit 0
fi

echo "" >&2
echo "ERREUR: buildout s'est termine avec le code $STATUS." >&2
echo "Les droits sur addons/ ont tout de meme ete repares." >&2

if [ "$STATUS" -eq 137 ]; then
    echo "" >&2
    echo "137 = 128 + 9, le processus a ete TUE (SIGKILL)." >&2
    echo "Sur un buildout, c'est presque toujours le manque de" >&2
    echo "memoire, et la partie coupable est 'plonesite': elle" >&2
    echo "reconstruit le site Plone et n'a rien a voir avec" >&2
    echo "l'add-on." >&2
    echo "" >&2
    echo "Verifier :" >&2
    echo "  free -h" >&2
    echo "  $ENGINE inspect $SERVICE --format 'Limite: {{.HostConfig.Memory}}'" >&2
    echo "" >&2
    echo "Contournement -- ne jouer que la partie utile a l'add-on :" >&2
    echo "  make redeploy-instance" >&2
    echo "" >&2
    echo "Si la sortie affichait bien 'Updating instance.' avant" >&2
    echo "d'etre tuee, l'add-on est deja pris en compte: il ne" >&2
    echo "manque que 'make restart'." >&2
fi

exit "$STATUS"
