# -*- coding: utf-8 -*-
"""
Configuration livree par le code, et non laissee a l'operateur.

Pourquoi ce module existe
-------------------------
Quatre demandes du cahier des charges (D6, D7, D9, D11) ont d'abord ete
traitees comme du parametrage: la fonctionnalite existait dans SENAITE,
il suffisait de la configurer. C'etait vrai, et c'etait insuffisant.
Documenter une manipulation que personne au laboratoire ne sait faire
deplace le probleme, il ne le resout pas -- et une configuration posee
a la main se perd a la premiere reinstallation.

Ce module pose donc en code ce qui peut l'etre, de facon idempotente:
reinstaller le profil ne duplique rien, et une valeur deja choisie par
le laboratoire n'est jamais ecrasee.

Ce qu'il couvre
---------------
D11  le gabarit de publication par defaut
D9   les calculs de moyenne sur repetitions, et leur rattachement

Ce qu'il ne couvre PAS
----------------------
D7 (analyste par analyse) demande un compte utilisateur par contact du
laboratoire. Creer un compte exige un mot de passe; en inventer un
serait un trou de securite, et en poser un connu de tous en serait un
pire. Seule l'attribution du role est automatisable -- voir
`grant_analyst_role`, qui agit sur les comptes DEJA crees.
"""

import logging

from bika.lims import api
from senaite.trimeta.samplefields import PRODUCT_NAME

logger = logging.getLogger("senaite.trimeta.samplefields")


# ---------------------------------------------------------------------
# D11 -- le gabarit de publication par defaut
# ---------------------------------------------------------------------
#
# LA CAUSE DU SYMPTOME DECRIT DANS LE CAHIER DES CHARGES.
#
# senaite.impress livre `senaite.impress:MultiDefault.pt` comme gabarit
# par defaut (voir son controlpanel.py, champ `default_template`). Or
# un gabarit dont le nom commence ou finit par "Multi" recoit la
# TOTALITE des echantillons selectionnes: c'est ainsi qu'impress
# distingue un rapport groupe d'un rapport unitaire.
#
# Publier cinq echantillons avec ce gabarit produit donc cinq fichiers
# aux noms differents contenant chacun les cinq echantillons --
# exactement ce que decrit le document: "je selectionne 5 resultats et
# le logiciel va generer 5 fichiers avec des noms differents mais qui
# ont tous le meme contenu".
#
# Ce n'etait pas un defaut du logiciel, ni une fausse manipulation de
# l'operateur: c'etait le reglage d'usine. On le corrige ici plutot que
# de demander a chacun d'y penser a chaque publication.
IMPRESS_DEFAULT_TEMPLATE_RECORD = "senaite.impress.default_template"

# Notre gabarit COA, unitaire (son nom ne contient pas "Multi").
COA_TEMPLATE = u"senaite.trimeta.samplefields:COA-Trimeta.pt"

# Les gabarits multi-echantillons livres par senaite.impress. On ne
# remplace le reglage que s'il vaut l'un d'eux: si le laboratoire a
# deja choisi autre chose en connaissance de cause, on n'y touche pas.
MULTI_TEMPLATES = (
    u"senaite.impress:MultiDefault.pt",
    u"senaite.impress:MultiDefaultByColumn.pt",
)


def set_default_coa_template():
    """Fait du COA Trimeta le gabarit propose par defaut.

    Idempotent, et prudent: ne remplace qu'un gabarit "Multi" livre par
    senaite.impress. Un choix deliberement pose par le laboratoire est
    conserve.
    """
    try:
        current = api.get_registry_record(
            IMPRESS_DEFAULT_TEMPLATE_RECORD, default=None)
    except Exception:
        logger.warning(
            "Registre %r introuvable (senaite.impress absent?) -- "
            "gabarit par defaut inchange.",
            IMPRESS_DEFAULT_TEMPLATE_RECORD)
        return False

    if current == COA_TEMPLATE:
        logger.info("Gabarit par defaut deja regle sur %s", COA_TEMPLATE)
        return False

    if current not in MULTI_TEMPLATES:
        logger.info(
            "Gabarit par defaut laisse tel quel (%r): ce n'est pas un "
            "gabarit multi-echantillons livre par senaite.impress, donc "
            "c'est un choix du laboratoire.", current)
        return False

    from plone import api as ploneapi
    ploneapi.portal.set_registry_record(
        IMPRESS_DEFAULT_TEMPLATE_RECORD, COA_TEMPLATE)
    logger.info(
        "Gabarit par defaut: %r -> %s. Un gabarit 'Multi' recevait tous "
        "les echantillons selectionnes, d'ou des fichiers distincts au "
        "contenu identique (demande D11).", current, COA_TEMPLATE)
    return True


