#!/bin/sh
set -e
BASE=/home/senaite/senaitelims/eggs/cp27mu/senaite.impress-2.6.0-py2.7.egg/senaite/impress
echo "=== summary.pt ==="
podman exec senaite cat "$BASE/analysisrequest/templates/summary.pt"
echo "=== header.pt ==="
podman exec senaite cat "$BASE/analysisrequest/templates/header.pt"
echo "=== jbot / override mechanism search ==="
podman exec senaite bash -c "grep -rl z3c.jbot /home/senaite/senaitelims/eggs/cp27mu/*.egg 2>/dev/null | head -5"
podman exec senaite bash -c "find /home/senaite/senaitelims -iname 'overrides' -o -iname '*jbot*' 2>/dev/null | grep -v '\.pyc\|\.pyo' | head -20"
echo "=== how senaite.trimeta addon zcml is structured (existing browser layer) ==="
podman exec senaite cat /home/senaite/senaitelims/src/senaite.trimeta.samplefields/senaite/trimeta/samplefields/browser/__init__.py 2>/dev/null || true
