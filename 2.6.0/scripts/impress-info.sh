#!/bin/sh
# Inventorie senaite.impress dans le container, pour construire le
# gabarit COA du lot 4.
#
# Un gabarit de rapport appelle des methodes de la vue fournie par
# senaite.impress. Ces methodes ne sont pas documentees: les deviner
# produirait un PDF en erreur. Ce script va les lire a la source.
#
# Deux pieges appris a la premiere version
# ----------------------------------------
# 1. On ne localise PAS le paquet par un import. `python` peut designer
#    un Python 2 dans l'image, et surtout un interpreteur lance a la
#    main n'a pas les eggs du buildout dans son sys.path. On cherche
#    donc les fichiers sur le disque.
# 2. On VALIDE le chemin trouve avant de s'en servir. La premiere
#    version capturait la sortie d'erreur dans une variable puis
#    l'injectait dans les commandes suivantes: le traceback, avec ses
#    parentheses, devenait du code shell.
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

# ---------------------------------------------------------------------
# Localisation, par le disque et non par un import
# ---------------------------------------------------------------------

section "Interpreteurs presents dans le container"
run "for p in python python2 python3; do \
       c=\$(command -v \$p 2>/dev/null); \
       if [ -n \"\$c\" ]; then echo \"  \$c -> \$(\$c --version 2>&1)\"; fi; \
     done"

section "Emplacement de senaite.impress sur le disque"
IMPRESS="$(run "find $INSTANCE_DIR -maxdepth 7 -type d -path '*/senaite/impress' 2>/dev/null | head -1" | tr -d '\r' | tr -d '\n')"

# Validation stricte avant toute reutilisation: un chemin absolu, se
# terminant par senaite/impress, sans espace ni caractere special.
case "$IMPRESS" in
    /*senaite/impress)
        echo "$IMPRESS"
        ;;
    *)
        echo "INTROUVABLE."
        echo ""
        echo "Recherche elargie sur tout le systeme de fichiers :"
        run "find / -maxdepth 9 -type d -path '*/senaite/impress' 2>/dev/null | head -5"
        echo ""
        echo "Contenu de $INSTANCE_DIR/eggs (30 premieres lignes) :"
        run "ls -1 $INSTANCE_DIR/eggs 2>/dev/null | head -30"
        echo ""
        echo "Si senaite.impress n'apparait nulle part, la publication"
        echo "des COA passe par un autre paquet: colle cette sortie."
        exit 1
        ;;
esac

# ---------------------------------------------------------------------
# Contenu
# ---------------------------------------------------------------------

section "Version du paquet"
run "ls -1d $INSTANCE_DIR/eggs/senaite.impress* 2>/dev/null | head -3 || echo '(egg non liste)'"

section "Gabarits de rapport livres"
# Ceux dont le nom commence ou finit par Multi recoivent TOUS les
# echantillons selectionnes: c'est l'explication de la demande D11.
run "ls -1 $IMPRESS/templates/reports/ 2>/dev/null | head -30"

section "Methodes offertes au gabarit par la vue"
run "grep -n 'class \|    def ' $IMPRESS/reportview.py 2>/dev/null | head -70"

section "Gabarit Default.pt: conventions d'appel a copier"
run "sed -n '1,110p' $IMPRESS/templates/reports/Default.pt 2>/dev/null"

section "Stockage des PDF: adaptateur a surcharger pour le nommage"
run "grep -n 'class \|def \|ARReport\|filename' $IMPRESS/storage.py 2>/dev/null | head -40"

section "Vue specifique aux echantillons (analysisrequest/)"
# Default.pt n'est qu'un assemblage: chaque section du COA est un
# template a part, rendu par une methode render_<section>. Pour changer
# le contenu du COA il suffit donc de surcharger LES SECTIONS voulues,
# pas le rapport entier.
run "ls -1 $IMPRESS/analysisrequest/ 2>/dev/null"

section "Templates de section du COA"
run "ls -1 $IMPRESS/analysisrequest/templates/ 2>/dev/null"

section "Methodes de la vue echantillon"
run "grep -n 'class \|    def ' $IMPRESS/analysisrequest/reportview.py 2>/dev/null | head -80"

section "Section INFO du COA (celle a modifier en priorite)"
# C'est elle qui porte les caracteristiques de l'echantillon: c'est la
# que doivent apparaitre poids, temperature, designation, lot, client.
run "cat $IMPRESS/analysisrequest/templates/info.pt 2>/dev/null | head -80"

section "Stockage: methode store() complete"
run "sed -n '30,130p' $IMPRESS/storage.py 2>/dev/null"

section "Nommage du PDF telecharge (publishview.py)"
run "sed -n '190,225p' $IMPRESS/publishview.py 2>/dev/null"

section "store_multireports_individually: piste pour la demande D11"
run "grep -rn 'store_multireports_individually\|store_individually' $IMPRESS/ 2>/dev/null | grep -v '.pyo' | head -10"

section "Interfaces publiques"
run "grep -n 'class I' $IMPRESS/interfaces.py 2>/dev/null | head -30"

section "Construction du nom de fichier telecharge"
run "grep -rn 'filename' $IMPRESS/ 2>/dev/null | grep -v '.pyc' | head -25"

echo ""
echo "Colle cette sortie: elle contient de quoi ecrire le gabarit COA"
echo "de Trimeta sans deviner une seule methode."
echo ""
