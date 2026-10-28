"""Le contexte d'un passage : configuration, état, journal, horloge et accès Git."""

import sys
import time

from . import commandes, compterendu


class Refus(Exception):
    """L'ordre est refusé : rien n'a bougé (ou ce qui a bougé est dit au compte rendu)."""


class Contexte:
    def __init__(self, cfg, registre, file, sortie=None, dormir=time.sleep, monotone=time.monotonic):
        self.cfg = cfg
        self.registre = registre
        self.file = file
        self._sortie = sortie
        self.dormir = dormir
        self.monotone = monotone
        self.battement = None   # fonction appelée dans les longues boucles (compte rendu « en cours »)

    def log(self, message):
        """Une ligne au journal systemd (sortie standard)."""
        ligne = "%s [%s] %s" % (compterendu.horodatage(), self.file, message)
        if self._sortie is not None:
            self._sortie(ligne)
        else:
            sys.stdout.write(ligne + "\n")
            sys.stdout.flush()

    def maintenant(self):
        return compterendu.maintenant()

    def acces_ordres(self):
        g = self.cfg.git
        return commandes.GitAcces(g.cle_ordres, g.known_hosts)

    def acces_application(self):
        g = self.cfg.git
        return commandes.GitAcces(g.cle_application, g.known_hosts)

    def tick(self):
        if self.battement:
            self.battement()
