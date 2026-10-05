#!/bin/sh
# Attente bornee: un container running ne prouve pas que Zope est pret.
set -eu
URL="${SITE_URL:-http://localhost:${PORT:-8080}/senaite}"
TIMEOUT="${READY_TIMEOUT:-600}"
START=$(date +%s)
while :; do
    CODE=$(curl --max-time 5 -s -o /dev/null -w '%{http_code}' "$URL" || true)
    case "$CODE" in
        200|301|302|401) echo "SENAITE repond sur $URL (HTTP $CODE)"; exit 0 ;;
    esac
    if [ $(($(date +%s) - START)) -ge "$TIMEOUT" ]; then
        echo "ERREUR: SENAITE ne repond pas apres ${TIMEOUT}s. Voir make logs." >&2
        exit 1
    fi
    sleep 5
done
