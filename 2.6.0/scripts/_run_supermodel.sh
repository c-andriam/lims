#!/bin/sh
podman exec senaite bash -c "find /home/senaite/senaitelims/eggs -iname 'supermodel*' -path '*senaite/app*' 2>/dev/null | grep -v '\.pyc\|\.pyo'"
F=$(podman exec senaite bash -c "find /home/senaite/senaitelims/eggs -iname 'supermodel.py' -path '*senaite/app*' 2>/dev/null | grep -v pyc | head -1")
echo "file: $F"
podman exec senaite cat "$F"
