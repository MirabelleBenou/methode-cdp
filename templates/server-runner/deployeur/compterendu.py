"""Le compte rendu d'un ordre : un fichier Markdown en français, première ligne ``Statut : …``."""

import datetime
import json

from . import __version__
from .filtre import filtrer

REUSSI = "réussi"
REFUSE = "refusé"
ECHEC_REVENU = "échec, revenu"
ECHEC_ARRET = "échec, file arrêtée"
INTERROMPU = "interrompu"
EN_COURS = "en cours"

STATUTS = (REUSSI, REFUSE, ECHEC_REVENU, ECHEC_ARRET, INTERROMPU, EN_COURS)


def maintenant():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def horodatage(dt=None):
    return (dt or maintenant()).strftime("%Y-%m-%dT%H:%M:%SZ")


class Compte:
    def __init__(self, stem, ordre_texte):
        self.stem = stem
        self.ordre_texte = ordre_texte
        self.statut = EN_COURS
        self.debut = horodatage()
        self.fin = None
        self.sections = []      # [(titre, [lignes])]
        self.a_decider = []
        self.journal_app = []   # lignes du journal de l'application (filtrées au rendu)
        self.deroulement = []

    # -- construction ----------------------------------------------------------------------------
    def section(self, titre):
        for t, lignes in self.sections:
            if t == titre:
                return lignes
        lignes = []
        self.sections.append((titre, lignes))
        return lignes

    def ligne(self, titre, texte):
        self.section(titre).append(texte)

    def etape(self, texte):
        self.deroulement.append("%s %s" % (horodatage(), texte))

    def decider(self, texte):
        self.a_decider.append(texte)

    def terminer(self, statut):
        self.statut = statut
        self.fin = horodatage()

    # -- rendu -----------------------------------------------------------------------------------
    def rendre(self):
        out = ["Statut : %s" % self.statut, "", "# Compte rendu de l'ordre %s" % self.stem, "", "## Ordre", "",
               "```json", self._ordre_recopie(), "```", "",
               "- début : %s" % self.debut,
               "- fin : %s" % (self.fin or "—"),
               "- version du déployeur : %s" % __version__, ""]
        for titre, lignes in self.sections:
            out.append("## %s" % titre)
            out.append("")
            out.extend(lignes)
            out.append("")
        if self.a_decider:
            out.append("## Ce que l'exploitant doit décider")
            out.append("")
            out.extend("- %s" % t for t in self.a_decider)
            out.append("")
        if self.deroulement:
            out.append("## Déroulement")
            out.append("")
            out.extend("- %s" % t for t in self.deroulement)
            out.append("")
        if self.journal_app:
            out.append("## Journal de l'application (50 dernières lignes utiles, filtrées)")
            out.append("")
            out.append("```")
            out.extend(filtrer(l) for l in self.journal_app[-50:])
            out.append("```")
            out.append("")
        return "\n".join(out).rstrip("\n") + "\n"

    def _ordre_recopie(self):
        try:
            return json.dumps(json.loads(self.ordre_texte), ensure_ascii=False, indent=2)
        except ValueError:
            return self.ordre_texte[:4000]


def lignes_utiles(texte, n=50):
    """Les ``n`` dernières lignes non vides d'un journal."""
    lignes = [l.rstrip() for l in (texte or "").splitlines() if l.strip()]
    return lignes[-n:]


def taille(octets):
    """Taille lisible."""
    n = float(octets)
    for unite in ("o", "Kio", "Mio", "Gio", "Tio"):
        if n < 1024 or unite == "Tio":
            return ("%d %s" % (n, unite)) if unite == "o" else ("%.1f %s" % (n, unite))
        n /= 1024.0
    return "%d o" % octets
