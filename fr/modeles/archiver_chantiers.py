#!/usr/bin/env python3
"""Archivage des chantiers en recette, et recherche d'un chantier, vivant ou archivé.

Un dépôt de « vivants » tient la liste des chantiers dans chantiers.yaml. Un chantier
fini passe en « statut: recette » et y reste : le fichier grossit sans fin. Ce script
sort automatiquement les chantiers en recette depuis assez longtemps vers des archives
figées (une par mois), et permet de retrouver un chantier archivé.

    python3 -B archiver_chantiers.py archiver --chantiers <chantiers.yaml> --archives <dossier> \\
        [--delai <jours, 15 par défaut>] [--date AAAA-MM-JJ] [--a-blanc]
    python3 -B archiver_chantiers.py chercher <motif> --chantiers <chantiers.yaml> \\
        --archives <dossier> [--partout]

La forme du fichier : chantiers.yaml n'est PAS du YAML standard et se lit sans
bibliothèque. Une entrée commence par « - id: <id> » en colonne 0 ; ses autres clés
suivent, une par ligne, en « <deux espaces><clé>: <valeur> ». Le bloc d'une entrée est
cette ligne et les lignes de clé qui la suivent, jusqu'à la première ligne qui n'a pas
cette forme. Les lignes vides et les commentaires entre les blocs ne sont jamais touchés.

« archiver » applique ces règles, dans l'ordre :
  1. dater : une entrée en « statut: recette » sans « recette-le: » reçoit la ligne
     « recette-le: <date du jour> » juste après son « statut: » ;
  2. dédater : une entrée qui porte « recette-le: » mais n'est plus en recette (un chantier
     rouvert) perd cette ligne ;
  3. une date illisible (« recette-le: » qui n'est pas AAAA-MM-JJ valide) : l'entrée n'est ni
     archivée ni modifiée, le script le signale et finit en code 1 ;
  4. sortir : toute entrée en recette dont « recette-le: » + délai jours <= la date du jour
     est ajoutée, bloc tel quel, en fin de <dossier>/CHANTIERS_<AAAA-MM>.yaml (le mois du
     jour) et retirée de chantiers.yaml. Une entrée datée au passage même ne sort pas ;
  5. l'archive du mois est créée avec un en-tête, ou complétée : on n'y fait qu'ajouter ;
  6. dans chantiers.yaml on retire les seules lignes des blocs sortis, sans jamais laisser
     deux lignes vides de suite ;
  7. sans perte, vérifié avant d'écrire : les lignes non vides de l'ancien fichier, plus les
     lignes « recette-le: » ajoutées, moins celles retirées, égalent (multiensemble) les
     lignes non vides du nouveau fichier plus celles des blocs ajoutés à l'archive ;
  8. l'archive est écrite d'abord, puis chantiers.yaml par un fichier temporaire et
     os.replace ; rien n'est écrit si rien ne change ; relancé à la même date, aucun
     changement.
« --date » remplace la date du jour ; « --a-blanc » dit ce qui serait fait sans rien écrire.
Le dossier d'archives doit exister : il n'est jamais créé.

« chercher » cherche dans chantiers.yaml puis dans chaque <dossier>/CHANTIERS_*.yaml (par
ordre de nom). Un motif égal à un id (casse comprise) donne ce seul chantier ; sinon on
cherche le motif, sans casse, dans l'id et le titre (dans toutes les valeurs avec
« --partout »). Une ligne par entrée : « <chemin>:<ligne> · <id> · <statut> · <titre> » ;
s'il n'y en a qu'une, son bloc complet suit.

Code de retour de « archiver » : 0 fait (avec ou sans changement), 1 fait avec au moins un
avertissement, 2 appel invalide, fichier ou dossier introuvable, ou contrôle 7 en défaut
(rien n'est écrit). Code de « chercher » : 0 au moins un trouvé, 1 aucun, 2 appel invalide
ou fichier introuvable.

Python 3.11 et plus, bibliothèque standard seulement.
"""
import argparse
import os
import re
import shutil
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

RE_ENTREE = re.compile(r"^- id:(.*)$")
RE_CLE = re.compile(r"^  ([a-z][a-z0-9-]*):(.*)$")
RE_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]

DELAI_DEFAUT = 15


@dataclass
class Bloc:
    """Une entrée : lignes [debut, fin) du fichier ; cles : clé -> (indice de ligne, valeur)."""
    debut: int
    fin: int
    id: str
    cles: dict = field(default_factory=dict)

    @property
    def ligne(self) -> int:
        return self.debut + 1

    def valeur(self, cle: str) -> str:
        return self.cles[cle][1] if cle in self.cles else ""


