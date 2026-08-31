#!/bin/sh
# Inventorie de quoi ecrire le tableau de bord du lot 5.
#
# Meme demarche que impress-info.sh, et pour la meme raison: une vue de
# listing appelle des methodes de senaite.app.listing qui ne sont pas
# documentees. Les deviner produit soit une colonne vide, soit un ZCML
# qui ne charge pas -- donc une instance qui ne demarre plus.
#
# Trois familles d'information sont ramenees:
#
#   1. l'API de ListingView: ce qu'une sous-classe peut declarer et
#      surcharger (colonnes, review_states, folderitem, filtres);
#   2. les index et colonnes de metadonnees REELLEMENT disponibles sur
#      le sample_catalog et l'analysis_catalog, lus dans les
#      declarations de senaite.core -- donc sans toucher a la ZODB de
#      production;
#   3. une vue de listing existante prise comme modele.
#
# Ce qui ne peut PAS venir d'ici: les mots-cles des services d'analyse
# (Vanilline, TH, AW...). Ce sont des donnees, pas du code. Le script
# rappelle l'URL ou les lire a la fin.
#
# Les deux pieges d'impress-info.sh s'appliquent tels quels:
#   - on localise les paquets par le DISQUE, pas par un import: un
#     interpreteur lance a la main n'a pas les eggs du buildout dans
#     son sys.path;
#   - on VALIDE chaque chemin avant de s'en servir, sinon un traceback
#     avec ses parentheses finit injecte comme du code shell.
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

