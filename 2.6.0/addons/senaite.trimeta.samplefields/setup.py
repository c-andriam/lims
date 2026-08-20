# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

version = "1.1.0"

long_description = (
    "Add-on SENAITE pour Trimeta Group.\n\n"
    "Ajoute au type Sample les champs des sections Reception et "
    "Analyse, un magasin de suggestions partagees pour les champs "
    "libres, et les index de catalogue permettant de les afficher, "
    "trier et rechercher dans les listings."
)

setup(
    name="senaite.trimeta.samplefields",
    version=version,
    description="Champs personnalises Reception/Analyse pour SENAITE LIMS "
                "- Trimeta Group",
    long_description=long_description,
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Zope2",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    keywords="senaite lims trimeta samplefields",
    author="Trimeta Group / Juvence Andriamampionona (candriam)",
    url="https://github.com/candriam/senaite.trimeta.samplefields",
    license="GPL-2.0",
    packages=find_packages(exclude=["ez_setup"]),
    namespace_packages=["senaite", "senaite.trimeta"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "senaite.core",
        "archetypes.schemaextender",
        # Fournit les indexeurs nommes. Deja present dans tout site
        # Plone, mais declare ici car l'add-on ne peut pas s'en passer.
        "plone.indexer",
    ],
    extras_require={
        "test": [
            "Products.PloneTestCase",
            "plone.app.testing",
            "senaite.core[test]",
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
