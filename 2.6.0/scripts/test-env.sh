#!/bin/sh
# Inventaire de ce qui est disponible dans le container pour executer
# les tests.
#
# L'image SENAITE de production n'embarque pas forcement de testrunner:
# un buildout d'exploitation ne construit que ce qui sert a servir le
# site. Avant d'ajouter une partie [test] a custom.cfg, il faut savoir
# ce qui existe deja et si le container peut telecharger une recette.
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

run() {
    "$ENGINE" exec "$SERVICE" sh -c "$1" 2>&1
}

section() {
    echo ""
    echo "=============================================================="
    echo " $1"
    echo "=============================================================="
}

# L'interpreteur peut s'appeler python ou python3 selon l'image.
#
# ATTENTION: run() capture aussi la sortie d'erreur. Sans
# validation, un message d'erreur se retrouverait injecte dans les
# commandes construites plus bas, ou ses parentheses seraient lues
# comme du code shell.  On exige donc un chemin absolu, rien
# d'autre.
#
# python3 est cherche EN PREMIER: certaines images embarquent
# encore un python2 qui repondrait a `command -v python` sans rien
# pouvoir importer du buildout.
PY="$(run "command -v python3 || command -v python" | tr -d '\r' | tr -d '\n')"
case "$PY" in
    /*python*) ;;
    *)
        echo "ERREUR: aucun interpreteur python utilisable dans" >&2
        echo "le container. Reponse obtenue: $PY" >&2
        exit 1
        ;;
esac

section "Interpreteur"
echo "Chemin  : $PY"
run "$PY --version"

section "Scripts disponibles dans $INSTANCE_DIR/bin"
run "ls -1 $INSTANCE_DIR/bin 2>/dev/null || echo '(repertoire absent)'"

section "zope.testrunner est-il installe ?"
run "cd $INSTANCE_DIR && $PY -c 'import zope.testrunner as t; print(\"OUI ->\", t.__file__)'" \
    || true

section "L'add-on est-il resolu comme distribution ?"
# Si egg-info manque ou que buildout n'a pas pris, la distribution n'est
# pas resolue et le ZCML de l'add-on n'est jamais charge.
run "cd $INSTANCE_DIR && $PY -c \"import pkg_resources as p; d=p.get_distribution('senaite.trimeta.samplefields'); print('OUI ->', d, d.location)\"" \
    || true

section "Structure du buildout (sections, parts, eggs)"
run "grep -n '^\[\|^parts\|^eggs\|^zcml\|^recipe' $INSTANCE_DIR/buildout.cfg 2>/dev/null | head -40 || echo '(buildout.cfg introuvable)'"

section "Le container peut-il installer une recette ?"
# zc.recipe.testrunner doit etre telechargeable pour construire
# bin/test. Sans reseau sortant, il faudra une autre approche.
run "$PY -m pip --version 2>/dev/null || echo 'pip absent'"
run "$PY -c \"import urllib.request as u; u.urlopen('https://pypi.org/simple/', timeout=5); print('reseau sortant vers PyPI: OUI')\"" \
    || echo "reseau sortant vers PyPI: NON (ou bloque)"

section "Eggs deja presents contenant 'testrunner'"
run "ls -1 $INSTANCE_DIR/eggs 2>/dev/null | grep -i testrunner || echo '(aucun)'"

echo ""
echo "Colle cette sortie: elle determine comment construire bin/test."
echo ""
echo "En attendant, 'make test-pure' fonctionne sans container et"
echo "couvre deja 54 tests de logique pure."
echo ""
