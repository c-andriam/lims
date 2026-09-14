#!/bin/sh
DIR=$(podman exec senaite bash -c "ls -d /home/senaite/senaitelims/eggs/cp27mu/senaite.app.supermodel*-py2.7.egg/senaite/app/supermodel 2>/dev/null" | tr -d '\r')
echo "DIR=[$DIR]"
podman exec senaite ls "$DIR"
echo "=== model.py ==="
podman exec senaite cat "$DIR/model.py"
