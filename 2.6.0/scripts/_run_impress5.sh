#!/bin/sh
BASE=/home/senaite/senaitelims/eggs/cp27mu/senaite.impress-2.6.0-py2.7.egg/senaite/impress
podman exec senaite sed -n '150,170p' "$BASE/configure.zcml"
