#!/bin/sh
# Rend a l'utilisateur courant la propriete du repertoire de l'add-on.
#
# Pourquoi c'est necessaire
# -------------------------
# compose.yml monte addons/senaite.trimeta.samplefields dans le
# container. Quand buildout s'execute dedans, il y ecrit des fichiers
# (egg-info, __pycache__) sous l'identite de l'utilisateur du
# container, qui n'est pas celle du compte du serveur.
#
# Resultat: git ne peut plus ni modifier ni supprimer ces fichiers, et
# un `git pull` echoue avec "Permission denied".
#
# Ce script est appele automatiquement a la fin de `make redeploy-addon`
# (en mode QUIET), pour que le probleme ne se represente plus. Il reste
# lancable a la main via `make fix-perms`.
#
# Variables:
#   TARGET   repertoire a reparer (defaut: addons)
#   ENGINE   podman ou docker
#   QUIET    si "1", ne parle que s'il y a quelque chose a reparer

set -eu

TARGET="${TARGET:-addons}"
ENGINE="${ENGINE:-}"
QUIET="${QUIET:-}"

say() {
    [ "$QUIET" = "1" ] || echo "$@"
}

clean_bytecode() {
    # Le bytecode Python 2 est ecrit a cote des sources. Ces fichiers
    # sont regenerables et ne sont pas versionnes: les supprimer evite
    # qu'ils ne redeviennent un obstacle au prochain git pull.
    count="$(find "$TARGET" -name '*.pyc' 2>/dev/null | wc -l | tr -d ' ')"
    if [ "$count" -gt 0 ]; then
        find "$TARGET" -name '*.pyc' -delete 2>/dev/null || true
        echo "$count fichier(s) .pyc supprime(s)."
    fi
}

if [ ! -d "$TARGET" ]; then
    echo "ERREUR: '$TARGET' introuvable." >&2
    echo "Lance ce script depuis le repertoire 2.6.0/." >&2
    exit 1
fi

MY_UID="$(id -u)"
MY_GID="$(id -g)"

FOREIGN="$(find "$TARGET" ! -user "$MY_UID" 2>/dev/null | wc -l | tr -d ' ')"

if [ "$FOREIGN" -eq 0 ]; then
    say "Droits sur $TARGET: tout appartient a $(id -un), rien a faire."
    exit 0
fi

# A partir d'ici il y a quelque chose a reparer: on parle, meme en mode
# QUIET. Une reparation silencieuse cacherait un comportement qui merite
# d'etre visible.
echo "Droits: $FOREIGN fichier(s) de $TARGET appartiennent a un autre"
echo "utilisateur (buildout a tourne dans le container). Reparation..."

if [ "$QUIET" != "1" ]; then
    echo ""
    echo "Compte courant : $(id -un) (uid=$MY_UID gid=$MY_GID)"
    find "$TARGET" ! -user "$MY_UID" -printf '  uid=%U gid=%G  %p\n' \
        2>/dev/null | head -10 || true
    echo ""
fi

# --- Methode 1: podman rootless.
# Les fichiers ecrits par le container appartiennent a des sous-uid que
# le compte possede deja, mais qui ne lui sont pas directement
# accessibles. `podman unshare` entre dans l'espace de noms
# d'utilisateurs et permet de les rendre sans aucun droit root.
if [ "$ENGINE" = "podman" ] || command -v podman >/dev/null 2>&1; then
    if podman unshare chown -R 0:0 "$TARGET" 2>/dev/null; then
        echo "Repare via 'podman unshare' (aucun droit root necessaire)."
        clean_bytecode
        exit 0
    fi
    say "'podman unshare' n'a pas suffi (container en mode root ?)."
fi

# --- Methode 2: chown classique, demande les droits root.
if command -v sudo >/dev/null 2>&1; then
    say "Tentative avec sudo..."
    sudo chown -R "$MY_UID:$MY_GID" "$TARGET"
    echo "Repare via sudo."
    clean_bytecode
    exit 0
fi

echo "ERREUR: impossible de reparer automatiquement." >&2
echo "Demande a un administrateur d'executer:" >&2
echo "  chown -R $MY_UID:$MY_GID $(pwd)/$TARGET" >&2
exit 1