# ---------------------------------------------------------------------
# D9 -- repetitions et moyenne automatique
# ---------------------------------------------------------------------
#
# Le cahier des charges demande "de pouvoir faire deux ou plusieurs
# repetitions pour un meme echantillon et de calculer automatiquement
# la moyenne".
#
# SENAITE fait cela avec des CHAMPS INTERMEDIAIRES (interim fields):
# des cases de saisie supplementaires sur la ligne d'analyse, dont un
# CALCUL tire le resultat publie.
#
# Les formules fixes ci-dessous sont conservees pour les anciens profils.
# Le nouveau calcul delegue a repetitions.mean_repetitions et utilise
# toutes les cases de l'analyse, avec au moins deux mesures valides.
# Une case vide ou invalide renvoie NA, jamais une moyenne partielle.
REPETITION_KEYWORD = "R{}"

# (nombre de repetitions, titre du calcul)
CALCULATIONS = (
    (2, u"Moyenne de 2 repetitions"),
    (3, u"Moyenne de 3 repetitions"),
)

# Les deux anciens calculs restent disponibles pour l'historique.
# Les nouvelles affectations utilisent le calcul variable.
DEFAULT_REPETITIONS = "dynamic"

# Meme resolution des services actifs que le tableau de bord: mots-cles
# configures, puis intitules reconnus si ces mots-cles sont absents.
from senaite.trimeta.samplefields.dashboard.columns import get_keywords
from senaite.trimeta.samplefields.dashboard.columns import resolve_column_keywords


def build_interims(count):
    """Les champs de saisie d'un calcul de moyenne.

    `value` reste vide DELIBEREMENT. Y mettre 0 rendrait le champ
    pre-rempli, donc comptabilise: trois cases a 0 dont deux seulement
    sont corrigees donneraient une moyenne fausse, et personne ne le
    verrait. Vide, une repetition oubliee donne "NA".
    """
    interims = []
    for num in range(1, count + 1):
        interims.append({
            "keyword": REPETITION_KEYWORD.format(num),
            "title": u"Repetition {}".format(num),
            "value": "",
            "choices": "",
            "result_type": "",
            "allow_empty": False,
            "unit": "",
            "report": False,
            "hidden": False,
            "wide": False,
        })
    return interims


def build_formula(count):
    """Formule de la moyenne de `count` repetitions.

    Ecrite avec les marqueurs [Rn] attendus par SENAITE. Volontairement
    la plus simple possible: le moteur de formules n'accepte qu'un
    sous-ensemble de Python, et toute construction plus savante y est un
    pari. Voir le docstring du module pour ce qu'il advient d'un champ
    vide.
    """
    terms = " + ".join(
        "[{}]".format(REPETITION_KEYWORD.format(num))
        for num in range(1, count + 1))
    return "({}) / {}".format(terms, count)


# ---------------------------------------------------------------------
# Creation effective dans l'instance
# ---------------------------------------------------------------------
#
# SENAITE a deplace une partie de sa configuration d'Archetypes vers
# Dexterity au fil des versions 2.x: certains dossiers vivent sous
# `portal.setup`, d'autres sous `portal.bika_setup`. On resout
# l'emplacement au moment de l'execution plutot que de le coder en dur,
# comme le fait deja tests/utils.py.
SETUP_FOLDERS = {
    "calculations": ("setup/calculations", "bika_setup/bika_calculations"),
    "analysisservices": ("setup/analysisservices",
                         "bika_setup/bika_analysisservices"),
}