def lire_lignes(chemin: Path) -> tuple[list[str], bool]:
    """Les lignes du fichier (sans leur fin) et : le fichier finit-il par une fin de ligne ?"""
    texte = chemin.read_bytes().decode("utf-8")
    lignes = texte.split("\n")
    if lignes[-1] == "":
        return lignes[:-1], True
    return lignes, False


def assembler(lignes: list[str], finale: bool) -> str:
    return "\n".join(lignes) + ("\n" if finale and lignes else "")


def trouver_blocs(lignes: list[str]) -> list[Bloc]:
    """Les entrées du fichier, chacune avec ses clés (première occurrence d'une clé)."""
    blocs: list[Bloc] = []
    for i, ligne in enumerate(lignes):
        m = RE_ENTREE.match(ligne)
        if m:
            blocs.append(Bloc(i, i + 1, m.group(1).strip(), {"id": (i, m.group(1).strip())}))
            continue
        m = RE_CLE.match(ligne)
        if m and blocs and blocs[-1].fin == i:
            blocs[-1].fin = i + 1
            blocs[-1].cles.setdefault(m.group(1), (i, m.group(2).strip()))
    return blocs


def lire_date(valeur: str) -> date | None:
    if not RE_DATE.match(valeur):
        return None
    try:
        return date(int(valeur[0:4]), int(valeur[5:7]), int(valeur[8:10]))
    except ValueError:
        return None


def cle_de(ligne: str) -> str:
    m = RE_CLE.match(ligne)
    return m.group(1) if m else ""


@dataclass
class Plan:
    """Ce qu'un passage ferait : lignes à insérer, à retirer, blocs à sortir, avertissements."""
    inserer: dict = field(default_factory=dict)    # indice de ligne -> ligne à insérer après
    retirer: set = field(default_factory=set)      # indices de lignes « recette-le: » à retirer
    sortants: list = field(default_factory=list)   # blocs à sortir, dans l'ordre du fichier
    avertissements: list = field(default_factory=list)
    dates: int = 0
    dedates: int = 0


def planifier(lignes: list[str], blocs: list[Bloc], aujourdhui: date, delai: int) -> Plan:
    plan = Plan()
    for b in blocs:
        recette = b.valeur("statut") == "recette"
        if not recette:
            datees = [i for i in range(b.debut, b.fin) if cle_de(lignes[i]) == "recette-le"]
            plan.retirer.update(datees)
            plan.dedates += bool(datees)
        elif "recette-le" not in b.cles:
            i = b.cles["statut"][0]
            fin = "\r" if lignes[i].endswith("\r") else ""
            plan.inserer[i] = f"  recette-le: {aujourdhui.isoformat()}{fin}"
            plan.dates += 1
        else:
            valeur = b.valeur("recette-le")
            jour = lire_date(valeur)
            if jour is None:
                plan.avertissements.append(f"id {b.id} : recette-le illisible « {valeur} »")
            elif (aujourdhui - jour).days >= delai:
                plan.sortants.append(b)
    return plan


def lignes_vides_de_fin(lignes: list) -> int:
    n = 0
    while n < len(lignes) and lignes[-1 - n] is not None and not lignes[-1 - n].strip():
        n += 1
    return n


def reconstruire(lignes: list[str], plan: Plan) -> list[str]:
    """Les lignes de chantiers.yaml après le plan : dates posées, blocs sortis retirés."""
    sortis = {i for b in plan.sortants for i in range(b.debut, b.fin)}
    debuts = {b.debut for b in plan.sortants}
    sortie: list = []
    for i, ligne in enumerate(lignes):
        if i in sortis:
            if i in debuts:
                sortie.append(None)  # repère : un bloc est sorti ici
            continue
        if i in plan.retirer:
            continue
        sortie.append(ligne)
        if i in plan.inserer:
            sortie.append(plan.inserer[i])
    return resserrer(sortie, lignes_vides_de_fin(lignes), lignes_vides_de_fin(lignes[::-1]))


def borne_de_la_suite(i: int, j: int, total: int, vides_de_fin: int, vides_de_tete: int) -> int:
    """Combien de lignes vides garder autour d'un repère : une, sauf en tête et en fin de fichier."""
    if i == 0:
        return vides_de_tete
    return 1 if j < total else vides_de_fin


