#!/bin/sh
# Inventorie senaite.impress dans le container, pour construire le
# gabarit COA du lot 4.
#
# Un gabarit de rapport appelle des methodes de la vue fournie par
# senaite.impress. Ces methodes ne sont pas documentees: les deviner
# produirait un PDF en erreur. Ce script va les lire a la source.
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

PY="$(run 'command -v python || command -v python3' | tr -d '\r')"
if [ -z "$PY" ]; then
    echo "ERREUR: aucun interpreteur python dans le container." >&2
    exit 1
fi

IMPRESS="$(run "cd $INSTANCE_DIR && $PY -c \"import senaite.impress, os; print(os.path.dirname(senaite.impress.__file__))\"" | tr -d '\r')"

section "Emplacement de senaite.impress"
echo "$IMPRESS"

section "Gabarits de rapport livres"
# Ceux dont le nom commence ou finit par Multi recoivent TOUS les
# echantillons selectionnes: c'est l'explication de la demande D11.
run "ls -1 $IMPRESS/templates/reports/ 2>/dev/null || echo '(introuvable)'"

section "Methodes offertes au gabarit par la vue mono-rapport"
run "grep -n '    def [a-z]' $IMPRESS/reportview.py 2>/dev/null | head -60 || echo '(reportview.py introuvable)'"

section "Methodes de la vue multi-rapports"
run "grep -n 'class \|    def [a-z]' $IMPRESS/reportview.py 2>/dev/null | head -80"

section "Gabarit par defaut: comment il lit les donnees"
# Le meilleur modele pour ecrire le notre: on copie ses conventions
# d'appel plutot que de les inventer.
run "sed -n '1,120p' $IMPRESS/templates/reports/Default.pt 2>/dev/null || echo '(Default.pt introuvable)'"

section "Stockage des PDF: adaptateur a surcharger pour le nommage"
run "grep -n 'class \|def \|IPdfReportStorage\|filename\|ARReport' $IMPRESS/storage.py 2>/dev/null | head -40 || echo '(storage.py introuvable)'"

section "Interfaces publiques de senaite.impress"
run "grep -n 'class I' $IMPRESS/interfaces.py 2>/dev/null | head -30"

section "Comment le nom du fichier telecharge est construit"
run "grep -rn 'filename' $IMPRESS/*.py 2>/dev/null | head -30 || echo '(aucune occurrence)'"

echo ""
echo "Colle cette sortie: elle contient tout ce qu'il faut pour ecrire"
echo "le gabarit COA de Trimeta sans deviner une seule methode."
echo ""
