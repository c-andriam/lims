#!/bin/sh
BASE=/home/senaite/senaitelims/eggs/cp27mu/senaite.impress-2.6.0-py2.7.egg/senaite/impress
echo "=== template.py ==="
podman exec senaite cat "$BASE/template.py"
echo "=== interfaces.py (ITemplateFinder area) ==="
podman exec senaite grep -n "ITemplateFinder" -A 15 "$BASE/interfaces.py"
echo "=== templatefinder implementation ==="
podman exec senaite grep -rln "implements(ITemplateFinder)\|@implementer(ITemplateFinder)" "$BASE" 2>/dev/null
echo "=== controlpanel.py (settings, custom template folder?) ==="
podman exec senaite cat "$BASE/controlpanel.py" 2>/dev/null | head -100
