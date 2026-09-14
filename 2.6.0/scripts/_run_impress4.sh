#!/bin/sh
BASE=/home/senaite/senaitelims/eggs/cp27mu/senaite.impress-2.6.0-py2.7.egg/senaite/impress
echo "=== configure.zcml (resourceDirectory registration) ==="
podman exec senaite grep -n "resourceDirectory\|senaite.impress.reports" -B2 -A5 "$BASE/configure.zcml"
echo "=== templates/reports dir listing ==="
podman exec senaite ls -la "$BASE/templates/reports/"
echo "=== vocabularies.py (Templates vocabulary, how 'name:content' is split/labeled) ==="
podman exec senaite cat "$BASE/vocabularies.py" 2>/dev/null | head -80
echo "=== publishview render / where template content gets the sample fields (search for ClientSampleID or getReceptionWeight or custom attrs) ==="
podman exec senaite grep -n "ClientSampleID\|getOrigin\|ReceptionWeight" "$BASE/analysisrequest/templates/"*.pt 2>/dev/null
