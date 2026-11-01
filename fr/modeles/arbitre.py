#!/usr/bin/env python3
"""L'arbitre des vivants, en passage planifié — un script, sans session et sans jeton de modèle.

Chaque matin, une action planifiée lance ce script sur le dépôt des documents vivants : il contrôle, dépose un
chantier par écart nouveau, archive, écrit une ligne de journal et rend un code. Tout y est déterministe ; le
jugement des documents (contradiction, doublon, historique inutile) reste à une autre session, le contrôleur.
Le comportement est celui de la procédure de l'arbitre (ARBITRE.md, §1 à §3).

    python3 -B arbitre.py --chantiers <chantiers.yaml> --registre <registre.md> --archives <dossier> \\
        --domaines <domaines.yaml> --journal-arbitre <journal.md> \\
        [--tableau <page> --generateur <script>] [--journal <plan.md>] [--racine <dossier>] \\
        [--methode <fichier>] [--fiche <fichier>] [--registre-depuis <n>] [--date "AAAA-MM-JJ HH:MM"]

Les options sont celles du vérificateur (verifier_vivants.py) pour les cinq premières, « --tableau » et
« --generateur » vont ensemble, « --racine » est le dossier d'où se lisent les checkpoints de la table des
domaines (le dossier courant par défaut ; c'est aussi le dossier de git). « --methode » (la méthode du projet) et
« --fiche » (la fiche commune) ne servent qu'à mesurer le socle du journal. « --registre-depuis » (le numéro de la
première entrée du registre mesurée par le contrôle 12) est passée telle quelle au vérificateur ; absente, rien n'est
passé et le registre n'est pas mesuré ; les plafonds restent ceux du vérificateur. « --date » (heure de Paris) sert aux
tests ; sans elle, c'est l'heure de Paris (zoneinfo, Europe/Paris). Le vérificateur, l'archiveur et
le script lui-même se trouvent dans le même dossier ; le générateur est celui de « --generateur ».
Bibliothèque standard seule, Python 3.11 au moins.

Un passage fait, dans l'ordre :
  1. normaliser (archiver_chantiers.py normaliser) ;
  2. contrôler (verifier_vivants.py) et relever les lignes d'écart ;
  3. déposer UN chantier par écart nouveau, en fin de chantiers.yaml, au format YAML strict : l'id
     « arbitre-c<n>-<clé> » (<n> le numéro du contrôle) ; le contrôle 9 en un chantier par domaine
     (« arbitre-c9-checkpoint-<domaine>-<AAAAMMJJ> »), le contrôle 10 de même
     (« arbitre-c10-checkpoint-court-<domaine>-<AAAAMMJJ> »), le contrôle 12 de même
     (« arbitre-c12-entrees-courtes-<domaine>-<AAAAMMJJ> » ; les lignes « hors domaine » et « registre » vont au
     chantier du domaine du coordinateur), un défaut de la table des domaines en un seul chantier
     pour le coordinateur (« arbitre-c9-table-<AAAAMMJJ> ») ; jamais en double : un chantier de même id (vivant)
     est déjà signalé, un id archivé ne se réutilise pas (on ajoute « -<AAAAMMJJ> »), un chantier de domaine
     « arbitre-c9-checkpoint-<domaine>-* » ou « arbitre-c9-table-* » encore ouvert (pas en recette) suffit, et
     pour le contrôle 10, un chantier ouvert « pour: » ce CdP dont l'id porte « checkpoint-court » aussi, et pour le
     contrôle 12, un chantier ouvert « pour: » ce CdP dont l'id porte « entrees-courtes » ;
  4. les témoins : la ligne « Session en activité » de chaque checkpoint de domaine et le dernier commit qui porte
     son identifiant — une information (le journal et la sortie), jamais un chantier ; la coordination (le domaine
     dont le « cdp » contient « Coordination ») est exclue ;
  5. le checkpoint en retard : un chantier du domaine, en recette et sans « pour: », dont la date d'acceptation est
     postérieure à la date du dernier commit du checkpoint, est une ligne du chantier du contrôle 9 de ce domaine ;
     la date d'acceptation est celle du commit qui l'a fait passer en recette (le plus ancien commit de
     chantiers.yaml d'où il est en recette sans interruption jusqu'à HEAD), pas « recette-le: », que l'arbitre pose
     lui-même à son passage ; sans cette preuve dans l'historique disponible, pas de ligne ;
  6. archiver (archiver_chantiers.py archiver) ;
  7. si chantiers.yaml a changé : régénérer le tableau (avec « --tableau »), puis contrôler de nouveau ;
  8. ajouter une ligne en fin de « --journal-arbitre » ;
  9. imprimer le résumé.

Le destinataire « pour: » se lit dans les données : le « cdp » du domaine (table « --domaines ») pour un chantier
de domaine, le « cdp: » d'un chantier en vol, sinon celui que le chantier porte, sinon le coordinateur (l'entrée de
la table dont le « cdp » contient « Coordination » : sans elle, code 2).

Le script ne commite pas et ne pousse pas : le workflow s'en charge. La dernière ligne de la sortie,
« Commit : <message> », est le message du commit. Il n'écrit que dans : la fin de chantiers.yaml, le tableau
régénéré, la fin du journal de l'arbitre, et ce que font l'archiveur et le normaliseur.

Code de retour : 0 sans chantier nouveau, 1 avec au moins un chantier nouveau, 2 si un fichier manque ou si un
script échoue (le journal dit alors « contrôle impossible : <fichier> »).
"""
import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

sys.dont_write_bytecode = True

ICI = Path(__file__).resolve().parent
FUSEAU = "Europe/Paris"
SILENCE = timedelta(hours=24)
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
ECART = "ÉCART"
OPTIONS_FICHIERS = ("chantiers", "registre", "domaines", "journal_arbitre", "tableau", "generateur", "journal",
                    "methode", "fiche")