def resserrer(sortie: list, vides_de_fin: int, vides_de_tete: int) -> list[str]:
    """Sur chaque repère, la suite de lignes vides qui l'entoure se réduit à une seule au plus."""
    resultat: list[str] = []
    i = 0
    while i < len(sortie):
        if sortie[i] is not None and sortie[i].strip():
            resultat.append(sortie[i])
            i += 1
            continue
        j = i
        while j < len(sortie) and (sortie[j] is None or not sortie[j].strip()):
            j += 1
        vides = [x for x in sortie[i:j] if x is not None]
        if any(x is None for x in sortie[i:j]):
            vides = vides[:borne_de_la_suite(i, j, len(sortie), vides_de_fin, vides_de_tete)]
        resultat.extend(vides)
        i = j
    return resultat


def non_vides(lignes) -> Counter:
    return Counter(ligne for ligne in lignes if ligne.strip())


def entete_archive(aujourdhui: date, delai: int) -> str:
    mois = f"{MOIS[aujourdhui.month - 1]} {aujourdhui.year}"
    return (f"# Chantiers archivés — {mois}\n"
            "#\n"
            "# Sortis automatiquement de chantiers.yaml par archiver_chantiers.py : chantiers en recette depuis\n"
            f"# au moins {delai} jours (clé recette-le). Même forme que chantiers.yaml (pas du YAML standard).\n"
            "# On n'y fait qu'ajouter ; figé à la fin du mois. Chercher : archiver_chantiers.py chercher <mot>\n"
            "\n")


def texte_des_blocs(lignes: list[str], blocs: list[Bloc]) -> str:
    return "\n".join("\n".join(lignes[b.debut:b.fin]) + "\n" for b in blocs)


def nouvelle_archive(existant: str | None, ajout: str, entete: str) -> str:
    if existant is None:
        return entete + ajout
    if existant and not existant.endswith("\n"):
        existant += "\n"
    if existant and not existant.endswith("\n\n"):
        existant += "\n"
    return existant + ajout


def ecrire(chemin: Path, contenu: str) -> None:
    """Écriture par un fichier temporaire du même dossier, puis os.replace."""
    descripteur, temporaire = tempfile.mkstemp(prefix=".archiver-", dir=chemin.parent)
    try:
        with os.fdopen(descripteur, "wb") as sortie:
            sortie.write(contenu.encode("utf-8"))
        if chemin.exists():
            shutil.copymode(chemin, temporaire)
        else:
            os.chmod(temporaire, 0o644)
        os.replace(temporaire, chemin)
    except BaseException:
        if os.path.exists(temporaire):
            os.unlink(temporaire)
        raise


def commande_archiver(a) -> int:
    chantiers, dossier = Path(a.chantiers), Path(a.archives)
    if not chantiers.is_file():
        raise ValueError(f"fichier introuvable : --chantiers {chantiers}")
    if not dossier.is_dir():
        raise ValueError(f"dossier introuvable : --archives {dossier}")
    aujourdhui = a.date_du_jour
    lignes, finale = lire_lignes(chantiers)
    plan = planifier(lignes, trouver_blocs(lignes), aujourdhui, a.delai)
    archive = dossier / f"CHANTIERS_{aujourdhui.year:04d}-{aujourdhui.month:02d}.yaml"
    nouvelles = reconstruire(lignes, plan)
    ajout = texte_des_blocs(lignes, plan.sortants)
    ajoutees = list(plan.inserer.values())
    retirees = [lignes[i] for i in plan.retirer]
    attendu = non_vides(lignes) + non_vides(ajoutees) - non_vides(retirees)
    recu = non_vides(nouvelles) + non_vides(ajout.split("\n"))
    if attendu != recu:
        raise ControleEnDefaut("contrôle de perte en défaut : rien n'est écrit")
    changement = bool(plan.inserer or plan.retirer or plan.sortants)
    if changement and not a.a_blanc:
        if plan.sortants:
            existant = archive.read_bytes().decode("utf-8") if archive.is_file() else None
            ecrire(archive, nouvelle_archive(existant, ajout, entete_archive(aujourdhui, a.delai)))
        ecrire(chantiers, assembler(nouvelles, finale))
    afficher_resume(plan, archive)
    return 1 if plan.avertissements else 0


def afficher_resume(plan: Plan, archive: Path) -> None:
    vers = f" vers {archive}" if plan.sortants else ""
    print(f"archiver · {plan.dates} daté(s), {plan.dedates} dédaté(s), {len(plan.sortants)} archivé(s){vers}")
    for b in plan.sortants:
        print(f"  {b.id}")
    for avertissement in plan.avertissements:
        print(avertissement)


