#!/usr/bin/env python3
"""Vérificateur des vivants partagés — contrôle en lecture seule.

Quand plusieurs chefs de projet écrivent en même temps dans un dépôt de
« vivants », ce script vérifie que les documents partagés restent cohérents :
le registre des arbitrages, la source des chantiers (chantiers.yaml), la page
qui s'en régénère (chantiers.html) et le journal des lots du plan.

    python3 -B verifier_vivants.py --chantiers <chantiers.yaml> --registre <registre.md> \\
        [--tableau <chantiers.html> --generateur <generer_tableau.py>] [--journal <plan.md>]

« --tableau » et « --generateur » vont ensemble ; « --journal » est facultatif.
Un contrôle dont les fichiers ne sont pas donnés s'affiche « non demandé ».

Les huit contrôles, dans cet ordre :
  1. numéros du registre : les lignes « | **R<n>** | » n'ont aucun numéro en
     double et aucun trou entre le plus petit et le plus grand ;
  2. réservations : une ligne « | **R<n>** | *réservé … » encore présente est un
     avertissement, pas un écart (une réservation vit le temps d'écrire l'entrée) ;
  3. identifiants de chantier : aucune « id: » en double dans chantiers.yaml ;
  4. versions des lots : aucune valeur de « version: » portée par deux entrées ;
  5. chantiers en vol : chaque entrée « statut: en-vol » porte un « cdp: » non vide ;
  6. tableau : la régénération de chantiers.yaml par le générateur, dans un
     dossier temporaire, est égale à l'octet à chantiers.html, après avoir
     remplacé dans les deux textes chaque date « jj/mm/aaaa » par un même jeton
     (le générateur date la page du jour où il tourne) ;
  7. journal : la dernière version du journal (dernière ligne du plan qui
     commence par « | `v…` | ») a une entrée de chantiers.yaml en
     « statut: recette » dont l'id ou la version la contient ;
  8. livrables : un livrable (« livrable: », le dépôt de code d'où sort la
     release) n'a qu'un seul lot en vol à la fois, et un lot qui attend
     (« attend: <id> ») est suspendu. Trois règles : (a) pour chaque valeur de
     « livrable: », au plus une entrée en « statut: en-vol » ; (b) chaque
     « attend: » désigne l'id d'une entrée qui existe ; (c) une entrée qui porte
     « attend: » n'est pas en « statut: en-vol ». Ce contrôle ne dépend que de
     « --chantiers » : il tourne toujours.

Sortie : une ligne par contrôle (OK, ÉCART ou avertissement, avec un compte),
le détail des écarts indenté dessous, puis une dernière ligne « VIVANTS · … ».
Code de retour : 0 sans écart, 1 avec au moins un écart, 2 pour un appel
invalide (argument manquant, fichier introuvable).

Python 3, bibliothèque standard seulement. Le lecteur YAML est volontairement
pauvre, comme celui du générateur : « - id: » puis des « clé: valeur » sur une
seule ligne.
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RE_NUMERO = re.compile(r"^\|\s*\*\*R(\d+)\*\*\s*\|")
RE_RESERVATION = re.compile(r"^\|\s*\*\*R(\d+)\*\*\s*\|\s*\*réservé")
RE_JOURNAL = re.compile(r"^\|\s*`(v[^`]*)`\s*\|")
RE_DATE = re.compile(rb"\d{2}/\d{2}/\d{4}")

NON_DEMANDE = "—  non demandé"


def lire_texte(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def lire_chantiers(chemin: Path) -> list[dict]:
    """Même lecteur que le générateur ; chaque entrée garde sa ligne source."""
    chantiers: list[dict] = []
    for numero, ligne in enumerate(lire_texte(chemin).split("\n"), start=1):
        nue = ligne.strip()
        if not nue or nue.startswith("#"):
            continue
        if nue.startswith("- "):
            chantiers.append({"_ligne": numero})
            nue = nue[2:]
        if ":" not in nue or not chantiers:
            continue
        cle, _, valeur = nue.partition(":")
        chantiers[-1][cle.strip()] = valeur.strip()
    return chantiers


def nom(c: dict) -> str:
    return c.get("id") or f"(sans id, ligne {c['_ligne']})"


def plages(numeros: list[int]) -> list[str]:
    """['R320', 'R325 à R327 (3 numéros)'] à partir d'une liste triée."""
    sortie, i = [], 0
    while i < len(numeros):
        j = i
        while j + 1 < len(numeros) and numeros[j + 1] == numeros[j] + 1:
            j += 1
        if i == j:
            sortie.append(f"R{numeros[i]}")
        else:
            sortie.append(f"R{numeros[i]} à R{numeros[j]} ({j - i + 1} numéros)")
        i = j + 1
    return sortie


