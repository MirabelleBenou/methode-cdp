"""python3 -m deployeur --file deploiement|fichiers [--config CHEMIN]   |   --verifier [--config CHEMIN]"""

import argparse
import sys

from . import __version__, config, passage


def main(argv=None):
    p = argparse.ArgumentParser(prog="deployeur", description="Déployeur : lit des ordres, joue une liste blanche d'actions.")
    p.add_argument("--file", choices=("deploiement", "fichiers"), help="la file à passer")
    p.add_argument("--config", default=config.CHEMIN_DEFAUT, help="fichier de configuration (défaut : %(default)s)")
    p.add_argument("--verifier", action="store_true", help="valide la configuration et sort")
    p.add_argument("--version", action="version", version="deployeur " + __version__)
    args = p.parse_args(argv)
    if not args.verifier and not args.file:
        p.error("--file est obligatoire (sauf avec --verifier)")
    try:
        cfg = config.charger(args.config)
    except config.ErreurConfig as e:
        sys.stderr.write("deployeur : %s\n" % e)
        sys.stderr.write("deployeur : configuration invalide, aucun passage\n")
        return 2
    if args.verifier:
        sys.stdout.write("configuration valide\n")
        return 0
    return passage.executer(cfg, args.file)


if __name__ == "__main__":
    sys.exit(main())