RE_ENTETE = re.compile(r"^(\d+)\s+(.+?)\s+(ÉCART|avertissement|OK)\s+(.*)$")
RE_NON_DEMANDE = re.compile(r"^(\d+)\s+(.+?)\s+—\s+non demandé$")
RE_DEFAUT_TABLE = re.compile(r"checkpoint introuvable|checkpoint illisible|section de file introuvable"
                             r"|domaine ou checkpoint manquant")
RE_JOUR = re.compile(r"\d{4}-\d{2}-\d{2}")
RE_TEMOIN = re.compile(r"^\**\s*Session en activité\s*:")
RE_IDENTIFIANT = re.compile(r"^\**\s*Session en activité\s*:\s*\**\s*([A-Za-z0-9]{8})(?=\s*,|\s+depuis\b)")
ACTIONS = {
    1: "Corriger le registre : un numéro est unique et sans trou.",
    3: "Rendre l'id unique, chantiers vivants et archives compris (un id archivé ne se réutilise pas).",
    4: ("Une version n'est portée que par un seul lot ; un lot en vol passe au-dessus de la plus haute version de "
        "son livrable."),
    5: "Renseigner le cdp: du chantier en vol.",
    6: "Régénérer la page du tableau et son fichier de données depuis chantiers.yaml, après le dernier pull.",
    7: "Passer en recette l'entrée de la dernière version du journal, ou mettre le journal d'accord avec chantiers.yaml.",
    8: "Un seul lot en vol par livrable ou ressource, et un attend: qui désigne un id existant et jamais un lot en vol.",
    11: "Corriger à la main la valeur : elle porte un caractère de contrôle, que la normalisation ne sait pas écrire.",
}


class Impossible(Exception):
    """Le contrôle est impossible : « fichier » dit ce qui manque ou échoue, « detail » le message (code 2)."""

    def __init__(self, fichier: str, detail: str = ""):
        super().__init__(detail or fichier)
        self.fichier, self.detail = fichier, detail


# ───────────────────────────── les scripts voisins ─────────────────────────────