# Chaque contrôle rend (verdict, compte, détails) ; verdict : OK, ÉCART ou avertissement.

def controle_numeros(registre: Path):
    lignes: dict[int, list[int]] = {}
    for position, ligne in enumerate(lire_texte(registre).split("\n"), start=1):
        m = RE_NUMERO.match(ligne)
        if m:
            lignes.setdefault(int(m.group(1)), []).append(position)
    total = sum(len(v) for v in lignes.values())
    if not lignes:
        return "ÉCART", "aucun numéro trouvé", ["aucune ligne « | **R<n>** | » dans le registre"]
    details = [f"R{n} en double (lignes {', '.join(map(str, v))})"
               for n, v in sorted(lignes.items()) if len(v) > 1]
    manquants = [n for n in range(min(lignes), max(lignes) + 1) if n not in lignes]
    details += [f"{p} manquant" if " " not in p else f"{p} manquants" for p in plages(manquants)]
    compte = f"{total} numéros, R{min(lignes)} à R{max(lignes)}"
    return ("ÉCART" if details else "OK"), compte, details


def controle_reservations(registre: Path):
    trouvees = []
    for position, ligne in enumerate(lire_texte(registre).split("\n"), start=1):
        m = RE_RESERVATION.match(ligne)
        if m:
            trouvees.append(f"R{m.group(1)} réservé (ligne {position})")
    if trouvees:
        return "avertissement", f"{len(trouvees)} réservation(s) en cours", trouvees
    return "OK", "aucune réservation en cours", []


def controle_identifiants(chantiers: list[dict]):
    vus: dict[str, list[int]] = {}
    for c in chantiers:
        if c.get("id"):
            vus.setdefault(c["id"], []).append(c["_ligne"])
    details = [f"id {i} en double (lignes {', '.join(map(str, v))})"
               for i, v in vus.items() if len(v) > 1]
    return ("ÉCART" if details else "OK"), f"{len(chantiers)} chantiers", details


def controle_versions(chantiers: list[dict]):
    portees: dict[str, list[str]] = {}
    for c in chantiers:
        if c.get("version"):
            portees.setdefault(c["version"], []).append(nom(c))
    details = [f"version {v} portée par {' et '.join(ids)}"
               for v, ids in portees.items() if len(ids) > 1]
    return ("ÉCART" if details else "OK"), f"{len(portees)} versions", details


def controle_en_vol(chantiers: list[dict]):
    en_vol = [c for c in chantiers if c.get("statut") == "en-vol"]
    details = [f"{nom(c)} (ligne {c['_ligne']}) : cdp absent ou vide"
               for c in en_vol if not c.get("cdp")]
    return ("ÉCART" if details else "OK"), f"{len(en_vol)} en vol", details


def controle_tableau(chantiers: list[dict], chantiers_yaml: Path, tableau: Path, generateur: Path):
    compte = f"{len(chantiers)} chantiers"
    with tempfile.TemporaryDirectory(prefix="vivants-") as dossier:
        sortie = Path(dossier) / "regeneration.html"
        essai = subprocess.run([sys.executable, "-B", str(generateur.resolve()), str(chantiers_yaml.resolve()), str(sortie)],
                               capture_output=True, text=True, cwd=dossier)
        if essai.returncode != 0 or not sortie.is_file():
            message = (essai.stderr.strip() or essai.stdout.strip() or "sans message").splitlines()[-1]
            return "ÉCART", compte, [f"le générateur a échoué (code {essai.returncode}) : {message}"]
        brut, regenere = tableau.read_bytes(), sortie.read_bytes()
    voulu, obtenu = RE_DATE.sub(b"<date>", brut), RE_DATE.sub(b"<date>", regenere)
    if voulu == obtenu:
        return "OK", f"{compte}, {len(brut)} octets identiques hors date", []
    rang = next((i for i, (a, b) in enumerate(zip(voulu, obtenu)) if a != b), min(len(voulu), len(obtenu)))
    ligne = voulu.count(b"\n", 0, rang) + 1
    return "ÉCART", compte, [f"le tableau diffère de sa régénération (dates masquées) : premier écart à l'octet "
                             f"{rang} (ligne {ligne}) ; {len(voulu)} octets contre {len(obtenu)} régénérés"]


