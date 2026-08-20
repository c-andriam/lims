#!/bin/sh
# Etat des lieux du deploiement SENAITE.
#
# Appele par `make doctor`. A lancer quand quelque chose ne demarre pas,
# avant de supprimer ou recreer quoi que ce soit: la question la plus
# importante est toujours "ou sont les donnees de production ?".
#
# Variables attendues:
#   ENGINE   podman ou docker
#   SERVICE  nom du container
#   PORT     port publie

set -u

ENGINE="${ENGINE:-}"
SERVICE="${SERVICE:-senaite}"
PORT="${PORT:-8080}"
ADDON_DIR="${ADDON_DIR:-addons}"

section() {
    echo ""
    echo "=============================================================="
    echo " $1"
    echo "=============================================================="
}

section "Moteur de conteneurs"
if [ -z "$ENGINE" ]; then
    echo "AUCUN moteur detecte (ni podman ni docker)."
else
    echo "Moteur : $ENGINE"
    "$ENGINE" --version 2>/dev/null || true
    echo "Mode   : $("$ENGINE" info --format '{{.Host.Security.Rootless}}' \
        2>/dev/null | sed 's/true/rootless/; s/false/root/')"
fi

section "Containers (tous, y compris arretes)"
if [ -n "$ENGINE" ]; then
    "$ENGINE" ps -a --format \
        'table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}' 2>/dev/null \
        || "$ENGINE" ps -a
fi

section "Qui ecoute sur le port $PORT"
# Sans droits root, le nom du processus peut manquer; la ligne
# d'ecoute, elle, reste visible et suffit a repondre a la question.
if command -v ss >/dev/null 2>&1; then
    ss -tlnp 2>/dev/null | grep -w ":$PORT" || echo "  (personne)"
elif command -v netstat >/dev/null 2>&1; then
    netstat -tlnp 2>/dev/null | grep -w ":$PORT" || echo "  (personne)"
else
    echo "  ni ss ni netstat disponible"
fi

echo ""
echo "Processus rootlessport (podman laisse parfois un orphelin qui"
echo "garde le port apres un arret brutal) :"
ps -eo pid,etime,cmd 2>/dev/null | grep -i '[r]ootlessport' \
    || echo "  (aucun)"

section "Volumes et donnees"
if [ -n "$ENGINE" ]; then
    echo "Volumes connus :"
    "$ENGINE" volume ls 2>/dev/null | sed 's/^/  /'
    echo ""
    echo "Volume monte sur /data, par container :"
    for name in $("$ENGINE" ps -a --format '{{.Names}}' 2>/dev/null); do
        vol="$("$ENGINE" inspect -f \
            '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{.Source}}{{end}}{{end}}' \
            "$name" 2>/dev/null)"
        [ -n "$vol" ] && echo "  $name  ->  $vol"
    done
    echo ""
    echo "C'EST LA QUESTION IMPORTANTE: le container qui detient le port"
    echo "$PORT est celui que voient les utilisateurs. Ne le supprime pas"
    echo "sans savoir quel volume il utilise."
fi

section "Droits sur $ADDON_DIR"
if [ -d "$ADDON_DIR" ]; then
    MY_UID="$(id -u)"
    echo "Compte courant : $(id -un) (uid=$MY_UID)"
    FOREIGN="$(find "$ADDON_DIR" ! -user "$MY_UID" 2>/dev/null | wc -l \
        | tr -d ' ')"
    if [ "$FOREIGN" -eq 0 ]; then
        echo "Tous les fichiers appartiennent au compte courant."
    else
        echo "$FOREIGN fichier(s) appartiennent a un autre utilisateur:"
        find "$ADDON_DIR" ! -user "$MY_UID" -printf '  uid=%U  %p\n' \
            2>/dev/null | head -5
        echo "  -> make fix-perms"
    fi
else
    echo "'$ADDON_DIR' introuvable (mauvais repertoire ?)"
fi

section "Add-on Trimeta"
PKG="$ADDON_DIR/senaite.trimeta.samplefields"
for path in \
    "$PKG/senaite/trimeta/samplefields/profiles/default/metadata.xml" \
    "$PKG/senaite/trimeta/samplefields/setuphandlers.py" \
    "$PKG/senaite/trimeta/samplefields/indexers.py" \
    "$PKG/senaite/trimeta/samplefields/qualitydata/extender.py" \
    "$PKG/senaite/trimeta/samplefields/listings/base.py"
do
    if [ -f "$path" ]; then
        echo "  OK      $(basename "$path")"
    else
        echo "  MANQUE  $path"
    fi
done

if [ -d "$PKG/senaite.trimeta.samplefields.egg-info" ]; then
    echo "  OK      egg-info (buildout a tourne)"
else
    echo "  MANQUE  egg-info -> lance 'make redeploy-addon',"
    echo "          sans lui l'add-on n'est pas resolu"
fi

echo ""