def charger(nom: str):
    """Importe un script voisin par son chemin (ses fonctions de lecture ; il ne s'exécute pas : garde __main__)."""
    import importlib.util
    chemin = ICI / nom
    if not chemin.is_file():
        raise Impossible(str(chemin), f"script introuvable : {chemin}")
    spec = importlib.util.spec_from_file_location("_arbitre_" + chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lancer(script: Path, *arguments) -> subprocess.CompletedProcess:
    if not Path(script).is_file():
        raise Impossible(str(script), f"script introuvable : {script}")
    return subprocess.run([sys.executable, "-B", str(script), *map(str, arguments)],
                          capture_output=True, text=True, encoding="utf-8")


def derniere_ligne(processus: subprocess.CompletedProcess) -> str:
    texte = (processus.stderr.strip() or processus.stdout.strip() or "sans message")
    return texte.splitlines()[-1]


def git(racine: Path, *arguments, erreurs: str = "strict") -> tuple[int, str]:
    processus = subprocess.run(["git", "-C", str(racine), *arguments], capture_output=True, text=True,
                               encoding="utf-8", errors=erreurs,
                               env={**os.environ, "LC_ALL": "C", "GIT_TERMINAL_PROMPT": "0"})
    return processus.returncode, processus.stdout.strip()


# ───────────────────────────── les arguments ─────────────────────────────

class Analyseur(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message.replace("expected one argument", "valeur manquante"))


def lire_arguments(argv: list[str]):
    p = Analyseur(prog="arbitre.py", allow_abbrev=False, add_help=False)
    for option in ("chantiers", "registre", "archives", "domaines", "journal-arbitre", "tableau", "generateur",
                   "journal", "racine", "methode", "fiche", "registre-depuis", "date"):
        p.add_argument(f"--{option}")
    a, inconnus = p.parse_known_args(argv)
    if inconnus:
        raise ValueError(f"argument inconnu : {inconnus[0]}")
    for option in ("chantiers", "registre", "archives", "domaines", "journal_arbitre"):
        if not getattr(a, option):
            raise ValueError(f"argument manquant : --{option.replace('_', '-')}")
    if bool(a.tableau) != bool(a.generateur):
        raise ValueError("--tableau et --generateur vont ensemble")
    return a


def lire_date(texte: str | None) -> datetime:
    """L'instant du passage, à l'heure de Paris (celle de « --date » si elle est donnée)."""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        fuseau = ZoneInfo(FUSEAU)
    except ZoneInfoNotFoundError:
        raise ValueError(f"fuseau {FUSEAU} introuvable (le paquet tzdata manque)")
    if texte is None:
        return datetime.now(fuseau)
    try:
        return datetime.strptime(texte, "%Y-%m-%d %H:%M").replace(tzinfo=fuseau)
    except ValueError:
        raise ValueError(f"--date : AAAA-MM-JJ HH:MM attendu, reçu « {texte} »")


# ───────────────────────────── le contrôle ─────────────────────────────

@dataclass
class Controle:
    """La sortie du vérificateur : {rang: (verdict, compte, [détails])} et la dernière ligne."""
    rangs: dict = field(default_factory=dict)
    bilan: str = ""
    code: int = 0

    def ecarts(self) -> int:
        return sum(1 for verdict, _, _ in self.rangs.values() if verdict == ECART)

    def lignes(self, rang: int) -> list[str]:
        verdict, _, details = self.rangs.get(rang, ("", "", []))
        return details if verdict == ECART else []


def lire_sortie(texte: str, code: int) -> Controle:
    controle, dernier = Controle(code=code), None
    for ligne in texte.split("\n"):
        if not ligne.strip():
            continue
        if ligne.startswith("      ") and dernier is not None:
            controle.rangs[dernier][2].append(ligne.strip())
            continue
        m = RE_ENTETE.match(ligne)
        if m:
            dernier = int(m.group(1))
            controle.rangs[dernier] = (m.group(3), m.group(4), [])
            continue
        m = RE_NON_DEMANDE.match(ligne)
        if m:
            dernier = None
            controle.rangs[int(m.group(1))] = ("non demandé", "", [])
            continue
        dernier = None
        controle.bilan = ligne
    return controle


def controler(a) -> Controle:
    options = ["--chantiers", a.chantiers, "--registre", a.registre, "--archives", a.archives,
               "--domaines", a.domaines]
    if a.tableau:
        options += ["--tableau", a.tableau, "--generateur", a.generateur]
    if a.journal:
        options += ["--journal", a.journal]
    if a.racine:
        options += ["--racine", a.racine]
    if a.registre_depuis:
        options += ["--registre-depuis", a.registre_depuis]
    processus = lancer(ICI / "verifier_vivants.py", *options)
    if processus.returncode not in (0, 1):
        raise Impossible("verifier_vivants.py", f"verifier_vivants.py a échoué (code {processus.returncode}) : "
                                                 f"{derniere_ligne(processus)}")
    return lire_sortie(processus.stdout, processus.returncode)


# ───────────────────────────── les constats ─────────────────────────────

@dataclass
class Constat:
    """Un chantier à déposer : id, titre, module, destinataire, mesure."""
    id: str
    titre: str
    module: str
    pour: str
    mesure: str


def date_longue(jour: date) -> str:
    return f"{jour.day} {MOIS[jour.month - 1]} {jour.year}"


def cle_sure(texte: str) -> str:
    """Une clé d'id : lettres, chiffres, point, tiret et soulignement."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", texte).strip("-") or "cas"


class Contexte:
    """Ce que lisent les règles de destinataire : chantiers, archives, domaines valides, coordinateur."""

    def __init__(self, verifier, chantiers: list[dict], archives: list[dict], table: list[dict], fichier: str):
        self.verifier = verifier
        self.chantiers, self.archives, self.table = chantiers, archives, table
        self.valides = [d for d in table if d.get("domaine") and d.get("checkpoint")]
        self.par_id = {c["id"]: c for c in chantiers if c.get("id")}
        coordination = next((d for d in table if "Coordination" in d.get("cdp", "")), None)
        if coordination is None:
            raise Impossible(fichier, f"aucune entrée Coordination dans la table des domaines ({fichier}) : "
                                      "le nom du coordinateur s'y lit")
        self.coordinateur = coordination["cdp"]
        self.domaine_coordination = coordination.get("domaine") or "coordination"
        self.cdp_de = {d["domaine"]: d.get("cdp") or self.coordinateur for d in self.valides}

    def domaine_de(self, c: dict) -> str | None:
        return self.verifier.domaine_de(c, self.valides) if c.get("id") else None

    def destinataire(self, c: dict | None) -> str:
        """§2 : un chantier en vol va au cdp qu'il porte ; un chantier de domaine au cdp du domaine ; sinon au
        cdp qu'il porte ; sinon au coordinateur."""
        if c is None:
            return self.coordinateur
        if c.get("statut") == "en-vol" and c.get("cdp"):
            return c["cdp"]
        domaine = self.domaine_de(c)
        if domaine:
            return self.cdp_de[domaine]
        return c.get("cdp") or self.coordinateur

    def module_de(self, c: dict | None) -> str:
        return (c or {}).get("module") or "methode"


def cas_du_controle(rang: int, ligne: str, ctx: Contexte):
    """Les cas (clé, chantier en cause) d'une ligne d'écart des contrôles autres que 9 et 10 ; [] si ce n'est pas un cas."""
    def chantier(i):
        return ctx.par_id.get(i)

    if rang == 1:
        m = re.match(r"R(\d+)", ligne)
        return [(f"R{m.group(1)}" if m else "registre", None)]
    if rang == 3:
        m = re.match(r"id (\S+) ", ligne)
        return [(cle_sure(m.group(1)), chantier(m.group(1)))] if m else [(cle_sure(ligne[:40]), None)]
    if rang == 4:
        # deux formes : « version <v> portée par <id> et <id> » (a) ; « <id> : <v> n'est pas au-dessus de … » (b)
        m = re.match(r"version (\S+) portée par (.+)$", ligne)
        if m:
            premier = m.group(2).split(" et ")[0]
            return [(cle_sure(premier), chantier(premier))]
        m = re.match(r"(\S+) : .+? n'est pas au-dessus de ", ligne)
        if m:
            return [(cle_sure(m.group(1)), chantier(m.group(1)))]
        return [(cle_sure(ligne[:40]), None)]
    if rang == 5:
        m = re.match(r"(.+?) \(ligne (\d+)\) : ", ligne)
        if m and m.group(1).startswith("(sans id"):
            return [(f"ligne-{m.group(2)}", None)]
        return [(cle_sure(m.group(1)), chantier(m.group(1)))] if m else [(cle_sure(ligne[:40]), None)]
    if rang == 6:
        return [("tableau", None)]
    if rang == 7:
        return [("journal", None)]
    if rang == 8:
        m = re.match(r"(?:livrable|ressource) .+ : \d+ lots en vol \((.+)\)$", ligne)
        if m:  # les CdP des lots en cause, un chantier chacun
            return [(cle_sure(i), chantier(i)) for i in m.group(1).split(", ")]
        m = re.match(r"(\S+) (?:attend|est en vol mais attend) ", ligne)
        return [(cle_sure(m.group(1)), chantier(m.group(1)))] if m else [(cle_sure(ligne[:40]), None)]
    if rang == 11:
        if ligne.startswith("pour normaliser"):
            return []
        m = re.match(r"(.*):\d+ : clé ", ligne)
        return [(f"format-{cle_sure(Path(m.group(1)).stem)}", None)] if m else [(cle_sure(ligne[:40]), None)]
    return [(cle_sure(ligne[:40]), None)]


def constats_ordinaires(controle: Controle, ctx: Contexte, jour: date) -> list[Constat]:
    """Un constat par cas des contrôles autres que 9, 10 et 12 ; les lignes d'une même clé se groupent."""
    constats = []
    for rang in sorted(controle.rangs):
        if rang in (9, 10, 12):
            continue
        groupes: dict[str, tuple] = {}
        for ligne in controle.lignes(rang):
            for cle, en_cause in cas_du_controle(rang, ligne, ctx):
                lignes = groupes.setdefault(cle, (en_cause, []))[1]
                if ligne not in lignes:
                    lignes.append(ligne)
        libelle = ACTIONS.get(rang, "Corriger le cas signalé.")
        for cle, (en_cause, lignes) in groupes.items():
            titre = f"Contrôle {rang} : {lignes[0]}" + (f" (et {len(lignes) - 1} autre(s))" if len(lignes) > 1 else "")
            constats.append(Constat(
                id=f"arbitre-c{rang}-{cle}", titre=titre, module=ctx.module_de(en_cause),
                pour=ctx.destinataire(en_cause),
                mesure=f"Signalé par l'arbitre le {date_longue(jour)} (contrôle {rang}). {' ; '.join(lignes)}. {libelle}"))
    return constats


def nom_du_domaine(ligne: str) -> str:
    return ligne.split(" : ", 1)[0]


def constats_checkpoints(controle: Controle, retards: dict, ctx: Contexte, jour: date) -> tuple[list[Constat], list[str]]:
    """Les constats des contrôles 9 et 10 et du retard : un par domaine (le défaut de la table, un seul au
    coordinateur). Rend aussi les domaines signalés, dans l'ordre de la table."""
    stamp, jour_long = jour.strftime("%Y%m%d"), date_longue(jour)
    table_lignes, par_domaine, trop_lourds = [], {}, {}
    for ligne in controle.lignes(9):
        if RE_DEFAUT_TABLE.search(ligne):
            table_lignes.append(ligne)
        else:
            par_domaine.setdefault(nom_du_domaine(ligne), []).append(ligne)
    for ligne in controle.lignes(10):
        trop_lourds.setdefault(nom_du_domaine(ligne), []).append(ligne)
    retardataires = {d: list(lignes) for d, lignes in retards.items() if lignes}
    constats = []
    if table_lignes:
        constats.append(Constat(
            id=f"arbitre-c9-table-{stamp}", titre="La table des domaines est en défaut", module="methode",
            pour=ctx.coordinateur,
            mesure=(f"Signalé par l'arbitre le {jour_long} (contrôle 9). {' ; '.join(table_lignes)}. "
                    "Aligner la table des domaines et le checkpoint : le CdP a peut-être renommé son checkpoint ou "
                    "sa section, revenir au titre convenu ou corriger la table.")))
    ordre = [d["domaine"] for d in ctx.valides]
    inconnus = [d for d in list(par_domaine) + list(trop_lourds) + list(retardataires) if d not in ordre]
    for domaine in ordre + sorted(set(inconnus)):
        lignes9, retard = par_domaine.get(domaine, []), retardataires.get(domaine, [])
        if lignes9 or retard:
            actions = []
            if lignes9:
                actions.append("Citer chaque chantier ouvert de ton domaine par son id dans ton checkpoint, retirer de "
                               "ta file les chantiers clos (méthode §6).")
            if retard:
                actions.append("Reprendre ton checkpoint : un chantier de ton domaine est en recette depuis une date "
                               "postérieure à son dernier commit (méthode §6).")
            constats.append(Constat(
                id=f"arbitre-c9-checkpoint-{domaine}-{stamp}", titre=f"Le checkpoint de {domaine} est en retard sur ses chantiers",
                module="methode", pour=ctx.cdp_de.get(domaine, ctx.coordinateur),
                mesure=(f"Signalé par l'arbitre le {jour_long} (contrôle 9). {' ; '.join(lignes9 + retard)}. "
                        f"{' '.join(actions)}")))
    for domaine in ordre + sorted(set(inconnus)):
        lignes10 = trop_lourds.get(domaine, [])
        if lignes10:
            chemin = next((d["checkpoint"] for d in ctx.valides if d["domaine"] == domaine), "")
            dossier = chemin.rsplit("/", 1)[0] + "/" if "/" in chemin else ""
            constats.append(Constat(
                id=f"arbitre-c10-checkpoint-court-{domaine}-{stamp}", titre=f"Le checkpoint de {domaine} dépasse 10 Ko",
                module="methode", pour=ctx.cdp_de.get(domaine, ctx.coordinateur),
                mesure=(f"Signalé par l'arbitre le {jour_long} (contrôle 10). {' ; '.join(lignes10)}. "
                        f"Sortir l'historique vers `{dossier}Archives/`, cité en une ligne ; le checkpoint tient en 10 Ko "
                        "(méthode §6).")))
    signales = [d for d in ordre + sorted(set(inconnus)) if par_domaine.get(d) or trop_lourds.get(d) or retardataires.get(d)]
    return constats, signales


def constats_entrees(controle: Controle, ctx: Contexte, jour: date) -> list[Constat]:
    """Les constats du contrôle 12 : un par domaine, dans l'ordre de la table ; les lignes « hors domaine » et « registre »
    se groupent avec celles du domaine du coordinateur."""
    par_domaine: dict[str, list[str]] = {}
    for ligne in controle.lignes(12):
        domaine = nom_du_domaine(ligne)
        if domaine in ("hors domaine", "registre"):
            domaine = ctx.domaine_coordination
        par_domaine.setdefault(domaine, []).append(ligne)
    ordre = [d["domaine"] for d in ctx.valides]
    constats = []
    for domaine in ordre + sorted(d for d in par_domaine if d not in ordre):
        lignes = par_domaine.get(domaine)
        if not lignes:
            continue
        constats.append(Constat(
            id=f"arbitre-c12-entrees-courtes-{domaine}-{jour.strftime('%Y%m%d')}",
            titre=f"Des entrées de {domaine} dépassent leur plafond", module="methode",
            pour=ctx.cdp_de.get(domaine, ctx.coordinateur),
            mesure=(f"Signalé par l'arbitre le {date_longue(jour)} (contrôle 12). {' ; '.join(lignes)}. "
                    "Ramener chaque entrée sous son plafond (méthode §6) : l'état, la décision, le prochain geste ; "
                    "le détail part au dossier du lot ou à une note du domaine, l'entrée n'en garde que le résumé "
                    "et le chemin.")))
    return constats


def est_ouvert(c: dict) -> bool:
    return c.get("statut") != "recette"


def deja_signale(constat: Constat, vivants: list[dict], archives_ids: set[str], ctx: Contexte):
    """None si le constat est à déposer (rend alors l'id à écrire, sinon le chantier qui le couvre déjà)."""
    ids = {c["id"] for c in vivants if c.get("id")}
    i = constat.id
    couvrant = None
    m = re.match(r"arbitre-c9-checkpoint-(.+)-\d{8}$", i)
    if m:
        couvrant = next((c for c in vivants if c.get("id") and est_ouvert(c)
                         and re.fullmatch(rf"arbitre-c9-checkpoint-{re.escape(m.group(1))}-\d{{8}}", c["id"])), None)
    elif i.startswith("arbitre-c9-table-"):
        couvrant = next((c for c in vivants if c.get("id", "").startswith("arbitre-c9-table-") and est_ouvert(c)), None)
    elif i.startswith("arbitre-c10-checkpoint-court-"):
        couvrant = next((c for c in vivants if c.get("id") and est_ouvert(c) and c.get("pour") == constat.pour
                         and "checkpoint-court" in c["id"]), None)
    elif i.startswith("arbitre-c12-entrees-courtes-"):
        couvrant = next((c for c in vivants if c.get("id") and est_ouvert(c) and c.get("pour") == constat.pour
                         and "entrees-courtes" in c["id"]), None)
    if couvrant is not None:
        return None, couvrant
    if i in ids:
        return None, next(c for c in vivants if c.get("id") == i)
    if i in archives_ids:  # un id archivé ne se réutilise pas
        i = f"{i}-{ctx.stamp}"
        if i in ids or i in archives_ids:
            return None, next((c for c in vivants if c.get("id") == i), {"id": i, "pour": constat.pour})
    return i, None


# ───────────────────────────── l'écriture de chantiers.yaml ─────────────────────────────

def valeur_yaml(archiveur, verifier, valeur: str) -> str:
    valeur = " ".join(valeur.split())
    return valeur if verifier.valeur_conforme(valeur) else archiveur.entre_guillemets(valeur)


def entree_yaml(constat: Constat, id_ecrit: str, archiveur, verifier) -> str:
    def v(texte):
        return valeur_yaml(archiveur, verifier, texte)
    lignes = [f"- id: {v(id_ecrit)}",
              f"  titre: {v(constat.titre)}",
              f"  module: {v(constat.module)}",
              "  categorie: doc",
              "  statut: a-cadrer",
              f"  pour: {v(constat.pour)}",
              "  priorite: moyen",
              "  complexite: faible",
              f"  cout: {v('aucun ; une correction dans les vivants')}",
              f"  mesure: {v(constat.mesure)}",
              "  refs: Methode/ARBITRE.md"]
    return "\n".join(lignes) + "\n"


def ajouter_en_fin(chemin: Path, entrees: list[str]) -> None:
    """Les entrées en fin de fichier, séparées par une ligne vide ; aucune ligne existante n'est touchée."""
    texte = chemin.read_bytes().decode("utf-8")
    if texte and not texte.endswith("\n"):
        texte += "\n"
    if texte and not texte.endswith("\n\n"):
        texte += "\n"
    chemin.write_bytes((texte + "\n".join(entrees)).encode("utf-8"))


def deposer(constats: list[Constat], a, ctx: Contexte, archiveur, verifier, nouveaux: list, deja: list) -> None:
    """Dépose les constats qui ne sont pas déjà signalés ; nouveaux et deja : listes de (id, pour)."""
    chemin = Path(a.chantiers)
    vivants = verifier.lire_chantiers(chemin)
    archives_ids = {c["id"] for c in verifier.lire_archives(Path(a.archives)) if c.get("id")}
    entrees = []
    for constat in constats:
        id_ecrit, couvrant = deja_signale(constat, vivants, archives_ids, ctx)
        if id_ecrit is None:
            deja.append((couvrant.get("id", constat.id), couvrant.get("pour") or constat.pour))
            continue
        entrees.append(entree_yaml(constat, id_ecrit, archiveur, verifier))
        vivants.append({"id": id_ecrit, "statut": "a-cadrer", "pour": constat.pour})
        nouveaux.append((id_ecrit, constat.pour))
    if entrees:
        ajouter_en_fin(chemin, entrees)


# ───────────────────────────── les témoins et le retard ─────────────────────────────

def identifiant_temoin(texte: str) -> str | None:
    """L'identifiant de la ligne « Session en activité » ; None si la ligne dit « aucune », « sans objet » ou n'existe pas."""
    for ligne in texte.split("\n"):
        if RE_TEMOIN.match(ligne):
            m = RE_IDENTIFIANT.match(ligne)
            return m.group(1) if m else None
    return None


def instant_git(racine: Path, *arguments) -> datetime | None:
    code, sortie = git(racine, "log", "-1", "--format=%cI", *arguments)
    if code != 0 or not sortie:
        return None
    try:
        return datetime.fromisoformat(sortie)
    except ValueError:
        return None


@dataclass
class Temoin:
    domaine: str
    identifiant: str
    quand: datetime
    avec_commit: bool


def lire_temoins(ctx: Contexte, racine: Path, maintenant: datetime) -> list[Temoin]:
    """Les témoins silencieux depuis plus de 24 h ; la coordination est exclue.

    Le dernier commit qui porte l'identifiant (« git log --grep ») ; sans aucun, le dernier commit qui touche le
    checkpoint tient lieu de pose du témoin."""
    silencieux = []
    for d in ctx.valides:
        if "Coordination" in d.get("cdp", ""):
            continue
        try:
            texte = (racine / d["checkpoint"]).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        identifiant = identifiant_temoin(texte)
        if not identifiant:
            continue
        quand = instant_git(racine, "--fixed-strings", f"--grep={identifiant}", "HEAD")
        avec_commit = quand is not None
        if quand is None:
            quand = instant_git(racine, "HEAD", "--", d["checkpoint"])
        if quand is not None and maintenant - quand > SILENCE:
            silencieux.append(Temoin(d["domaine"], identifiant, quand, avec_commit))
    return silencieux


def texte_du_temoin(maintenant: datetime, silencieux: list[Temoin]) -> str:
    if not silencieux:
        return "témoins frais"
    t = min(silencieux, key=lambda s: s.quand)
    quand = t.quand.astimezone(maintenant.tzinfo).strftime("%Y-%m-%d %H:%M")
    precision = f"dernier commit le {quand}" if t.avec_commit else f"aucun commit, checkpoint touché le {quand}"
    return f"{t.domaine} ({t.identifiant}, {precision})"


def statuts_du_texte(verifier, texte: str) -> dict[str, str]:
    """Le statut de chaque entrée d'un chantiers.yaml, par id (même lecteur que le vérificateur)."""
    entrees: list[dict] = []
    for _, debut, cle, brut in verifier.analyser(texte):
        if debut:
            entrees.append({})
        if cle is not None:
            entrees[-1][cle] = verifier.lire_valeur(brut)
    return {e["id"]: e.get("statut", "") for e in entrees if e.get("id")}


def dates_d_acceptation(ctx: Contexte, racine: Path, chantiers: Path) -> dict[str, str]:
    """Par id, la date (%cs) du commit qui a fait passer l'entrée en recette ; sans preuve, l'id n'y est pas.

    Les entrées lues sont celles du domaine, en recette et sans « pour: ». La date est celle du plus ancien commit de
    chantiers.yaml d'où l'entrée est en recette sans interruption jusqu'à HEAD. Une seule lecture de l'historique :
    chaque version du fichier se lit une fois au plus, pour toutes les entrées, de la plus récente à la plus
    ancienne, et la lecture s'arrête quand chaque entrée est jugée. Sans preuve (entrée déjà en recette à la
    plus ancienne version lisible, fichier ou historique introuvable), l'id n'est pas rendu."""
    domaines = {d["domaine"] for d in ctx.valides}
    restantes = {c["id"] for c in ctx.chantiers
                 if c.get("id") and c.get("statut") == "recette" and "pour" not in c and ctx.domaine_de(c) in domaines}
    try:
        relatif = Path(chantiers).resolve().relative_to(Path(racine).resolve()).as_posix()
    except ValueError:
        return {}
    if not restantes:
        return {}
    code, sortie = git(racine, "log", "--topo-order", "--format=%H %cs", "--", relatif)
    commits = [ligne.split() for ligne in sortie.split("\n") if ligne.strip()]
    if code != 0 or not commits or any(len(c) != 2 or not RE_JOUR.fullmatch(c[1]) for c in commits):
        return {}

    def statuts_a(revision: str) -> dict[str, str] | None:
        code, texte = git(racine, "show", f"{revision}:./{relatif}", erreurs="replace")
        return statuts_du_texte(ctx.verifier, texte) if code == 0 else None

    depuis: dict[str, str] = {}     # id -> la date du plus ancien commit lu d'où l'entrée est en recette sans interruption
    preuves: dict[str, str] = {}
    for hachage, jour in commits:   # de la version la plus récente à la plus ancienne
        statuts = statuts_a(hachage)
        if statuts is None:         # une version illisible : rien de plus ne se prouve
            return preuves
        for i in list(restantes):
            if statuts.get(i) == "recette":
                depuis[i] = jour
            else:                   # la série s'arrête ici : la version plus récente est celle du passage en recette
                if i in depuis:
                    preuves[i] = depuis[i]
                restantes.discard(i)
        if not restantes:
            return preuves
    # il reste les entrées en recette jusqu'à la plus ancienne version qui touche le fichier : la version d'avant
    # (le parent) dit si elles y étaient déjà ; sans parent ni fichier, c'est l'origine de l'historique lisible
    parent = statuts_a(f"{commits[-1][0]}^")
    if parent is not None:
        for i in restantes:
            if parent.get(i) != "recette":
                preuves[i] = depuis[i]
    return preuves


def lire_retards(ctx: Contexte, racine: Path, chantiers: Path) -> dict[str, list[str]]:
    """Par domaine, les chantiers en recette dont la date d'acceptation suit le dernier commit du checkpoint.

    La date d'acceptation est celle du commit qui a fait passer l'entrée en recette (dates_d_acceptation), pas
    « recette-le: » que l'arbitre pose lui-même ; sans preuve dans l'historique, aucune ligne."""
    retards: dict[str, list[str]] = {}
    acceptations = dates_d_acceptation(ctx, racine, chantiers)
    for d in ctx.valides:
        code, sortie = git(racine, "log", "-1", "--format=%cs", "--", d["checkpoint"])
        if code != 0 or not RE_JOUR.fullmatch(sortie):
            continue
        for c in ctx.chantiers:
            acceptee = acceptations.get(c.get("id", ""))
            if (acceptee is None or c.get("statut") != "recette" or "pour" in c
                    or ctx.domaine_de(c) != d["domaine"]):
                continue
            try:
                posterieur = date.fromisoformat(acceptee) > date.fromisoformat(sortie)
            except ValueError:
                continue
            if posterieur:
                retards.setdefault(d["domaine"], []).append(
                    f"{d['domaine']} : {c['id']} est en recette depuis le {acceptee}, "
                    f"le checkpoint n'a pas été touché depuis le {sortie}")
    return retards


# ───────────────────────────── les scripts appelés ─────────────────────────────

def normaliser(a) -> int:
    processus = lancer(ICI / "archiver_chantiers.py", "normaliser", "--chantiers", a.chantiers,
                       "--archives", a.archives, "--domaines", a.domaines)
    if processus.returncode not in (0, 1):
        raise Impossible("archiver_chantiers.py", f"archiver_chantiers.py normaliser a échoué (code "
                                                  f"{processus.returncode}) : {derniere_ligne(processus)}")
    m = re.search(r"normaliser · (\d+) valeur", processus.stdout)
    return int(m.group(1)) if m else 0


@dataclass
class Archivage:
    dates: int = 0
    archives: int = 0
    avertissements: list = field(default_factory=list)
    erreur: str = ""


def archiver(a, jour: date) -> Archivage:
    processus = lancer(ICI / "archiver_chantiers.py", "archiver", "--chantiers", a.chantiers,
                       "--archives", a.archives, "--date", jour.isoformat())
    resultat = Archivage()
    if processus.returncode not in (0, 1):
        resultat.erreur = f"{derniere_ligne(processus)}"
        return resultat
    m = re.search(r"archiver · (\d+) daté\(s\), (\d+) dédaté\(s\), (\d+) archivé\(s\)", processus.stdout)
    if m:
        resultat.dates, resultat.archives = int(m.group(1)), int(m.group(3))
    resultat.avertissements = [ligne for ligne in processus.stdout.split("\n") if ligne.startswith("id ")]
    return resultat


def regenerer_tableau(a) -> None:
    processus = lancer(Path(a.generateur), Path(a.chantiers).resolve(), Path(a.tableau).resolve())
    if processus.returncode != 0:
        raise Impossible(a.generateur, f"le générateur a échoué (code {processus.returncode}) : "
                                       f"{derniere_ligne(processus)}")


def constats_archivage(archivage: Archivage, ctx: Contexte, jour: date) -> list[Constat]:
    constats = []
    for ligne in archivage.avertissements:
        m = re.match(r"id (\S+) : ", ligne)
        i = m.group(1) if m else cle_sure(ligne[:40])
        constats.append(Constat(
            id=f"arbitre-ca-archivage-{cle_sure(i)}", titre=f"Archivage : {ligne}", module=ctx.module_de(ctx.par_id.get(i)),
            pour=ctx.coordinateur,
            mesure=(f"Signalé par l'arbitre le {date_longue(jour)} (archivage). {ligne}. "
                    "Faire corriger la date recette-le: (AAAA-MM-JJ) par son propriétaire : l'arbitre ne la corrige pas.")))
    return constats


# ───────────────────────────── le journal et la sortie ─────────────────────────────

def pluriel(n: int, singulier: str, pluriel_: str) -> str:
    return f"{n} {singulier if n < 2 else pluriel_}"


def socle_ko(a, ctx: Contexte, racine: Path) -> int:
    """La somme des tailles de la méthode, de la fiche et de tous les checkpoints de la table, en Ko (1 Ko = 1024 octets)."""
    fichiers = {}
    for option in (a.methode, a.fiche):
        if option:
            fichiers[Path(option).resolve()] = Path(option)
    for d in ctx.table:
        if d.get("checkpoint"):
            fichiers[(racine / d["checkpoint"]).resolve()] = racine / d["checkpoint"]
    total = sum(chemin.stat().st_size for chemin in fichiers.values() if chemin.is_file())
    return int(total / 1024 + 0.5)


def ajouter_au_journal(chemin: Path, ligne: str) -> None:
    texte = chemin.read_bytes().decode("utf-8")
    if texte and not texte.endswith("\n"):
        texte += "\n"
    chemin.write_bytes((texte + ligne + "\n").encode("utf-8"))


def message_commit(jour: date, constats: int, ecarts: int, archivage: Archivage, normalisees: int) -> str:
    base = f"{constats} constat(s)" if constats or ecarts else "vivants conformes"
    suite = []
    if base == "vivants conformes" and archivage.dates:
        suite.append(f"{archivage.dates} daté(s)")
    if archivage.archives:
        suite.append(f"{archivage.archives} archivé(s)")
    if normalisees:
        suite.append(f"{normalisees} valeur(s) normalisée(s)")
    return f"Arbitre {jour.isoformat()} : " + ", ".join([base] + suite)


def verifier_prealables(a, racine: Path) -> None:
    """Un fichier qui manque est un code 2, avant toute écriture."""
    for option in OPTIONS_FICHIERS:
        chemin = getattr(a, option)
        if chemin and not Path(chemin).is_file():
            raise Impossible(chemin, f"fichier introuvable : {chemin}")
    for option in ("archives", "racine"):
        chemin = getattr(a, option)
        if chemin and not Path(chemin).is_dir():
            raise Impossible(chemin, f"dossier introuvable : {chemin}")
    for script in ("verifier_vivants.py", "archiver_chantiers.py"):
        if not (ICI / script).is_file():
            raise Impossible(script, f"script introuvable : {ICI / script}")
    code, _ = git(racine, "rev-parse", "--git-dir")
    if code != 0:
        raise Impossible("dépôt git", f"{racine} n'est pas un dépôt git")


def passage(a, maintenant: datetime) -> int:
    racine = Path(a.racine) if a.racine else Path(".")
    jour = maintenant.date()
    verifier_prealables(a, racine)
    verifier, archiveur = charger("verifier_vivants.py"), charger("archiver_chantiers.py")
    table = verifier.lire_chantiers(Path(a.domaines))
    ctx = Contexte(verifier, [], [], table, a.domaines)  # le coordinateur d'abord : sans lui, rien n'est écrit
    ctx.stamp = jour.strftime("%Y%m%d")
    chantiers_avant = Path(a.chantiers).read_bytes()

    normalisees = normaliser(a)                                  # 1
    controle = controler(a)                                      # 2
    ctx.chantiers = verifier.lire_chantiers(Path(a.chantiers))
    ctx.archives = verifier.lire_archives(Path(a.archives))
    ctx.par_id = {c["id"]: c for c in ctx.chantiers if c.get("id")}
    silencieux = lire_temoins(ctx, racine, maintenant)           # 4
    retards = lire_retards(ctx, racine, Path(a.chantiers))                          # 5
    nouveaux, deja = [], []
    constats_9, signales = constats_checkpoints(controle, retards, ctx, jour)
    constats = constats_ordinaires(controle, ctx, jour) + constats_9 + constats_entrees(controle, ctx, jour)
    deposer(constats, a, ctx, archiveur, verifier, nouveaux, deja)  # 3
    archivage = archiver(a, jour)                                # 6
    if archivage.avertissements:
        ctx.chantiers = verifier.lire_chantiers(Path(a.chantiers))
        ctx.par_id = {c["id"]: c for c in ctx.chantiers if c.get("id")}
        deposer(constats_archivage(archivage, ctx, jour), a, ctx, archiveur, verifier, nouveaux, deja)
    final = controle
    if Path(a.chantiers).read_bytes() != chantiers_avant:        # 7
        if a.tableau:
            regenerer_tableau(a)
        final = controler(a)
    ecarts = final.ecarts() + (1 if retards else 0)

    temoin = texte_du_temoin(maintenant, silencieux)
    checkpoints = ", ".join(signales) if signales else "à jour"
    if archivage.erreur:
        archive_texte = f"archivage : impossible, {archivage.erreur}"
    else:
        archive_texte = f"archivage : {archivage.dates} daté(s), {archivage.archives} archivé(s)"
    ko = socle_ko(a, ctx, racine)
    ligne = " · ".join([maintenant.strftime("%Y-%m-%d %H:%M"), pluriel(ecarts, "écart", "écarts"),
                        f"{len(nouveaux)} constat{'s' if len(nouveaux) > 1 else ''} nouveau"
                        f"{'x' if len(nouveaux) > 1 else ''}",
                        temoin, archive_texte, f"checkpoints : {checkpoints}", f"socle : {ko} Ko"])
    ajouter_au_journal(Path(a.journal_arbitre), "- " + ligne)    # 8

    commit = message_commit(jour, len(nouveaux), ecarts, archivage, normalisees)
    resume(jour, final, ecarts, nouveaux, deja, temoin, archive_texte, checkpoints, ko, commit, archivage.erreur,
           list(retards))  # 9
    if archivage.erreur:
        print(f"archivage impossible : {archivage.erreur}", file=sys.stderr)
        return 2
    return 1 if nouveaux else 0


def resume(jour: date, final: Controle, ecarts: int, nouveaux: list, deja: list, temoin: str, archive_texte: str,
           checkpoints: str, ko: int, commit: str, erreur: str, retards: list) -> None:
    if not ecarts and not nouveaux and not erreur:
        print(f"Vivants conformes au {jour.isoformat()}")
    else:
        print(f"Arbitre des vivants au {jour.isoformat()} · {pluriel(ecarts, 'écart', 'écarts')}")
        if final.bilan:
            print(f"Contrôle · {final.bilan}")
        if retards:
            print(f"Checkpoint en retard · {', '.join(retards)}")
        print(f"Constats nouveaux ({len(nouveaux)}) :")
        for i, pour in nouveaux:
            print(f"  - {i} · pour {pour}")
        print(f"Déjà signalés et toujours là ({len(deja)}) :")
        for i, pour in deja:
            print(f"  - {i} · pour {pour}")
    print(f"Témoins · {temoin}")
    print(f"Archivage · {archive_texte.removeprefix('archivage : ')}")
    print(f"Checkpoints · {checkpoints}")
    print(f"Socle · {ko} Ko")
    print(f"Commit : {commit}")


def echec(a, maintenant: datetime, erreur: Impossible) -> int:
    """Un code 2 : le journal dit « contrôle impossible », rien d'autre n'est écrit."""
    print(f"arbitre : {erreur.detail}", file=sys.stderr)
    journal = Path(a.journal_arbitre)
    if journal.is_file():
        ajouter_au_journal(journal, f"- {maintenant.strftime('%Y-%m-%d %H:%M')} · contrôle impossible : {erreur.fichier}")
        print(f"Contrôle impossible : {erreur.fichier}")
        print(f"Commit : Arbitre {maintenant.date().isoformat()} : contrôle impossible")
    return 2


def main(argv: list[str]) -> int:
    try:
        a = lire_arguments(argv)
        maintenant = lire_date(a.date)
    except ValueError as erreur:
        print(f"arbitre : {' '.join(str(erreur).split())}", file=sys.stderr)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        return passage(a, maintenant)
    except Impossible as erreur:
        return echec(a, maintenant, erreur)
    except (OSError, UnicodeDecodeError) as erreur:
        return echec(a, maintenant, Impossible(getattr(erreur, "filename", None) or "arbitre.py", str(erreur)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