def get_setup_folder(portal, kind):
    """Dossier de configuration pour `kind`, ou None."""
    for path in SETUP_FOLDERS[kind]:
        obj = portal
        for part in path.split("/"):
            obj = getattr(obj, part, None)
            if obj is None:
                break
        if obj is not None:
            return obj
    logger.warning(
        "Dossier de configuration '%s' introuvable (essaye: %s). La "
        "structure de SENAITE a probablement change: mettre a jour "
        "SETUP_FOLDERS dans defaults.py.",
        kind, ", ".join(SETUP_FOLDERS[kind]))
    return None


def find_by_title(folder, title):
    """Premier objet du dossier portant ce titre, ou None.

    On retrouve un calcul par son TITRE et non par son identifiant:
    l'identifiant est genere par SENAITE et n'est pas previsible.
    """
    for obj in folder.objectValues():
        try:
            if api.get_title(obj) == title:
                return obj
        except Exception:
            continue
    return None


def setup_calculations(portal):
    """Cree les calculs de moyenne s'ils n'existent pas deja.

    :returns: {nombre de repetitions: objet Calculation}

    Idempotent. Un calcul deja present n'est ni recree ni modifie: le
    laboratoire a pu en ajuster la formule, et l'ecraser a chaque
    reinstallation serait une facon sournoise de perdre son travail.
    """
    folder = get_setup_folder(portal, "calculations")
    if folder is None:
        return {}

    created = {}
    for count, title in CALCULATIONS:
        existing = find_by_title(folder, title)
        if existing is not None:
            logger.info("Calcul '%s' deja present", title)
            created[count] = existing
            continue
        try:
            calc = api.create(folder, "Calculation", title=title)
            # L'ordre compte: setFormula() relit les mots-cles pour en
            # deduire les services dependants, et doit donc voir les
            # champs intermediaires deja poses.
            calc.setInterimFields(build_interims(count))
            calc.setFormula(build_formula(count))
            created[count] = calc
            logger.info("Calcul '%s' cree: %s", title, build_formula(count))
        except Exception:
            logger.exception("Creation du calcul '%s' impossible", title)
    created[DEFAULT_REPETITIONS] = setup_dynamic_calculation(portal)
    return created


def setup_dynamic_calculation(portal):
    """Un calcul partage; le nombre de cases appartient a chaque analyse."""
    from senaite.trimeta.samplefields import repetitions
    folder = get_setup_folder(portal, "calculations")
    if folder is None:
        return None
    for calculation in folder.objectValues():
        if repetitions.is_dynamic_calculation(calculation):
            return calculation
    calculation = api.create(folder, "Calculation", title=repetitions.TITLE)
    calculation.setInterimFields(build_interims(2))
    calculation.setPythonImports(repetitions.IMPORTS)
    calculation.setFormula(repetitions.FORMULA)
    calculation.trimeta_variable_repetitions = True
    return calculation


def get_repetition_keywords(portal):
    """Mots-cles reels des services actifs reconnus par le tableau de bord."""
    folder = get_setup_folder(portal, "analysisservices")
    if folder is None:
        return get_keywords()
    services = []
    for service in folder.objectValues():
        try:
            if api.is_active(service):
                services.append((service.getKeyword(), api.get_title(service)))
        except Exception:
            logger.exception("Service illisible pour les calculs de repetitions")
    resolved = resolve_column_keywords(services)
    return sorted(set(keyword for keywords in resolved.values()
                      for keyword in keywords))


def attach_calculation_to_service(service, calculation):
    """Pose le calcul uniquement sur un service actif sans calcul existant."""
    if calculation is None:
        return False
    try:
        if not api.is_active(service) or service.getCalculation() is not None:
            return False
        field = service.getField("Calculation")
        if field is None:
            return False
        field.set(service, calculation)
        service.setUseDefaultCalculation(False)
        service.reindexObject()
        logger.info("Service %s: calcul '%s' rattache",
                    service.getKeyword(), api.get_title(calculation))
        return True
    except Exception:
        logger.exception("Rattachement du calcul de repetitions impossible")
        return False


