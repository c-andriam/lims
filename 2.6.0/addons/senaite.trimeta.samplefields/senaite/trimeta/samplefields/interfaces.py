# -*- coding: utf-8 -*-
"""
Couche de navigateur (browser layer) de l'add-on.

A quoi elle sert
----------------
Certaines demandes du cahier des charges portent sur le COMPORTEMENT
d'une vue de senaite.core, pas sur un ajout. C'est le cas du nommage
des fichiers COA (demande D10): la vue existe, il faut seulement qu'elle
fabrique un autre nom.

senaite.core enregistre ses vues avec
`layer="bika.lims.interfaces.IBikaLIMS"`. En declarant une couche qui en
DERIVE, puis en reenregistrant la meme vue dessus, le registre
d'adaptateurs de Zope choisit la notre: elle est plus specifique. Le
code amont n'est pas touche.

Pourquoi pas un monkey patch
----------------------------
Un patch s'applique au chargement du module et ne se retire jamais. La
couche, elle, est activee par `profiles/default/browserlayer.xml` et
retiree par `profiles/uninstall/browserlayer.xml`: desinstaller l'add-on
redonne exactement le comportement natif. Sur un systeme de laboratoire
ou les rapports sont des documents qualite, pouvoir revenir en arriere
proprement n'est pas un detail.

L'add-on garde un patch, un seul, et pour une raison qui lui est propre:
`patches/date_received_patch.py` doit intervenir avant que le workflow ne
soit sollicite, ce qu'une couche ne permet pas.
"""

from bika.lims.interfaces import IBikaLIMS
from zope.publisher.interfaces.browser import IBrowserRequest


class ITrimetaLayer(IBikaLIMS, IBrowserRequest):
    """Couche activee sur les sites ou l'add-on est installe.

    Derive de **IBikaLIMS** pour etre plus specifique que les
    `browser:page` de senaite.core, et pour ne s'appliquer que dans un
    site SENAITE.

    Derive aussi de **IBrowserRequest**, et ce n'est pas decoratif. Le
    telechargement groupe de COA n'est pas une `browser:page` mais un
    adaptateur nomme, dont senaite.core declare le second element du
    `for` comme `IBrowserRequest`. Or IBikaLIMS, contrairement a
    l'IDefaultBrowserLayer habituel de Plone, n'en derive PAS.

    Sans cet heritage, notre surcharge l'emporterait tout de meme, mais
    pour une raison fragile: une interface directement fournie a un
    objet (ce que fait plone.browserlayer sur la requete) precede dans
    l'ordre de resolution celles declarees par sa classe. Cela tient a
    un detail d'implementation du registre d'adaptateurs, pas a la
    hierarchie. En derivant d'IBrowserRequest, notre enregistrement est
    strictement plus specifique que celui de l'amont: le choix devient
    une consequence de la hierarchie, verifiable a la lecture.

    C'est d'ailleurs ce que fait IDefaultBrowserLayer, dont derivent
    les couches de la plupart des add-ons Plone.
    """
