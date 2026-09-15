"""Audit des listes SENAITE : colonnes visibles entierement vides.

Voir docs/audit-listes.md. Pour chaque page, recupere tous les tableaux
qu'elle contient (data-api_url), demande toutes leurs lignes et signale
les colonnes visibles dont aucune ligne n'a de valeur. Une colonne vide
n'est un defaut que si la donnee existe : a verifier a la source.

    make audit-listes
    SENAITE_URL=http://192.168.8.100:8080/senaite make audit-listes
    python3 scripts/audit-listes.py /clients /samples

Variables : SENAITE_URL, SENAITE_USER, SENAITE_PASSWORD.
"""
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("SENAITE_URL", "http://localhost:8080/senaite").rstrip("/")
USER = os.environ.get("SENAITE_USER", "admin")
PASSWORD = os.environ.get("SENAITE_PASSWORD", "")
AUTH = "Basic " + base64.b64encode(
    "{}:{}".format(USER, PASSWORD).encode()).decode()

PAGES = sys.argv[1:] or [
    "/clients",
    "/samples",
    "/worksheets",
    "/trimeta-dashboard",
    "/bika_setup/bika_labcontacts",
    "/bika_setup/bika_analysisservices",
    "/bika_setup/bika_calculations",
    "/bika_setup/bika_instruments",
    "/setup/sampletypes",
    "/setup/analysiscategories",
    "/setup/departments",
    "/setup/samplecontainers",
    "/setup/samplematrices",
    "/methods",
    "/batches",
]


def http(url, body=None):
    req = urllib.request.Request(url, method="POST" if body is not None else "GET")
    req.add_header("Authorization", AUTH)
    if body is not None:
        req.add_header("Content-Type", "application/json")
        req.data = body
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, ""
    except urllib.error.URLError as error:
        return None, str(error.reason)


def text(value):
    if isinstance(value, dict):
        value = (value.get("formatted_value") or value.get("value")
                 or value.get("title") or "")
    if isinstance(value, list):
        value = " ".join(text(v) for v in value)
    value = str(value or "")
    if re.search(r"<(img|i|svg)\b", value):
        return "icone"
    return re.sub(r"<[^>]+>", "", value).strip()


def title(column, key):
    return re.sub(r"<[^>]+>", "", str(column.get("title") or "")).strip() or key


def main():
    if not PASSWORD:
        print("SENAITE_PASSWORD manquant")
        return 2
    seen = set()
    for page in PAGES:
        status, html = http(BASE + page)
        apis = sorted(set(re.findall(r'data-api_url="([^"]+)"', html)))
        if status != 200 or not apis:
            print("### %s : HTTP %s, %d tableau(x)" % (page, status, len(apis)))
            continue
        for api in apis:
            if api in seen:
                continue
            seen.add(api)
            # toutes les lignes, pas seulement la premiere page
            status, body = http(api + "/folderitems", b'{"pagesize": 100000}')
            try:
                data = json.loads(body)
            except ValueError:
                print("### %s : HTTP %s, reponse non JSON" % (api, status))
                continue
            columns = data.get("columns") or {}
            state = (data.get("review_states") or [{}])[0].get("columns") or list(columns)
            visible = [k for k in state
                       if k in columns and columns[k].get("toggle", True) is not False]
            items = data.get("folderitems") or []
            empty = [
                "%s [%s]" % (title(columns[key], key), key) for key in visible
                if not any(text(it.get(key)) or text((it.get("replace") or {}).get(key))
                           for it in items)
            ]
            print("### %s" % api.replace(BASE, ""))
            print("    %d ligne(s), %d colonne(s) visible(s)" % (len(items), len(visible)))
            if items:
                print("    vides : %s" % (", ".join(empty) or "aucune"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