def attach_calculation_to_services(portal, calculation, keywords):
    """Rattache `calculation` aux services designes par `keywords`.

    Ne touche QUE les services qui n'ont pas deja un calcul: en imposer
    un a un service qui en porte deja un ecraserait un reglage
    deliberement pose, et pourrait fausser des resultats en silence.

    :returns: liste des mots-cles reellement rattaches
    """
    folder = get_setup_folder(portal, "analysisservices")
    if folder is None or calculation is None:
        return []

    wanted = set(k for k in (keywords or []) if k)
    attached = []
    for service in folder.objectValues():
        try:
            keyword = service.getKeyword()
        except Exception:
            continue
        if keyword not in wanted:
            continue
        if attach_calculation_to_service(service, calculation):
            attached.append(keyword)
    return attached


def setup_repetitions(portal):
    """D9 de bout en bout: cree les calculs et les rattache."""
    calculations = setup_calculations(portal)
    calculation = calculations.get(DEFAULT_REPETITIONS)
    if calculation is None:
        logger.warning(
            "Calcul de moyenne variable absent: aucun rattachement.")
        return []

    keywords = get_repetition_keywords(portal)
    attached = attach_calculation_to_services(portal, calculation, keywords)

    missing = sorted(set(keywords) - set(attached))
    if missing:
        # Un mot-cle qui ne correspond a aucun service ne leve rien.
        # C'est la meme incertitude que pour le tableau de bord, et elle
        # se leve au meme endroit.
        logger.info(
            "Aucun service rattache pour les mots-cles %s. Soit le "
            "service porte deja un calcul, soit le mot-cle ne "
            "correspond a rien: verifier la colonne Keyword dans "
            "Configuration > Analyses.", ", ".join(missing))
    return attached


def on_analysis_service_modified(service, event):
    """Configure un service cree ou modifie apres installation du profil."""
    try:
        portal = api.get_portal()
        installer = getattr(portal, "portal_quickinstaller", None)
        if installer is None or not installer.isProductInstalled(PRODUCT_NAME):
            return
        if not api.is_active(service) or service.getCalculation() is not None:
            return
        if service.getKeyword() not in get_repetition_keywords(portal):
            return
        calculations = setup_calculations(portal)
        attach_calculation_to_service(
            service, calculations.get(DEFAULT_REPETITIONS))
    except Exception:
        # L'enregistrement natif doit rester possible; le profil peut
        # rejouer le rattachement si un calcul n'a pas pu etre pose.
        logger.exception("Calcul de repetitions du service non configure")


# ---------------------------------------------------------------------
# D7 -- ce qui est automatisable de l'analyste par analyse
# ---------------------------------------------------------------------

ANALYST_ROLE = "Analyst"


def grant_analyst_role(portal):
    """Donne le role Analyst aux comptes lies aux contacts du laboratoire.

    Le champ "Analyste" d'une Work Sheet ne liste pas les contacts du
    laboratoire: il liste les UTILISATEURS portant le role Analyst. Un
    contact sans compte n'y apparait donc jamais -- d'ou l'impression
    que le champ est absent.

    Ce qui est automatisable s'arrete ici. CREER le compte demanderait
    un mot de passe: en inventer un empecherait la personne de se
    connecter, en poser un commun a tous serait un trou de securite. La
    creation des comptes reste donc une operation humaine, decrite dans
    docs/lot1-parametrage.md; cette fonction evite au moins d'avoir a
    penser au role.

    :returns: liste des identifiants ayant recu le role
    """
    from senaite.core.catalog import CONTACT_CATALOG

    granted = []
    try:
        contacts = api.get_tool(CONTACT_CATALOG)(portal_type="LabContact")
    except Exception:
        logger.exception("Contacts du laboratoire illisibles")
        return granted

    for brain in contacts:
        try:
            contact = api.get_object(brain, default=None)
            if contact is None:
                continue
            user = contact.getUser()
            if user is None:
                continue
            if ANALYST_ROLE in user.getRoles():
                continue
            portal.acl_users.userFolderEditUser(
                user.getId(), None,
                list(user.getRoles()) + [ANALYST_ROLE], [])
            granted.append(user.getId())
            logger.info("Role %s accorde a %s", ANALYST_ROLE, user.getId())
        except Exception:
            logger.exception("Attribution du role Analyst impossible")
    return granted


