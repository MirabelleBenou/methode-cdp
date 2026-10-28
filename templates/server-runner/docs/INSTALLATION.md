# Installation du déployeur — les gestes de l'exploitant

Ce document dit, dans l'ordre, ce que fait l'exploitant. L'installateur (`installer.sh`) fait tout le reste ; il est
**idempotent** : on peut le relancer sans rien casser. Il **ne touche ni au pare-feu, ni à SSH (`sshd_config`), ni au dossier
Compose, ni à Docker.** Il n'ouvre aucune connexion entrante : le déployeur ne se connecte qu'en sortie (Git, HTTPS).

## 0 · Ce qu'il faut avant

Sur la machine : Debian, `python3` 3.11 ou plus récent, `git`, `docker compose`, `systemctl`, `flock`, `ssh-keygen`,
`ssh-keyscan`. Si `rsync` manque, l'installateur l'installe (`apt-get install -y rsync`, sa seule action apt) puis vérifie que
`/usr/bin/rrsync` est présent. Les valeurs propres à l'installation (projet, dossiers, dépôts, zones…) sont dans le bloc
« Valeurs de ce projet » en tête de `installer.sh`, qui écrit la configuration au premier passage.

## 1 · Les gestes, dans l'ordre

1. **Déposer l'archive sur le serveur** (par le gestionnaire de fichiers, `scp`, ou tout autre moyen) et la décompresser
   dans un dossier de travail. Le dossier doit contenir `installer.sh`, `deployeur/`, `systemd/`, `VERSION` et `docs/`.
2. **Lancer l'installateur, en root, depuis ce dossier** :
   ```
   sudo sh installer.sh
   ```
   Il affiche chaque étape. Il copie le programme dans un dossier neuf de `/opt/deployeur/`, pointe `/opt/deployeur/courant` dessus,
   écrit `/etc/deployeur/config.json` **seulement s'il n'existe pas**, valide la configuration (il s'arrête si elle est
   invalide, par exemple si une zone est interdite), génère deux clés SSH ed25519 sans phrase de passe **seulement si
   elles sont absentes**, contrôle l'empreinte de `github.com` avant d'écrire `known_hosts`, crée les zones qui manquent (au compte propriétaire des zones, déclaré dans le bloc « Valeurs de ce projet », qui doit
   exister : sinon il s'arrête) et leur corbeille,
   le compte de transfert et ses dossiers, installe les quatre unités systemd et active les deux minuteurs.
3. **Coller les deux clés publiques en clés de déploiement GitHub.** À la fin, l'installateur affiche les deux clés publiques
   avec la consigne. Pour chacune : sur GitHub, ouvrir le dépôt concerné, puis **Settings → Deploy keys → Add deploy key**,
   donner un titre, coller la clé.
   - clé `cle_ordres` : dépôt d'ordres, **cocher « Allow write access »** (le déployeur y pousse ses comptes rendus) ;
   - clé `cle_app` : dépôt de l'application, **ne pas cocher « Allow write access »** (lecture seule).
4. **Rien d'autre.** Dans la minute qui suit, le premier passage trouve le dépôt d'ordres et attend les ordres.

Pour relire les clés publiques plus tard : `cat /etc/deployeur/cle_ordres.pub /etc/deployeur/cle_app.pub`.

### Option : autoriser le PC à déposer des fichiers

Sur le PC, afficher la clé publique SSH (une ligne `ssh-ed25519 AAAA… commentaire`), puis sur la machine :

```
sudo sh installer.sh --cle-transfert "ssh-ed25519 AAAA… commentaire"
```

La clé est ajoutée au compte `transfert` avec `restrict,command="/usr/bin/rrsync -wo -no-del <dossier entree/>"` : elle ne
permet que `rsync` en écriture seule dans `entree/` de la zone de transfert, sans suppression, et rien d'autre (ni shell,
ni redirection de port). Une ligne déjà présente n'est pas doublée. Exemple de dépôt depuis le PC :

```
rsync -av ./monfichier.zip transfert@<machine>:
```

(`rrsync` fixe le dossier de destination ; le chemin côté serveur est celui de `entree/`.)

## 2 · L'essai à blanc

Après l'installation, l'essai à blanc prouve la chaîne complète **sans rien changer** : le commit d'essai est celui qui est
déjà servi, aucun commit n'est créé. Chaque ordre est un fichier `ordres/<id>.json` du dépôt d'ordres ; le compte rendu
arrive dans `resultats/<id>.md` dans la minute (voir `ORDRES.md` pour le format).

1. **`etat`** : constater l'état. Vérifier la version servie, les contrôles du projet (« conforme »), les comptes des
   tables, la place libre, les sauvegardes existantes, les deux files « en marche ».
