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
echo "Ports libres parmi les candidats habituels :"
for candidate in 8080 8081 8082 8090 8180 9080; do
    if command -v ss >/dev/null 2>&1; then
        if ss -tln 2>/dev/null | grep -q ":$candidate "; then
            echo "  $candidate  occupe"
        else
            echo "  $candidate  LIBRE"
        fi
    fi
done
echo ""
echo "Pour en choisir un: ecrire SENAITE_PORT=<port> dans 2.6.0/.env"
echo "(voir .env.example), puis 'make down' et 'make up'."

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
            '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}  [{{.Source}}]{{end}}{{end}}' \
            "$name" 2>/dev/null)"
        [ -n "$vol" ] && echo "  $name  ->  $vol"
    done
    echo ""
    echo "C'EST LA QUESTION IMPORTANTE: le container qui detient le port"
    echo "$PORT est celui que voient les utilisateurs. Ne le supprime pas"
    echo "sans savoir quel volume il utilise."
fi

section "Reponse HTTP de SENAITE"
# curl ignore HSTS et le cache du navigateur. Si curl repond en clair
# alors que le navigateur bascule en https, le probleme est cote
# navigateur, pas cote serveur.
if command -v curl >/dev/null 2>&1; then
    URL="http://localhost:$PORT/senaite"
    echo "GET $URL"
    # On capture AVANT d'afficher, en deux temps.
    #
    # Le pipeline se terminait par `sed`, qui reussit meme sans rien
    # recevoir: le `|| echo "(pas de reponse)"` place en bout de
    # chaine ne se declenchait donc jamais, et une absence de reponse
    # s'affichait comme une section vide. C'est le meme piege qui, dans
    # require-running.sh, a fait chercher un port occupe alors qu'il
    # etait libre.
    RAW="$(curl -sS -o /dev/null -D - -m 5 "$URL" 2>&1)"
    HEADERS="$(echo "$RAW" | grep -i '^HTTP/\|^location:\|^strict-transport')"
    if [ -n "$HEADERS" ]; then
        echo "$HEADERS" | sed 's/^/  /'
    else
        echo "  (pas de reponse)"
        echo "$RAW" | sed 's/^/  /'
    fi
    echo ""
    echo "Si la reponse est 200 ou une redirection vers http://, le"
    echo "serveur va bien et la bascule vers https vient du navigateur."
    echo ""
    echo "Cause la plus probable ici: une redirection 301 mise en cache."
    echo "dsio-gateway publiait 8080->80; un nginx en frontal fait"
    echo "presque toujours 'return 301 https://...' sur le port clair."
    echo "Le navigateur a retenu cette redirection en PERMANENT et"
    echo "l'applique encore, alors que nginx n'ecoute plus."
    echo "Test decisif: ouvrir l'URL dans une fenetre privee (cache"
    echo "separe). Si ca marche, vider le cache du navigateur."
else
    echo "curl absent, verification impossible"
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