# ---------------------------------------------------------------------
# D6 -- historique des pannes et des entretiens
# ---------------------------------------------------------------------
#
# Ce que le cahier des charges montre vraiment
# --------------------------------------------
# La capture qui accompagne la demande est la fiche d'un equipement
# (AW Metre 1), et ce qu'elle donne a voir est sa BARRE D'ONGLETS:
#
#     Edit | View | QC Results | Calibrations |
#     Certificat d'etalonnage | Validations | Documents
#
# Il n'y a pas d'onglet "Maintenance". La demande "ajouter un champ
# pour Historique des pannes et Historique des entretiens dans le
# module Equipements" designe donc cet emplacement precis: il manque
# une entree dans cette barre.
#
# Pourquoi elle manque
# --------------------
# Pas parce que la fonctionnalite est absente. senaite.core v2.6.0
# embarque le type de contenu InstrumentMaintenanceTask, la vue
# InstrumentMaintenanceView, et son enregistrement:
#
#     <browser:page for="...IInstrument" name="maintenance"
#         class="...instrument.InstrumentMaintenanceView" ... />
#
# Tout fonctionne. Seul l'ONGLET est masque, dans le profil de
# senaite.core lui-meme (profiles/default/types/Instrument.xml):
#
#     <action action_id="calibrations" ... visible="True">
#     <action action_id="maintenance"  ... visible="False">
#     <action action_id="schedule"     ... visible="False">
#
# SENAITE livre donc cette fonction desactivee.
#
# Consequence sur notre documentation
# -----------------------------------
# docs/lot1-parametrage.md indiquait "Onglet Maintenance > Ajouter".
# Cet onglet n'existe pas dans l'interface du laboratoire: la
# manipulation etait litteralement impossible a suivre. C'est corrige
# ici, en rendant l'onglet visible, plutot que dans le mode d'emploi.
#
# On ne touche pas a "schedule": le cahier des charges ne demande pas
# de planification, et afficher un onglet dont personne n'a l'usage
# encombre la barre sans rien apporter.
INSTRUMENT_TYPE = "Instrument"
MAINTENANCE_ACTION = "maintenance"


def show_instrument_maintenance_tab():
    """Rend visible l'onglet Maintenance sur la fiche d'un equipement.

    Idempotent: si l'onglet est deja visible -- parce que le profil a
    deja tourne, ou parce que le laboratoire l'a active a la main --
    on ne fait rien.

    :returns: True si la visibilite a ete changee
    """
    try:
        portal_types = api.get_tool("portal_types")
        fti = getattr(portal_types, INSTRUMENT_TYPE, None)
    except Exception:
        logger.exception("portal_types illisible")
        return False

    if fti is None:
        logger.warning(
            "Type de contenu '%s' introuvable: onglet Maintenance "
            "inchange.", INSTRUMENT_TYPE)
        return False

    for action in fti.listActions():
        try:
            if action.getId() != MAINTENANCE_ACTION:
                continue
        except Exception:
            continue
        if getattr(action, "visible", False):
            logger.info("Onglet Maintenance deja visible")
            return False
        action.visible = True
        logger.info(
            "Onglet Maintenance rendu visible sur les equipements. "
            "senaite.core le livre masque (visible=False dans son "
            "Instrument.xml); la vue existait deja et fonctionnait, "
            "seule l'entree de barre manquait (demande D6).")
        return True

    logger.warning(
        "Aucune action '%s' sur le type %s: la structure de SENAITE a "
        "peut-etre change.", MAINTENANCE_ACTION, INSTRUMENT_TYPE)
    return False


def hide_instrument_maintenance_tab():
    """Remet l'onglet Maintenance dans l'etat ou senaite.core le livre.

    Appele a la desinstallation: l'add-on ne doit pas laisser derriere
    lui une interface qu'il est le seul a expliquer.
    """
    try:
        portal_types = api.get_tool("portal_types")
        fti = getattr(portal_types, INSTRUMENT_TYPE, None)
        if fti is None:
            return False
        for action in fti.listActions():
            if action.getId() == MAINTENANCE_ACTION:
                action.visible = False
                logger.info("Onglet Maintenance remasque")
                return True
    except Exception:
        logger.exception("Remasquage de l'onglet Maintenance impossible")
    return False