2. **`adopter`** avec le commit actuellement servi : tous les fichiers du dossier doivent être identiques à l'archive du
   commit (sinon le compte rendu liste les écarts et rien n'est retenu). Après `réussi`, le déployeur connaît le commit servi.
3. **`deployer-application`** du **même commit et de la même version**, avec un `go` : comptes identiques avant et après,
   sauvegarde présente dans `backups/` (`…_deploiement-<révision>_<horodatage>.dump` et `…_ecussons.tar.gz`) et relue,
   application recréée, santé bonne, statut `réussi`.
4. **`revenir`** avec `"cible": "application"` et un `go` : retour au commit « précédent », qui est ici le même ; le chemin
   complet (sauvegarde, build, recréation, santé) est rejoué sans changement.
5. **Une suite en aller-retour** : `deployer-suite` du fichier actuellement servi (même commit que le fichier, sha256 du fichier
   servi), puis `revenir` avec la suite en cible. Le fichier précédent (`<nom>.prec<extension>`) est créé puis échangé.
6. **Quelques opérations de fichiers** : `creer-dossier`, `lister`, `mettre-a-la-corbeille` (un dossier d'essai), dans une zone.

Le **retour automatique** après un échec de santé sans migration ne s'essaie pas sur la machine : un ordre dont la version ne
correspond pas au fichier `VERSION` de l'archive est refusé dès les préconditions, avant tout geste. Ce chemin est prouvé
par les tests (`tests/test_deploiement.py`) sur des doublures de Docker.

## 3 · La configuration, clé par clé

Fichier `/etc/deployeur/config.json` (600, root), validé à chaque démarrage : le programme refuse de tourner sur une
configuration invalide et le dit au journal. Contrôle manuel : `cd /opt/deployeur/courant && python3 -m deployeur --verifier`.
Un exemple neutre est fourni : `config.exemple.json`.

| clé | rôle |
|---|---|
| `repertoire_etat` | état du déployeur (défaut `/var/lib/deployeur`, 700) : journaux, miroir de l'application, copies du dépôt d'ordres, archives |
| `git.cle_ordres`, `git.cle_application` | clés privées SSH (chemins absolus) du dépôt d'ordres et du dépôt de l'application |
| `git.known_hosts` | fichier `known_hosts` utilisé (`StrictHostKeyChecking=yes`) |
| `git.identite_nom`, `git.identite_courriel` | identité Git des comptes rendus |
| `depot_ordres.url`, `depot_ordres.branche` | dépôt d'ordres (SSH, `file://` en essai) et sa branche (`main`) |
| `application.projet` | nom du projet Compose |
| `application.dossier` | dossier Compose (chemin absolu) |
| `application.fichier_compose` | fichier Compose, dans ce dossier (défaut `docker-compose.yml`) |
| `application.service_app`, `application.service_db` | services Compose : l'application (seule recréée) et la base (jamais touchée) |
| `application.conteneur_db` | nom du conteneur de la base (lecture, sauvegarde) |
| `application.volume_base`, `application.montage_base` | volume de la base et son point de montage dans le conteneur |
| `application.volume_ecussons`, `application.volume_depots_bruts` | les deux autres volumes irremplaçables |
| `application.prefixe_sauvegarde` | préfixe des sauvegardes du déployeur, `<préfixe>_deploiement-…` |
| `application.url_sante` | URL qui répond `{"version": "…"}` sans session |
| `application.depot_url` | dépôt de l'application (SSH), cloné en miroir dans l'état |
| `application.tables_histoire` | tables dont le nombre de lignes ne doit jamais baisser |
| `application.chemins_proteges` | chemins protégés **en plus** de `.env` et `backups/` (relatifs) |
| `application.place_min_deploiement_go` | place libre minimale (Go) du dossier Compose pour déployer |
| `application.sauvegardes_garder` | sauvegardes du déployeur gardées (défaut 10 ; une valeur inférieure à 3 vaut 3) |
| `application.delai_sante_s` | délai maximal de la santé après le démarrage (défaut 180 s) |
| `application.intervalle_sante_s` | intervalle entre deux essais de santé (défaut 5 s) |
| `suites.<nom>` | une suite : `depot` (`propriétaire/dépôt` public), `chemin` du fichier dans le dépôt, `dossier` servi, `fichier` servi |
| `hote_fichiers_bruts` | hôte des fichiers bruts du dépôt (défaut `raw.githubusercontent.com`) |
| `zones.<nom>` | une zone : `chemin` absolu et `place_min_go` (place libre minimale, Go, pour écrire) |
| `zone_transfert` | la zone qui reçoit `entree/` (dépôt de fichiers depuis le PC) |
| `depots_publics` | dépôts (`propriétaire/dépôt`) autorisés comme sources de `telecharger` |
| `hotes_autorises` | hôtes HTTPS autorisés comme sources de `telecharger` |
| `intervalle_en_cours_s` | intervalle des comptes rendus « en cours » d'une opération longue (défaut 300 s) |

Une zone ne peut pas contenir, ni être contenue dans : le dossier Compose, `/var/lib/docker`, `/etc`, `/var/lib/deployeur`,
`/etc/deployeur`, le dossier d'une suite, `/home`, `/root`, `/usr`, `/boot` ; elle ne peut pas être `/`. Deux zones peuvent être
imbriquées.

## 4 · Ce que l'installateur pose sur la machine

| chemin | contenu |
|---|---|
| `/opt/deployeur/<version>/` (ou `<version>.nouveau/`), `/opt/deployeur/courant` | le programme et le lien vers la version courante |
| `/etc/deployeur/` (700) | `config.json` (600), `cle_ordres`, `cle_app` (600), `known_hosts` |
| `/var/lib/deployeur/` (700) | état : `journal-<file>.json`, `application.json`, `arret-<file>.json`, `archives/`, `manifestes/`, `miroir-application/`, `ordres-<file>/`, `resultats-<file>/`, `verrou-<file>` |
| `/etc/systemd/system/deployeur-*.service` et `.timer` | quatre unités ; services `Type=oneshot` ; minuteurs `OnBootSec=2min`, `OnUnitActiveSec=1min` ; délai de 30 min pour `deploiement`, aucun pour `fichiers` |
| les zones et `<zone>/_corbeille/` | créés s'ils manquent ; une zone qui existe déjà n'est pas touchée |
| `<zone de transfert>/entree/` | propriétaire : le compte propriétaire des zones ; groupe `transfert` ; mode 2775 |
| compte `transfert` | utilisateur système, mot de passe verrouillé, `~/.ssh/authorized_keys` (700/600) |

## 5 · Dépannage

- **Voir ce que fait le déployeur** : `journalctl -u deployeur-deploiement.service -n 100` et
  `journalctl -u deployeur-fichiers.service -n 100` ; `systemctl list-timers 'deployeur-*'`.
- **« configuration invalide »** : le message liste chaque problème. Corriger `/etc/deployeur/config.json`, puis
  `python3 -m deployeur --verifier` depuis `/opt/deployeur/courant`.
- **Un ordre n'est pas joué** : le nom du fichier doit être `<id>.json` avec `id` identique dans le fichier ; l'ordre doit être
  poussé sur la branche `main` du dépôt d'ordres ; la clé `cle_ordres` doit être déclarée sur ce dépôt **avec** l'écriture ;
  `journalctl` dit « dépôt d'ordres inaccessible » si la clé ou le réseau manque.
- **Un compte rendu n'apparaît pas** : si le push échoue, le compte rendu est conservé sur la machine et poussé de nouveau au
  passage suivant ; la suite des ordres n'est pas retardée.
- **« verrou pris »** : un autre passage de la même file est en cours (une opération longue). Rien à faire.
- **File arrêtée** : le compte rendu de l'ordre fautif dit pourquoi et ce qu'il faut décider ; l'ordre `etat` montre l'ordre
  qui a arrêté la file ; `reprendre-file` (avec un `go`) la rouvre. **Le déployeur ne restaure jamais la base** : le compte
  rendu nomme la sauvegarde du déploiement et la dernière sauvegarde avant migration ; la restauration est une opération
  manuelle de l'exploitation.
- **Ordre `interrompu`** : le passage a été coupé (redémarrage, panne) pendant l'ordre. Il n'est jamais rejoué : jouer
  `etat`, constater, et envoyer un nouvel ordre si besoin.
- **Empreinte de `github.com` inattendue** : l'installateur s'arrête sans écrire `known_hosts`. Ne pas contourner : vérifier le
  réseau et l'empreinte publiée par GitHub (`SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU`).
- **La place manque dans une zone** : `vider-la-corbeille` (avec `go`) libère de la place ; c'est la seule suppression réelle.
- **`.echec` dans `backups/`** : une sauvegarde de déploiement a échoué à un contrôle ; les fichiers fautifs sont gardés pour
  examen, jamais effacés.

## 6 · Mise à jour et désinstallation

- **Mise à jour** : déposer la nouvelle archive, `sudo sh installer.sh`. Le programme est copié dans un dossier neuf voisin
  (pour une réinstallation de la même version, `<version>.nouveau`, puis `<version>` à la fois suivante : les deux noms
  alternent), le lien `courant` est basculé dessus de façon atomique ; la configuration et les clés existantes sont
  gardées telles quelles. L'ancien dossier de la même version n'est retiré qu'une fois pris puis relâchés les deux
  verrous de file (`/var/lib/deployeur/verrou-deploiement` et `verrou-fichiers`), donc après la fin d'un éventuel passage
  en cours ; l'attente est bornée à 30 minutes, au-delà l'installateur laisse l'ancien dossier et le dit.
- **Désinstallation** : `sudo sh installer.sh --desinstaller` arrête et retire les unités et les minuteurs et supprime
  `/opt/deployeur`. Il **garde** `/etc/deployeur`, `/var/lib/deployeur`, les zones et le compte `transfert`, et le dit.
