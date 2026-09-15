#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compile les traductions de l'add-on (.po -> .mo), sans dependance.

    make i18n
    python3 scripts/compile-mo.py [repertoire des locales]

Zope ne lit que les .mo: apres toute modification d'un .po, recompiler,
puis redeployer l'add-on. Le test test_i18n.py echoue si un .mo livre ne
correspond plus a son .po.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE = os.path.join(HERE, os.pardir, "addons", "senaite.trimeta.samplefields",
                       "senaite", "trimeta", "samplefields")

spec = importlib.util.spec_from_file_location(
    "trimeta_i18n", os.path.join(PACKAGE, "i18n.py"))
i18n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i18n)

target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PACKAGE, "locales")
written = i18n.compile_directory(os.path.normpath(target))
for path in written:
    print("compile: %s" % os.path.relpath(path))
print("%d catalogue(s) recompile(s)" % len(written))
