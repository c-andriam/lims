from setuptools import setup, find_packages

version = "1.0.0"

setup(
    name="senaite.trimeta.samplefields",
    version=version,
    description="Champs personnalises Reception/Analyse pour SENAITE LIMS - Trimeta Group",
    long_description="Add-on ajoutant les champs obligatoires et facultatifs "
                      "requis dans les sections Reception et Analyse des "
                      "caracteristiques des echantillons.",
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
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
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