def controle_journal(chantiers: list[dict], journal: Path):
    derniere = None
    for ligne in lire_texte(journal).split("\n"):
        m = RE_JOURNAL.match(ligne)
        if m:
            derniere = m.group(1)
    if derniere is None:
        return "ÉCART", "aucune version", ["aucune ligne « | `v…` | » dans le journal"]
    portent = [c for c in chantiers if derniere in c.get("id", "") or derniere in c.get("version", "")]
    recettes = [c for c in portent if c.get("statut") == "recette"]
    if recettes:
        return "OK", f"dernière version {derniere}", []
    details = [f"{derniere} : aucune entrée en statut recette ne porte cette version"]
    details += [f"{nom(c)} la porte mais est en statut {c.get('statut') or 'vide'}" for c in portent]
    return "ÉCART", f"dernière version {derniere}", details


def controle_livrables(chantiers: list[dict]):
    livrables: dict[str, list[str]] = {}  # livrable -> ids des entrées en vol
    for c in chantiers:
        if c.get("livrable"):
            livrables.setdefault(c["livrable"], [])
            if c.get("statut") == "en-vol":
                livrables[c["livrable"]].append(nom(c))
    ids = {c["id"] for c in chantiers if c.get("id")}
    details = [f"livrable {livrable} : {len(en_vol)} lots en vol ({', '.join(en_vol)})"
               for livrable, en_vol in livrables.items() if len(en_vol) > 1]
    attendent = [c for c in chantiers if c.get("attend")]
    details += [f"{nom(c)} attend {c['attend']}, qui n'existe pas"
                for c in attendent if c["attend"] not in ids]
    details += [f"{nom(c)} est en vol mais attend {c['attend']}"
                for c in attendent if c.get("statut") == "en-vol"]
    en_vol = sum(len(v) for v in livrables.values())
    compte = f"{len(livrables)} livrables, {en_vol} en vol, {len(attendent)} en attente"
    return ("ÉCART" if details else "OK"), compte, details


class Analyseur(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message.replace("expected one argument", "valeur manquante"))


def lire_arguments(argv: list[str]):
    p = Analyseur(prog="verifier_vivants.py", allow_abbrev=False, add_help=False)
    for option in ("chantiers", "registre", "tableau", "generateur", "journal"):
        p.add_argument(f"--{option}")
    a, inconnus = p.parse_known_args(argv)
    if inconnus:
        raise ValueError(f"argument inconnu : {inconnus[0]}")
    for option in ("chantiers", "registre"):
        if not getattr(a, option):
            raise ValueError(f"argument manquant : --{option}")
    if bool(a.tableau) != bool(a.generateur):
        raise ValueError("--tableau et --generateur vont ensemble")
    chemins = {option: Path(getattr(a, option)) for option in
               ("chantiers", "registre", "tableau", "generateur", "journal") if getattr(a, option)}
    for option, chemin in chemins.items():
        if not chemin.is_file():
            raise ValueError(f"fichier introuvable : --{option} {chemin}")
    return chemins


def main(argv: list[str]) -> int:
    try:
        f = lire_arguments(argv)
        chantiers = lire_chantiers(f["chantiers"])
        for option in ("registre", "journal"):  # lecture d'essai : un fichier illisible est un appel invalide
            if option in f:
                lire_texte(f[option])
    except (ValueError, OSError, UnicodeDecodeError) as erreur:
        print(f"verifier_vivants : {' '.join(str(erreur).split())}", file=sys.stderr)
        return 2

    controles = [
        ("numéros du registre", lambda: controle_numeros(f["registre"])),
        ("réservations", lambda: controle_reservations(f["registre"])),
        ("identifiants de chantier", lambda: controle_identifiants(chantiers)),
        ("versions des lots", lambda: controle_versions(chantiers)),
        ("chantiers en vol", lambda: controle_en_vol(chantiers)),
        ("tableau", (lambda: controle_tableau(chantiers, f["chantiers"], f["tableau"], f["generateur"]))
         if "tableau" in f else None),
        ("journal", (lambda: controle_journal(chantiers, f["journal"])) if "journal" in f else None),
        ("livrables", lambda: controle_livrables(chantiers)),
    ]
    ecarts = 0
    for rang, (libelle, controle) in enumerate(controles, start=1):
        if controle is None:
            print(f"{rang}  {libelle:<26} {NON_DEMANDE}")
            continue
        verdict, compte, details = controle()
        ecarts += verdict == "ÉCART"
        print(f"{rang}  {libelle:<26} {verdict:<13}  {compte}")
        for detail in details:
            print(f"      {detail}")
    print("VIVANTS · aucun écart" if not ecarts else f"VIVANTS · {ecarts} écart(s)")
    return 1 if ecarts else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
