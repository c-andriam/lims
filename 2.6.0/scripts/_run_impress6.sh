#!/bin/sh
BASE=/home/senaite/senaitelims/eggs/cp27mu/senaite.impress-2.6.0-py2.7.egg/senaite/impress
echo "=== analysisrequest/model.py ==="
podman exec senaite cat "$BASE/analysisrequest/model.py"
