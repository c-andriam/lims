"""Compare les listes de l'instance, sans creer ni modifier de contenu.

Python 3, bibliotheque standard uniquement. Authentification par
SENAITE_USER et SENAITE_PASSWORD; adresse par SENAITE_URL ou --url.
Les POST visent exclusivement les endpoints de consultation folderitems.
Ce controle ne remplace pas une recette de creation avec des donnees metier.
"""

import argparse
import base64
import datetime
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get(
        "SENAITE_URL", "http://localhost:8080/senaite"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sample-code", help="Code reel recherche, facultatif")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    password = os.environ.get("SENAITE_PASSWORD")
    if not password:
        parser.error("SENAITE_PASSWORD doit etre defini")
    if not 1 <= args.limit <= 10000:
        parser.error("--limit doit etre compris entre 1 et 10000")
    base = args.url.rstrip("/")
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        parser.error("Adresse HTTP(S) attendue")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        parser.error("Adresse sans identifiants, parametres ni fragment attendue")
    auth = base64.b64encode((os.environ.get("SENAITE_USER", "admin") +
                            ":" + password).encode("utf-8")).decode("ascii")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            # Ne jamais transmettre les identifiants a une autre adresse.
            return None

    opener = urllib.request.build_opener(NoRedirect())

    def read_listing(path, **params):
        payload = dict(pagesize=args.limit, **params)
        request = urllib.request.Request(
            base + path, data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": "Basic " + auth,
                     "Content-Type": "application/json"})
        with opener.open(request, timeout=60) as response:
            data = json.load(response)
        if "folderitems" not in data or "total" not in data:
            raise ValueError("Reponse de listing invalide: " + path)
        rows = data["folderitems"]
        ids = [row.get("id") for row in rows]
        return {
            "endpoint": path,
            "parameters": payload,
            "total": data["total"],
            "returned": len(rows),
            "complete": len(rows) == data["total"],
            "ids": ids,
            "query": data.get("content_filter"),
            "catalog": data.get("catalog"),
            "catalog_indexes": data.get("catalog_indexes"),
            "catalog_columns": data.get("catalog_columns"),
        }, rows

    report = {
        "checked_at_utc": datetime.datetime.now(
            datetime.timezone.utc).isoformat(),
        "url": base,
        "mode": "consultation_only",
        "limitations": [
            "Ne cree aucun echantillon; ne prouve pas une nouvelle sauvegarde.",
            "Resultats limites aux droits du compte et a --limit.",
            "Ne compare pas directement la ZODB avec le catalogue.",
            "Requetes successives: une modification concurrente peut changer les comptes.",
        ],
        "listings": {},
    }
    cases = [
        ("samples_all", "/samples/view/folderitems", {"review_state": "all"}),
        ("samples_active", "/samples/view/folderitems", {"review_state": "default"}),
        ("dashboard_received", "/trimeta-dashboard/folderitems",
         {"sort_on": "getDateReceived"}),
        ("dashboard_created", "/trimeta-dashboard/folderitems",
         {"sort_on": "created"}),
    ]
    failed = False
    for name, path, params in cases:
        try:
            summary, rows = read_listing(path, **params)
            report["listings"][name] = summary
            if name == "samples_all":
                report["existing_samples"] = [{
                    "id": row.get("id"),
                    "state": row.get("review_state"),
                    "has_sample_code": bool(row.get("SampleCode")),
                    "code_marked_demo": "DEMO" in str(
                        row.get("SampleCode", "")).upper(),
                    "has_date_received": bool(row.get("getDateReceived")),
                } for row in rows]
                if args.sample_code:
                    report["requested_code_matches"] = [row.get("id")
                        for row in rows if row.get("SampleCode") == args.sample_code]
        except (urllib.error.URLError, ValueError, TimeoutError) as error:
            failed = True
            report["listings"][name] = {
                "error": type(error).__name__,
                "http_status": getattr(error, "code", None),
            }
    received = report["listings"].get("dashboard_received", {})
    created = report["listings"].get("dashboard_created", {})
    if received.get("complete") and created.get("complete"):
        report["missing_with_received_sort"] = sorted(
            set(created["ids"]) - set(received["ids"]))
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