# Localise un paquet par son chemin de module, et valide le resultat.
# Renvoie le chemin sur stdout, ou une chaine vide.
locate_package() {
    _path="$1"          # ex: senaite/app/listing
    _found="$(run "find $INSTANCE_DIR -maxdepth 8 -type d -path '*/$_path' 2>/dev/null | head -1" \
              | tr -d '\r' | tr -d '\n')"
    case "$_found" in
        /*"$_path") echo "$_found" ;;
        *)          echo "" ;;
    esac
}

# ---------------------------------------------------------------------
# Localisation
# ---------------------------------------------------------------------

section "Interpreteurs presents dans le container"
run "for p in python python2 python3; do \
       c=\$(command -v \$p 2>/dev/null); \
       if [ -n \"\$c\" ]; then echo \"  \$c -> \$(\$c --version 2>&1)\"; fi; \
     done"

LISTING="$(locate_package senaite/app/listing)"
CORE="$(locate_package senaite/core)"

section "Emplacement des paquets"
echo "senaite.app.listing : ${LISTING:-INTROUVABLE}"
echo "senaite.core        : ${CORE:-INTROUVABLE}"

if [ -z "$LISTING" ] || [ -z "$CORE" ]; then
    echo ""
    echo "Recherche elargie sur tout le systeme de fichiers :"
    run "find / -maxdepth 9 -type d -path '*/senaite/app/listing' 2>/dev/null | head -5"
    run "find / -maxdepth 9 -type d -path '*/senaite/core' 2>/dev/null | head -5"
    echo ""
    echo "Sans ces deux paquets le tableau de bord ne peut pas etre"
    echo "ecrit sans deviner. Colle cette sortie."
    exit 1
fi

section "Versions des eggs"
run "ls -1d $INSTANCE_DIR/eggs/senaite.app.listing* $INSTANCE_DIR/eggs/senaite.core* 2>/dev/null | head -5 \
     || echo '(eggs non listes: paquets probablement en src/)'"

# ---------------------------------------------------------------------
# 1. API de ListingView
# ---------------------------------------------------------------------

section "ListingView: attributs de classe declarables"
# Ce sont eux qu'une sous-classe redefinit: contentFilter, columns,
# review_states, pagesize, sort_on, show_search... La liste exacte
# change d'une version 2.x a l'autre.
run "sed -n '1,140p' $LISTING/view.py"

section "ListingView: methodes surchargeables"
run "grep -n '^class \|^    def \|^    [a-z_]* = ' $LISTING/view.py | head -120"

section "Interfaces publiques de senaite.app.listing"
run "grep -n 'class I\|    def \|    [a-z_]* = Attribute' $LISTING/interfaces.py 2>/dev/null | head -60"

section "Point d'entree des requetes AJAX (pagination, tri, recherche)"
# La vue rend une coquille HTML; tout le reste passe par cette vue
# JSON. Si un filtre personnalise doit survivre a un changement de page,
# c'est ici que ca se joue.
run "grep -n '^class \|^    def ' $LISTING/ajax.py 2>/dev/null | head -80"

section "Comment un contentFilter est construit et applique"
run "grep -rn 'contentFilter' $LISTING/*.py 2>/dev/null | head -40"

# ---------------------------------------------------------------------
# 2. Catalogues: index et colonnes reellement disponibles
# ---------------------------------------------------------------------

section "sample_catalog: declaration complete (index + metadonnees)"
# C'est la reference qui dit si getClientTitle, getSampleTypeTitle,
# getDateReceived, getDateVerified... sont des index, des colonnes de
# metadonnees, ou les deux.
run "cat $CORE/catalog/sample_catalog.py 2>/dev/null"

section "analysis_catalog: declaration complete"
# D'ou viendront les colonnes de resultats (Vanilline, TH, AW...).
# Verifier en particulier: getResult est-il une colonne de
# metadonnees ? Sinon chaque ligne reveille son analyse depuis la
# ZODB, et le tableau de bord devient inutilisable a plusieurs
# milliers d'echantillons.
run "cat $CORE/catalog/analysis_catalog.py 2>/dev/null"

section "Constantes de nommage des catalogues"
run "cat $CORE/catalog/__init__.py 2>/dev/null | head -60"

# ---------------------------------------------------------------------
# 3. Une vue de listing existante, prise comme modele
# ---------------------------------------------------------------------

section "Ou vivent les vues de listing des echantillons"
run "find $CORE -type f -name '*.py' -path '*samples*' 2>/dev/null | head -10"

section "SamplesView: colonnes, review_states, folderitem"
# Le modele a copier. On veut voir la forme exacte d'une definition de
# colonne et d'un review_state dans CETTE version.
SAMPLES_VIEW="$(run "find $CORE -type f -name 'view.py' -path '*samples*' 2>/dev/null | head -1" \
                | tr -d '\r' | tr -d '\n')"
case "$SAMPLES_VIEW" in
    /*.py) run "sed -n '1,200p' $SAMPLES_VIEW" ;;
    *)     echo "Vue introuvable a cet emplacement. Recherche large :"
           run "grep -rln 'class SamplesView' $CORE 2>/dev/null | head -5" ;;
esac

section "Declaration ZCML d'une vue de listing (browser:page)"
run "grep -rn -A 8 'SamplesView' $CORE/browser/configure.zcml 2>/dev/null | head -40"

section "Enregistrement d'une action de menu SENAITE"
# Pour ajouter l'entree 'Tableau de bord' a la barre de navigation.
run "find $CORE -name 'actions.xml' -o -name 'portal_actions*' 2>/dev/null | head -10"

# ---------------------------------------------------------------------
# Ce que le script ne peut pas savoir
# ---------------------------------------------------------------------

section "A RECUPERER A LA MAIN: les mots-cles des services d'analyse"
cat <<'EOF'
Les colonnes de resultats du tableau de bord (Vanilline,
Gluco-vanilline, AC Vanillique, PHB, AC PHB, TH, AW) sont retrouvees
par leur MOT-CLE (Keyword), pas par leur intitule: l'intitule peut
etre renomme, le mot-cle est la cle stable.

Ces mots-cles sont des donnees saisies dans l'instance, pas du code.
Ils ne peuvent donc pas etre lus ici.

Ouvrir :

    Configuration > Analyses  (Setup > Analysis Services)
    /senaite/bika_setup/bika_analysisservices

La colonne "Keyword" donne la valeur exacte de chacun. Coller la liste
des sept services concernes sous la forme :

    Vanilline          -> VANILLINE
    Gluco-vanilline    -> GLUCOVANILLINE
    ...

Si un service n'existe pas encore, le signaler: le tableau de bord
affichera simplement une colonne vide, sans erreur.
EOF

echo ""
echo "Colle cette sortie: elle contient de quoi ecrire le tableau de"
echo "bord sans deviner une seule methode."
echo ""
