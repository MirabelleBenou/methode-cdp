"""L'état du déployeur sur la machine : journal des ordres joués, files arrêtées, commit servi, verrous.

Tout vit sous le répertoire d'état de la configuration (700, propriétaire root).
"""

import fcntl
import os

from . import ecriture

FILES = ("deploiement", "fichiers")

NB_ARCHIVES_GARDEES = 5


class Registre:
    def __init__(self, repertoire):
        self.rep = repertoire

    # -- chemins ---------------------------------------------------------------------------------
    def chemin(self, *morceaux):
        return os.path.join(self.rep, *morceaux)

    def preparer(self):
        os.makedirs(self.rep, mode=0o700, exist_ok=True)
        for sous in ("archives", "manifestes", "travail"):
            os.makedirs(self.chemin(sous), mode=0o700, exist_ok=True)

    # -- verrou ----------------------------------------------------------------------------------
    def verrou(self, file):
        return Verrou(self.chemin("verrou-" + file))

    # -- journal des ordres ----------------------------------------------------------------------
    def _chemin_journal(self, file):
        return self.chemin("journal-%s.json" % file)

    def journal(self, file):
        return ecriture.lire_json(self._chemin_journal(file), {"ordres": {}}).get("ordres", {})

    def marquer(self, file, ordre_id, statut, **champs):
        j = ecriture.lire_json(self._chemin_journal(file), {"ordres": {}})
        entree = j["ordres"].get(ordre_id, {})
        entree.update(champs)
        entree["statut"] = statut
        j["ordres"][ordre_id] = entree
        ecriture.ecrire_json(self._chemin_journal(file), j)

    # -- files arrêtées --------------------------------------------------------------------------
    def arret(self, file):
        return ecriture.lire_json(self.chemin("arret-%s.json" % file))

    def arreter(self, file, ordre_id, raison, date):
        ecriture.ecrire_json(self.chemin("arret-%s.json" % file), {"ordre": ordre_id, "raison": raison, "date": date})

    def rouvrir(self, file):
        try:
            os.remove(self.chemin("arret-%s.json" % file))
        except FileNotFoundError:
            pass

    # -- l'application servie --------------------------------------------------------------------
    def application(self):
        return ecriture.lire_json(self.chemin("application.json"), {"servi": None, "precedent": None, "historique": []})

    def enregistrer_application(self, etat):
        ecriture.ecrire_json(self.chemin("application.json"), etat)

    def chemin_archive(self, commit):
        return self.chemin("archives", commit + ".tar")

    def chemin_manifeste(self, commit):
        return self.chemin("manifestes", commit + ".json")

    def manifeste(self, commit):
        d = ecriture.lire_json(self.chemin_manifeste(commit))
        return None if d is None else d.get("fichiers", {})

    def travail(self, ordre_id):
        d = self.chemin("travail", ordre_id)
        os.makedirs(d, mode=0o700, exist_ok=True)
        return d

    def garder_archives(self, etat):
        """Garde les cinq derniers commits servis (et jamais le servi ni le précédent) ; le reste est retiré."""
        garder = list(etat.get("historique", []))[:NB_ARCHIVES_GARDEES]
        for cle in ("servi", "precedent"):
            if etat.get(cle) and etat[cle]["commit"] not in garder:
                garder.append(etat[cle]["commit"])
        for sous, ext in (("archives", ".tar"), ("manifestes", ".json")):
            try:
                noms = os.listdir(self.chemin(sous))
            except FileNotFoundError:
                continue
            for nom in noms:
                if nom.endswith(ext) and nom[:-len(ext)] not in garder:
                    try:
                        os.remove(self.chemin(sous, nom))
                    except OSError:
                        pass


class Verrou:
    """Verrou exclusif non bloquant sur un fichier (flock) : un second passage sort sans rien faire."""

    def __init__(self, chemin):
        self.chemin = chemin
        self.fd = None

    def __enter__(self):
        os.makedirs(os.path.dirname(self.chemin), mode=0o700, exist_ok=True)
        self.fd = os.open(self.chemin, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self.fd)
            self.fd = None
        return self

    @property
    def pris(self):
        return self.fd is not None

    def __exit__(self, *exc):
        if self.fd is not None:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
            finally:
                os.close(self.fd)
                self.fd = None
        return False
