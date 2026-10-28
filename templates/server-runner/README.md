# Exécutant serveur — implémentation de référence (« déployeur »)

Un programme déterministe, lancé par systemd chaque minute sur le serveur de production, qui lit les ordres d'un dépôt
Git privé (le dépôt d'ordres), n'exécute qu'une liste blanche d'actions (déployer l'application ou une suite de fichiers
statiques, revenir, état, opérations de fichiers dans des zones déclarées) et y pousse son compte rendu. Aucune IA dans
le chemin du déploiement ; aucune connexion entrante.

C'est l'implémentation de référence du guide `EXECUTANT_SERVEUR.md` du package méthode : à lire d'abord. Le code, les
identifiants et la documentation sont en français. Toutes les valeurs propres à une installation (projet Compose,
dossiers, dépôts, suites, zones, hôtes, tables comptées, compte propriétaire) sont des **valeurs d'exemple**, réunies dans
le bloc « Valeurs de ce projet » en tête de `installer.sh` : à remplacer par les vôtres avant le premier lancement.

- **Python 3.11 ou plus récent, bibliothèque standard seule.** Un seul module (`deployeur/commandes.py`) lance des
  processus, avec une liste blanche de commandes Docker et Git ; aucun interpréteur de commandes.
- **La base ne se perd jamais** : projet et volumes vérifiés avant tout geste, sauvegarde relue avant chaque déploiement,
  comptes des tables d'histoire avant et après, aucun retour automatique après une migration, aucune restauration par le
  déployeur.
- **Deux files** (`deploiement`, `fichiers`), chacune son minuteur et son verrou.
- **Opérations de fichiers enfermées dans des zones** déclarées sur le serveur : rien ne s'efface (corbeille), rien ne
  s'exécute.

L'application visée est servie par Docker Compose, avec une base PostgreSQL (service `db`) et une route de santé qui
répond `{"version": "…"}` ; les suites sont des fichiers HTML autoportants tirés de dépôts publics. Une autre pile
demande d'adapter `deployeur/application.py`, `deployeur/base.py` et `deployeur/commandes.py`.

## Installation

Voir [`docs/INSTALLATION.md`](docs/INSTALLATION.md) : déposer l'archive sur le serveur, `sudo sh installer.sh`, coller
les deux clés publiques en clés de déploiement GitHub. L'installateur ne touche ni au pare-feu, ni à SSH, ni au dossier
Compose, ni à Docker.

## Ordres et comptes rendus

Voir [`docs/ORDRES.md`](docs/ORDRES.md) : le format de chaque action, un exemple de chacune, le format des comptes rendus.

## Tests

```
python3 -m unittest discover -s tests
```

Sans réseau, sous Python 3.12 et 3.13 : un faux `docker`, un faux transport HTTPS, des dépôts Git locaux. Les tests de
l'installateur demandent root et `ssh-keygen` (sinon ils sont sautés).