def fichiers_a_chercher(chantiers: Path, dossier: Path) -> list[Path]:
    return [chantiers] + sorted(p for p in dossier.glob("CHANTIERS_*.yaml") if p.is_file())


def entrees_trouvees(fichiers: list[Path], motif: str, partout: bool) -> list[tuple[Path, list[str], Bloc]]:
    """Les entrées qui répondent au motif : un id égal d'abord, sinon une sous-chaîne sans casse."""
    toutes = []
    for fichier in fichiers:
        lignes, _ = lire_lignes(fichier)
        toutes += [(fichier, lignes, b) for b in trouver_blocs(lignes)]
    exactes = [t for t in toutes if t[2].id == motif]
    if exactes:
        return exactes
    petit = motif.casefold()
    return [t for t in toutes if any(petit in v.casefold() for v in valeurs_cherchees(t[2], partout))]


def valeurs_cherchees(bloc: Bloc, partout: bool) -> list[str]:
    cles = bloc.cles if partout else ("id", "titre")
    return [bloc.valeur(cle) for cle in cles]


def commande_chercher(a) -> int:
    chantiers, dossier = Path(a.chantiers), Path(a.archives)
    if not chantiers.is_file():
        raise ValueError(f"fichier introuvable : --chantiers {chantiers}")
    if not dossier.is_dir():
        raise ValueError(f"dossier introuvable : --archives {dossier}")
    trouvees = entrees_trouvees(fichiers_a_chercher(chantiers, dossier), a.motif, a.partout)
    for fichier, _, b in trouvees:
        print(f"{fichier}:{b.ligne} · {b.id} · {b.valeur('statut')} · {b.valeur('titre')}")
    if len(trouvees) == 1:
        _, lignes, b = trouvees[0]
        print("\n".join(lignes[b.debut:b.fin]))
    print(f"chercher · {len(trouvees)} trouvé(s)")
    return 0 if trouvees else 1


class ControleEnDefaut(Exception):
    """Le contrôle « sans perte » (règle 7) a échoué."""


class Analyseur(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(en_francais(message))


def en_francais(message: str) -> str:
    """Les messages de l'analyseur d'arguments, traduits."""
    traductions = [
        (r"the following arguments are required: (.*)", r"argument manquant : \1"),
        (r"unrecognized arguments: (\S*).*", r"argument inconnu : \1"),
        (r"argument (\S+): expected one argument", r"\1 : valeur manquante"),
        (r"argument (\S+): invalid int value: (.*)", r"\1 : un nombre entier est attendu, reçu \2"),
        (r"argument commande: invalid choice: (\S+).*", r"commande inconnue : \1 (archiver ou chercher)"),
    ]
    for motif, remplacement in traductions:
        if re.fullmatch(motif, message):
            return re.sub(motif, remplacement, message)
    return message


def construire_analyseur() -> argparse.ArgumentParser:
    p = Analyseur(prog="archiver_chantiers.py", allow_abbrev=False, add_help=False)
    sous = p.add_subparsers(dest="commande", required=True)
    arch = sous.add_parser("archiver", allow_abbrev=False, add_help=False)
    cher = sous.add_parser("chercher", allow_abbrev=False, add_help=False)
    for s in (arch, cher):
        s.add_argument("--chantiers", required=True)
        s.add_argument("--archives", required=True)
    arch.add_argument("--delai", type=int, default=DELAI_DEFAUT)
    arch.add_argument("--date")
    arch.add_argument("--a-blanc", dest="a_blanc", action="store_true")
    cher.add_argument("motif")
    cher.add_argument("--partout", action="store_true")
    return p


def lire_arguments(argv: list[str]):
    a = construire_analyseur().parse_args(argv)
    if a.commande == "archiver":
        if a.delai < 0:
            raise ValueError("--delai : un nombre de jours positif ou nul est attendu")
        a.date_du_jour = date.today()
        if a.date is not None:
            a.date_du_jour = lire_date(a.date)
            if a.date_du_jour is None:
                raise ValueError(f"--date : AAAA-MM-JJ attendu, reçu « {a.date} »")
    return a


def main(argv: list[str]) -> int:
    try:
        a = lire_arguments(argv)
        return commande_archiver(a) if a.commande == "archiver" else commande_chercher(a)
    except (ValueError, ControleEnDefaut, OSError, UnicodeDecodeError) as erreur:
        print(f"archiver_chantiers : {' '.join(str(erreur).split())}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
