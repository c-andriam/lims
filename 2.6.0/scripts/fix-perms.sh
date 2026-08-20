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
# un `git checkout` echoue avec une pluie de "Permission denied".
#
# Ce script diagnostique la situation puis repare, en essayant d'abord
# la methode qui ne demande pas les droits root.

set -eu

TARGET="${TARGET:-addons}"
ENGINE="${ENGINE:-}"

if [ ! -d "$TARGET" ]; then
    echo "ERREUR: '$TARGET' introuvable." >&2
    echo "Lance ce script depuis le repertoire 2.6.0/." >&2
    exit 1
fi

MY_UID="$(id -u)"
MY_GID="$(id -g)"

echo "Compte courant : $(id -un) (uid=$MY_UID gid=$MY_GID)"
echo ""
echo "Proprietaires actuels dans $TARGET :"
find "$TARGET" ! -user "$MY_UID" -printf '  uid=%U gid=%G  %p\n' 2>/dev/null \
    | head -10 || true

FOREIGN="$(find "$TARGET" ! -user "$MY_UID" 2>/dev/null | wc -l | tr -d ' ')"
if [ "$FOREIGN" -eq 0 ]; then
    echo "  (aucun -- rien a reparer)"
    exit 0
fi
echo ""
echo "$FOREIGN fichier(s) appartiennent a un autre utilisateur."
echo ""

# --- Methode 1: podman rootless.
# Les fichiers ecrits par le container appartiennent a des sous-uid que
# le compte possede deja, mais qui ne lui sont pas directement
# accessibles. `podman unshare` entre dans l'espace de noms
# d'utilisateurs et permet de les rendre sans aucun droit root.
if [ "$ENGINE" = "podman" ] || command -v podman >/dev/null 2>&1; then
    if podman unshare chown -R 0:0 "$TARGET" 2>/dev/null; then
        echo "Repare via 'podman unshare' (aucun droit root necessaire)."
        exit 0
    fi
    echo "'podman unshare' n'a pas suffi (container en mode root ?)."
    echo ""
fi

# --- Methode 2: chown classique, demande les droits root.
if command -v sudo >/dev/null 2>&1; then
    echo "Tentative avec sudo..."
    sudo chown -R "$MY_UID:$MY_GID" "$TARGET"
    echo "Repare via sudo."
    exit 0
fi

echo "ERREUR: impossible de reparer automatiquement." >&2
echo "Demande a un administrateur d'executer:" >&2
echo "  chown -R $MY_UID:$MY_GID $(pwd)/$TARGET" >&2
exit 1
