# L'exécutant serveur — un programme déterministe sur le serveur de production, piloté par un dépôt d'ordres · v1
### 28 octobre 2026 · éprouvé sur un projet réel (une application web sous Docker Compose et deux pages HTML autoportantes)

*Pour un projet dont le livrable tourne **sur un serveur que le porteur administre**. Le CdP y déploie lui-même, sur le
« go » du porteur, sans que personne ne dépose de fichier ni ne lance de commande. Le reste de la méthode ne change pas :
le CdP cadre, réceptionne et déploie ; l'exécutant serveur exécute ; le porteur décide et valide à l'écran.*

> **Module facultatif.** Pas de serveur de production, ou un hébergement qui déploie déjà depuis Git : **sautez ce
> guide.** Le livrable se remet alors au porteur tel quel (méthode §4).

*L'implémentation de référence est dans `modeles/executant-serveur/` (dans la copie publique : `templates/server-runner/`,
à la racine, non traduite). Son code, ses identifiants et sa documentation sont **en français**. Elle se lit avec ce
guide ; elle n'en est pas la condition : un autre programme qui tient les mêmes règles fait l'affaire.*

---

## 1. Quand s'en servir, quand ne pas

**Oui** : une application ou des fichiers servis par une machine que vous administrez (une VM, un serveur dédié, une
machine chez vous), où un livrable reçu doit aujourd'hui être déposé puis lancé à la main.

**Non** :
- un hébergement mutualisé, ou une plateforme qui déploie déjà depuis Git (Pages, PaaS) : le push suffit ;
- un livrable qui ne se sert pas (un PDF, une archive qu'on télécharge) : il se remet ;
- un serveur que vous n'administrez pas (pas de root, pas de systemd).

**Ce que ça change** : le porteur ne dépose plus rien. Il dit « go », et valide à l'écran. Le CdP voit la production
(version servie, santé, sauvegarde, comptes) sans que le porteur relaie une sortie de commande.

## 2. Les rôles, et la règle

| | fait | ne fait pas |
|---|---|---|
| **CdP** (cloud) | réceptionne, demande le « go », pousse l'ordre, lit le compte rendu, le dit au porteur, fusionne après la validation | ne se connecte jamais au serveur ; ne restaure jamais une base |
| **Exécutant serveur** (le programme ; dans un projet, souvent « le déployeur ») | tire les ordres, n'exécute que sa liste blanche, vérifie la santé, revient en arrière quand c'est sûr, pousse son compte rendu | ne décide rien ; n'exécute jamais une commande écrite dans un ordre |
| **Porteur** | installe une fois ; dit « go » en nommant l'action ; valide à l'écran ; décide après un échec qui touche aux données | ne dépose plus rien, ne lance plus rien, sauf en repli |
| **Dev** | construit le livrable, comme toujours | **ne lit ni n'écrit jamais au dépôt d'ordres** |

**La règle : aucune IA dans le chemin du déploiement.** Le déploiement est un programme déterministe : mêmes entrées,
même résultat. **Un agent sur un serveur de production, s'il existe, est borné** — ni secrets, ni écriture en base, ni
root : un compte dédié hors du groupe `docker` ; `sudo` limité à une liste (l'exécutant serveur, la lecture des journaux,
l'état des conteneurs, un client de base sous un rôle en lecture seule) ; le fichier des secrets illisible pour lui ;
jamais en mode sans permissions, jamais lancé seul par une tâche planifiée. Il appelle l'exécutant serveur, il ne le
remplace pas. *Pourquoi* : un agent à pleins droits lit les secrets et la base, sur une machine qui sort librement, et il
lit des contenus que les utilisateurs déposent (journaux, titres, pseudonymes) — un texte piégé parlerait à un agent qui
peut tout.

## 3. Le circuit, côté CdP

```
CdP (cloud)                      GitHub                           serveur
───────────                      ──────                           ───────
réception sans écart
porteur : « go déploiement v1.2.3 »
pousse ordres/<id>.json  ──────► dépôt d'ordres (privé)
                                        ▲     │  chaque minute (minuteur systemd, SSH sortant)
                                        │     ▼
                                        │  exécutant serveur : ordre neuf ? valide ?
                                        │     ├─ récupère le commit (dépôt de code : clé en lecture seule)
                                        │     ├─ sauvegarde relue, comptes, déploie, santé
                                        │     ├─ revient seul en arrière quand c'est sûr
                                        └─────┴─ pousse resultats/<id>.md
lit le compte rendu, dit au porteur
« v1.2.3 servie, santé bonne,
  sauvegarde …, comptes identiques » ──► le porteur valide à l'écran
fusion dans main
```

1. **Une application qui a des utilisateurs** : après une réception sans écart, le CdP demande au porteur **un « go » qui
   nomme l'action** — « go déploiement v1.2.3 », pas « go » ni « ok » — et le cite mot pour mot dans le champ `go` de
   l'ordre (leçon ④).
2. **Il pousse `ordres/<id>.json`** au dépôt d'ordres. L'identifiant est `AAAA-MM-JJ-NN` : **le suivant au dépôt, pris
   par le push** — push refusé → `git pull`, numéro suivant, comme un numéro de décision. Un ordre ne se réécrit jamais :
   pour corriger, un nouvel ordre.
3. **Il lit `resultats/<id>.md`** : une à deux minutes en temps normal. **Attente bornée** (une relecture toutes les
   20 à 30 s, quelques minutes au plus), **jamais une boucle sans fin** ; passé le délai, il le dit au porteur et lance
   `etat`.
4. **Il dit au porteur** la version servie, la santé, la sauvegarde prise et les comptes avant et après. Le porteur valide
   à l'écran ; **puis** la fusion dans `main`, comme sans exécutant serveur. Un compte rendu en échec : le CdP le dit, avec
   le nom de la sauvegarde ; la base ne se restaure que sur décision du porteur, **par la procédure manuelle**.
5. **Des fichiers statiques à retour instantané** (une page HTML autoportante, sans base ni redémarrage) : déploiement
   **direct après la réception, sans go** ; le porteur valide ensuite à l'écran.
6. **Le retour** : `revenir` — sur go pour l'application, **refusé après une migration** ; sans go pour un fichier
   statique.
7. **Les opérations de fichiers** (poser une archive, décompresser, basculer un dossier servi) : action `fichiers`, dans
   des **zones déclarées côté serveur**, sans go — sauf vider la corbeille, la seule suppression réelle, sur go.
8. **Avant un cadrage qui touche la production**, le CdP lance `etat` : version servie, conteneurs, place disque,
   sauvegardes, comptes. C'est la sonde, sans geste du porteur.

**Chaque CdP qui déploie rattache le dépôt d'ordres en écriture** en début de session. **Le dev ne le lit ni ne
l'écrit** : il n'est pas dans sa commande, et le prompt du dev le lui interdit.

**Le repli** : quand l'exécutant serveur est en panne (ou désinstallé), le livrable se remet au porteur tel quel, sous
son nom exact avec son sha256, et la procédure manuelle du dépôt de code s'applique. La réception continue de produire
l'archive : le repli est toujours prêt.

**Jamais de restauration de base par l'exécutant serveur** : c'est une procédure manuelle, écrite au dépôt de code, qui
commence par sauvegarder l'état présent.

## 4. Les prérequis

- **Une machine Linux avec systemd**, `git`, `python3` (3.11 ou plus récent pour l'implémentation de référence), et
  **un accès sortant à GitHub** (SSH, port 22).
- **Docker Compose** s'il y a une application ; une **route de santé sans session** qui rend la version servie
  (`{"version": "1.2.3"}`), et un fichier `VERSION` à la racine de l'archive.
- **Aucun port entrant.** Le serveur va chercher ses ordres ; personne n'entre chez lui. L'exposition de l'application
  (un tunnel, un proxy, un VPN) ne regarde pas l'exécutant serveur.
- **Facultatif — déposer de gros fichiers depuis le PC** : `rsync` sur SSH vers un dossier `entree/`, avec une clé
  restreinte (écriture seule, enfermée dans ce dossier, sans shell). Il faut alors **un chemin privé vers le port SSH du
  serveur** : un VPN (par exemple Tailscale), un réseau local, ou SSH exposé par clé seule. Le réseau se nomme dans la
  configuration de l'exécutant local (hôte, port, utilisateur), jamais dans la méthode ni dans le code ; en changer, c'est
  changer l'hôte et la règle du pare-feu. **Le pare-feu reste au porteur** : l'installateur n'y touche pas.
- **Un accès root ponctuel** pour l'installation (console web de l'hébergeur ou SSH) : un seul script à lancer.

## 5. Le dépôt d'ordres et les clés

**Le dépôt d'ordres** : un dépôt **privé**, vide à la création, que le porteur crée (`<owner>/<Projet>-Ordres`).

```
ordres/<id>.json        écrits par le CdP, jamais réécrits
resultats/<id>.md       écrits par l'exécutant serveur, un par ordre
LISEZ_MOI.md            le format des ordres (copie de docs/ORDRES.md de l'implémentation)
```

Écrit par le CdP (les ordres) et par le serveur (les comptes rendus), **jamais par le dev**. Aucun secret, aucune donnée
de production dans un ordre ni dans un compte rendu (le serveur filtre ses journaux avant de les pousser, §7).

**Les clés de déploiement**, générées sur le serveur par l'installateur, **une par dépôt** :

| clé | dépôt | droit |
|---|---|---|
| `cle_ordres` | le dépôt d'ordres | **écriture** (lire les ordres, pousser les comptes rendus) |
| `cle_app` | le dépôt de code de l'application | **lecture seule** |

Une clé de déploiement ne vaut que pour son dépôt : un serveur compromis ne réécrit ni le code, ni les lots, ni les
vivants. Les fichiers statiques viennent de dépôts **publics**, sans clé. **Une pièce jointe de release d'un dépôt
privé** ne se lit pas avec une clé de déploiement : il faudrait un jeton à grain fin, en lecture seule, sur les seuls
dépôts choisis — à ne poser que si une release privée sert vraiment de source.

## 6. L'installation, par un seul script

**D'abord une sonde en lecture seule** (leçon ⑤) : le CdP écrit un script d'inventaire que le porteur dépose et lance
une fois — dossier et nom du projet Compose (constaté, pas supposé), volumes et conteneurs, ce que le dossier contient
hors archive (`.env`, `backups/`…), propriétaire des dossiers servis, versions du système, de Git et de Docker, disques
et place libre, pare-feu, et, s'il y a un dépôt de fichiers depuis le PC, SSH. Le cadrage se fonde sur sa sortie.

**Puis l'installateur** (`installer.sh` dans l'implémentation de référence), un seul script POSIX, idempotent, à lancer en
root depuis le dossier de l'archive :

```
sudo sh installer.sh
```

Il vérifie le système, copie le programme dans un dossier neuf de `/opt/deployeur/` (bascule atomique d'un lien), écrit
la configuration **seulement si elle n'existe pas** et la valide, génère les deux clés **seulement si elles manquent**,
contrôle l'empreinte publiée de `github.com` avant d'écrire `known_hosts`, crée les zones qui manquent et leur corbeille,
le compte de transfert, pose les unités systemd et active les minuteurs ; à la fin, il affiche les deux clés publiques
avec la consigne. **Il ne touche ni au pare-feu, ni à SSH, ni au dossier Compose, ni à Docker.**

**Les valeurs propres à l'installation** sont toutes dans le bloc « Valeurs de ce projet » en tête du script, seul endroit
où elles apparaissent — le programme ne connaît que la configuration :

| valeur | sens |
|---|---|
| `PROJET`, `DOSSIER_COMPOSE`, `FICHIER_COMPOSE`, `SERVICE_APP`, `SERVICE_DB`, `CONTENEUR_DB` | le projet Compose **tel que l'inventaire l'a constaté** |
| `VOLUME_BASE`, `MONTAGE_BASE`, et les autres volumes irremplaçables | ce qui ne doit jamais se perdre (§8) |
| `PREFIXE_SAUVEGARDE`, `URL_SANTE`, `DELAI_SANTE_S`, `PLACE_MIN_DEPLOIEMENT_GO`, `SAUVEGARDES_GARDER` | sauvegardes, santé, seuils |
| `DEPOT_APPLICATION`, `DEPOT_ORDRES` | les deux dépôts (adresses SSH) |
| `TABLES_HISTOIRE` | les tables dont le nombre de lignes ne doit jamais baisser |
| `SUITES` | les fichiers statiques : nom, dépôt public, chemin dans le dépôt, dossier et nom servis |
| `ZONES`, `ZONE_TRANSFERT`, `PROPRIETAIRE_ZONES` | les zones des opérations de fichiers, celle qui reçoit `entree/`, leur propriétaire |
| `DEPOTS_PUBLICS`, `HOTES_AUTORISES` | les sources autorisées des téléchargements |

**Le porteur, ensuite** : sur GitHub, **Settings → Deploy keys → Add deploy key**, deux fois — `cle_ordres` au dépôt
d'ordres **avec** « Allow write access », `cle_app` au dépôt de code **sans**. Dans la minute, le premier passage trouve
le dépôt d'ordres. Option : `sudo sh installer.sh --cle-transfert "<ligne de clé publique du PC>"` autorise le dépôt de
fichiers depuis le PC.

**Le script s'essaie avant le serveur** : sur une machine simulée (une racine d'essai, des doublures de `systemctl`,
`useradd`, `docker`…), installation, réinstallation, mise à jour et **désinstallation comprises** ; l'implémentation de
référence le fait dans ses tests (`INSTALLATEUR_PREFIXE`).

## 7. Les ordres et les comptes rendus

Un ordre est **un objet JSON** dans `ordres/<id>.json` : `id` (égal au nom du fichier), `action`, `demande_par`, et
**exactement** les champs de l'action — un champ inconnu ou manquant refuse l'ordre. L'ordre se valide **en entier avant
tout geste** ; un refus ne fait rien bouger. Un ordre ne se joue qu'une fois ; les ordres d'une file se jouent un à la
fois, par ordre d'`id`. **Le protocole est neutre** : ses noms d'actions et de champs ne nomment pas le projet
(leçon ①).

**Deux files**, chacune son minuteur et son verrou, pour qu'une opération de fichiers longue ne retarde jamais un
déploiement : `deploiement` (`etat`, `adopter`, `deployer-application`, `deployer-suite`, `revenir`, `reprendre-file`) et
`fichiers` (`fichiers`). Une file **arrêtée** (après un échec qui touche aux données) refuse tout, sauf `etat` et
`reprendre-file`. Un ordre trouvé « en cours » après une coupure devient `interrompu` et **n'est jamais rejoué**.

**`etat`** — lecture seule, toujours accepté : version servie, conteneurs, contrôles du projet, commit servi, révision de
migration, comptes de toutes les tables, place libre, dernières sauvegardes, empreintes des fichiers servis, état des
files, ordres récents.

```json
{"id": "2026-10-27-01", "action": "etat", "demande_par": "chef de projet"}
```

**`adopter`** — déclarer, une fois, le commit déjà servi : chaque fichier de son archive est comparé au dossier servi ;
un seul écart, refus. Sans go.

```json
{"id": "2026-10-27-02", "action": "adopter", "demande_par": "chef de projet",
 "commit": "0123456789abcdef0123456789abcdef01234567"}
```

**`deployer-application`** — sur go. Préconditions (bon projet, place, commit présent, `VERSION` égal à `version`, aucun
chemin protégé dans l'archive) ; comptes et révision avant ; **sauvegarde relue** ; pose des fichiers ; build ; recréation
du seul service applicatif ; **santé** (la route rend la version attendue, le journal ne montre ni échec ni trace) ;
comptes après. Échec sans migration : **retour automatique**. Échec après une migration : **aucun retour**, file arrêtée.

```json
{"id": "2026-10-27-03", "action": "deployer-application", "demande_par": "chef de projet",
 "commit": "0123456789abcdef0123456789abcdef01234567", "version": "1.2.3",
 "go": "« go déploiement v1.2.3 », le porteur, 27 octobre 10:42"}
```

**`deployer-suite`** — un fichier statique, sans go : téléchargé au commit, **sha256 de la réception vérifié** (refus s'il
diffère, le fichier servi intact) ; l'ancien devient `<nom>.prec<extension>`, le nouveau prend sa place par renommage.

```json
{"id": "2026-10-27-04", "action": "deployer-suite", "demande_par": "chef de projet", "suite": "suite-a",
 "commit": "0123456789abcdef0123456789abcdef01234567",
 "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
```

**`revenir`** — l'application sur go (le commit précédent, par le même chemin que le déploiement ; **refusé si une
migration a été appliquée depuis**) ; un fichier statique sans go (le précédent redevient le servi).

```json
{"id": "2026-10-27-05", "action": "revenir", "demande_par": "chef de projet", "cible": "application",
 "go": "« go retour à la version précédente », le porteur"}
```

```json
{"id": "2026-10-27-06", "action": "revenir", "demande_par": "chef de projet", "cible": "suite-a"}
```

**`reprendre-file`** — rouvrir une file arrêtée, sur go, une fois la décision prise.

```json
{"id": "2026-10-27-07", "action": "reprendre-file", "demande_par": "chef de projet", "file": "deploiement",
 "go": "« go reprise de la file deploiement », le porteur"}
```

**`fichiers`** — de 1 à 50 opérations jouées dans l'ordre ; la première en erreur arrête l'ordre. Opérations :
`lister`, `empreinte`, `creer-dossier`, `telecharger` (dépôt public connu à un commit, release d'un dépôt connu, hôte
autorisé, HTTPS seulement), `copier`, `deplacer`, `decompresser` (`.tar`, `.tar.gz`, `.tgz`, `.zip`, vers un dossier
neuf), `basculer` (un dossier préparé remplace un dossier servi), `mettre-a-la-corbeille`, `vider-la-corbeille` (sur go).
**Les zones sont déclarées sur le serveur, jamais dans l'ordre** ; tous les chemins sont relatifs à une zone. **Rien ne
s'efface** (tout part dans `<zone>/_corbeille/<id>/`), **rien ne s'exécute** (aucun bit d'exécution posé), **jamais
d'écrasement silencieux** (cible existante : refus, sauf `"si_existe": "remplacer"`, qui met l'ancienne à la corbeille).

```json
{"id": "2026-10-27-08", "action": "fichiers", "demande_par": "chef de projet",
 "operations": [
   {"operation": "deplacer", "zone": "echange", "de": "entree/fond.tar.gz", "zone_vers": "donnees",
    "vers": "archives/fond.tar.gz"},
   {"operation": "decompresser", "zone": "donnees", "archive": "archives/fond.tar.gz", "vers": "cartes/fond-v2"},
   {"operation": "basculer", "zone": "donnees", "prepare": "cartes/fond-v2", "servi": "cartes/fond"}]}
```

```json
{"id": "2026-10-27-09", "action": "fichiers", "demande_par": "chef de projet",
 "operations": [{"operation": "vider-la-corbeille", "zone": "donnees", "id_corbeille": "2026-10-20-03"}],
 "go": "« go vider la corbeille de l'ordre 2026-10-20-03 », le porteur"}
```

**Le compte rendu** — `resultats/<id>.md`, dont la première ligne est `Statut : …` :

| statut | sens |
|---|---|
| `réussi` | joué jusqu'au bout |
| `refusé` | validation, précondition ou opération en erreur : rien d'autre n'a bougé que ce qu'il dit |
| `échec, revenu` | échec après le début des gestes ; le retour a remis l'ancien état |
| `échec, file arrêtée` | échec qui touche aux données (migration appliquée, compte en baisse, retour impossible) ; la file attend la décision du porteur |
| `interrompu` | passage coupé pendant l'ordre ; jamais rejoué |
| `en cours` | avancement d'une opération longue |

Suivent l'ordre recopié, les heures, la version de l'exécutant serveur ; selon l'action, versions et commits avant et
après, santé, sauvegarde (noms, tailles, contrôles), comptes table par table (**baisses en gras**), révision de migration,
fichiers posés et inconnus, place libre ; en échec, l'étape, la raison, ce qui a été remis en place et **ce que le porteur
doit décider** ; enfin les dernières lignes du journal de l'application, **passées au filtre** (jetons, mots de passe,
cookies, URL à secret masqués). Extrait :

```markdown
Statut : réussi

# Compte rendu de l'ordre 2026-10-27-03

## Résumé

- version servie avant : 1.2.2 (commit 89abcdef…)
- révision de migration avant : 0039 ; après : 0039 (inchangée)
- version servie après : 1.2.3 (commit 01234567…) ; santé : bonne

## Sauvegarde

- monprojet_deploiement-0039_20261027-180003.dump (3.1 Mio ; 30 entrées TABLE DATA pour 29 tables)

## Comptes des tables

| table | avant | après |
|---|---:|---:|
| membres (histoire) | 120 | 120 |
```

Le détail, champ par champ et avec un exemple de chaque opération : `docs/ORDRES.md` de l'implémentation, recopié en
`LISEZ_MOI.md` du dépôt d'ordres.

## 8. Les données ne se perdent jamais — les invariants

Non négociables ; chacun a son test dans l'implémentation et sa vérification à la réception. Ils valent pour la base
**et pour chaque volume irremplaçable** (fichiers déposés par les utilisateurs, dépôts bruts).

1. **Le service de la base n'est jamais touché.** L'exécutant serveur ne lance que le build et la recréation du service
   applicatif (`up -d --no-deps`) ; jamais `down`, jamais `-v`, jamais de suppression ni de `prune` d'un volume. Ces mots
   sont absents du programme, et une recherche dans le code le prouve.
2. **Le bon projet ou rien.** Avant tout geste, il constate que les volumes du projet Compose attendu existent et portent
   son étiquette, et que le conteneur de la base en service est bien monté dessus. Sinon : refus. C'est la parade à **la
   base vide** : Compose nomme le projet d'après le dossier, et un déploiement dans un autre dossier démarrerait une base
   neuve sur des volumes neufs. D'où aussi : **le même dossier à chaque déploiement**, jamais un dossier par version.
3. **Une sauvegarde à chaque déploiement de l'application**, migration ou pas : dump de la base et archive des autres
   volumes, contrôlés non vides et **relus** (`pg_restore --list`, archive relue en entier), **avant** le build. Échec de
   la sauvegarde : pas de déploiement.
4. **Des comptes avant et après.** En lecture seule, le nombre de lignes des tables qui portent l'histoire du projet (les
   utilisateurs, leurs inscriptions, leurs contenus, les journaux d'activité — la liste se fixe au cadrage, sur
   l'inventaire). Un compte en baisse arrête la file, même si la santé est bonne.
5. **Jamais de restauration automatique.** Le retour automatique ne remet que du code, et seulement sans migration
   appliquée. Une restauration se fait à la main, sur décision du porteur, et commence par sauvegarder l'état présent.
6. **Une rétention minimale** : les trois dernières sauvegardes de l'exécutant serveur restent toujours, quelle que soit la
   rétention réglée ailleurs ; une sauvegarde d'une autre famille n'est jamais purgée par lui. La sauvegarde entière du
   serveur, si elle existe, reste le dernier filet.
7. **L'essai à blanc le prouve** (§9).

**Les régler pour votre projet** : les volumes et le point de montage de la base, relevés par l'inventaire (l'implémentation
de référence attend trois volumes — la base et deux autres ; avec moins, adapter `deployeur/base.py`) ; les tables
d'histoire, choisies parmi celles que l'application ne vide jamais d'elle-même (une table de session ou de cache n'y entre
pas : son compte baisse normalement) ; les **chemins protégés** de l'archive — `.env` et `backups/` par défaut —, et les
autres, **passés sur l'archive réelle avant de cadrer** (leçon ②).

## 9. L'essai à blanc, puis le premier vrai déploiement

**L'essai à blanc** prouve la chaîne entière **sans rien changer** : le commit d'essai est celui qui est déjà servi.

1. `etat` : version servie, contrôles du projet conformes, comptes, place, sauvegardes, files « en marche ».
2. `adopter` du commit servi : tous les fichiers identiques, sinon les écarts listés et rien de retenu.
3. `deployer-application` du **même commit et de la même version**, avec un go : comptes identiques avant et après,
   sauvegarde présente et relue, service recréé, santé bonne.
4. `revenir` l'application, avec un go : le chemin complet rejoué sans changement.
5. Un fichier statique en aller-retour : `deployer-suite` du fichier servi (son commit, son sha256), puis `revenir`.
6. Quelques opérations de fichiers dans une zone : `creer-dossier`, `lister`, `mettre-a-la-corbeille`.
7. **Ce que l'exploitant voit** : si le porteur dépose ou regarde des fichiers par un outil graphique (un gestionnaire de
   fichiers web), vérifier qu'il voit `entree/` et les zones — un lien symbolique peut ne pas y être suivi (leçon ③).

Le retour automatique après un échec de santé ne s'essaie pas en production : il se prouve par les tests, sur des
doublures de Docker.

**Le premier vrai déploiement** : le lot suivant, par le circuit du §3 — go nommé, ordre, compte rendu lu, validation à
l'écran, fusion. Le CdP note dans la méthode du projet que le circuit par ordres est en service et que la remise devient
le repli.

## 10. Dépannage, désinstallation, retour au dépôt manuel

- **Voir ce que fait le programme** : les journaux des deux services (`journalctl -u deployeur-deploiement.service`,
  `deployeur-fichiers.service`) et la liste des minuteurs. Le CdP, lui, lance `etat`.
- **Ordre refusé** : le compte rendu dit pourquoi ; rien n'a bougé. Corriger, envoyer **un nouvel ordre** (nouvel `id`).
- **Ordre pas joué** : le nom du fichier égal à l'`id`, poussé sur `main` du dépôt d'ordres, la clé d'ordres déclarée
  **avec** l'écriture ; le journal dit « dépôt d'ordres inaccessible » si la clé ou le réseau manque.
- **Compte rendu absent** : un push en échec se rejoue au passage suivant ; au-delà de l'attente bornée, `etat`.
- **Santé en échec** : sans migration, le retour automatique a eu lieu (`échec, revenu`) ; le journal filtré dit pourquoi.
  Le correctif fait un lot de la version suivante.
- **File arrêtée** : le compte rendu de l'ordre fautif nomme la cause et les sauvegardes ; le porteur décide (garder le
  nouveau code, ou restaurer à la main) ; puis `reprendre-file` sur go.
- **Place disque** : sous le seuil, les écritures sont refusées ; `vider-la-corbeille` (sur go) est la seule suppression.
- **Configuration invalide** : le programme refuse de tourner et liste chaque problème ; corriger, revérifier
  (`python3 -m deployeur --verifier`).
- **Désinstaller** : `sudo sh installer.sh --desinstaller` retire les unités, les minuteurs et le programme ; il **garde**
  la configuration, les clés, l'état, les zones et le compte de transfert, et le dit.
- **Revenir au dépôt manuel** : arrêter les minuteurs (ou désinstaller), retirer les deux clés de déploiement sur GitHub ;
  la remise du livrable et la procédure manuelle reprennent, la méthode du projet le note. Le dépôt d'ordres reste, comme
  historique.

## 11. La sécurité : ce que le modèle protège, ce qu'il ne protège pas

**Il protège** :
- **la surface réseau** : aucun port entrant, aucun service nouveau exposé ; tout est sortant ;
- **le code et les autres dépôts** : une clé par dépôt, l'écriture sur le seul dépôt d'ordres ;
- **contre l'ordre arbitraire** : une liste blanche d'actions, des champs exacts, aucune commande composée à partir du
  contenu d'un ordre, un seul module qui lance des processus, sans interpréteur de commandes ;
- **les données** : les invariants du §8 ;
- **les secrets** : le fichier d'environnement reste sur le serveur, hors de l'archive (chemin protégé), jamais lu par le
  programme ; tout texte de journal passe au filtre avant d'être poussé ;
- **les fichiers** : zones déclarées sur le serveur, chemins résolus et liens rejetés s'ils sortent de la zone,
  décompression contrôlée membre par membre, corbeille, aucun bit d'exécution ;
- **le dépôt depuis le PC** : une clé qui n'ouvre que `rsync` en écriture seule, sans suppression, dans `entree/`.

**Il ne protège pas** :
- **qui peut pousser au dépôt d'ordres, déploie** — dans les limites de la liste blanche. C'est le même niveau de
  confiance que « le porteur dépose ce que le CdP lui remet » ; il se tient en limitant qui a l'écriture sur ce dépôt (le
  porteur et les sessions de CdP qu'il y rattache) ;
- **un commit mauvais mais reçu** : l'identité est le commit, et la porte est la réception, puis le go ;
- **le programme lui-même** : il tourne en root (Docker équivaut à root). D'où un programme court, lu en entier à la
  réception, et ses mises à jour reçues comme un lot ;
- **une source externe autorisée** dont le contenu change : le sha256 ne protège que s'il est donné dans l'ordre ;
- **la panne du disque ou du serveur** : la sauvegarde entière du serveur reste le dernier filet ;
- **le remplissage** de `entree/` par la clé de transfert : les seuils de place refusent les écritures suivantes, ils ne
  bloquent pas le dépôt.

## 12. Les leçons de la mise en service

1. **Un cadrage qui interdit des noms dans le code ne doit pas les imposer au protocole.** Le dev s'est arrêté, à juste
   titre, sur des noms d'actions qui nommaient le projet : le protocole (actions, champs, formats) est neutre ; les noms
   propres vivent dans la configuration seule.
2. **Un motif de chemins protégés se passe sur l'archive réelle avant de cadrer.** `.env.*` attrapait `.env.example`, que
   l'application livre dans son archive, et bloquait l'adoption du commit servi.
3. **L'essai à blanc vérifie que l'outil graphique de l'exploitant voit ce qu'on lui prépare** : un gestionnaire de
   fichiers web ne suivait pas un lien symbolique posé pour lui.
4. **L'outil de la session peut bloquer la poussée d'un ordre de production sur un « go » ambigu** : demander un go qui
   nomme l'action, et le citer dans l'ordre.
5. **Une sonde en lecture seule avant tout script qui modifie le système** (inventaire, sonde du disque), et le script
   s'essaie sur une machine simulée, retour arrière compris.

## 13. L'implémentation de référence

`modeles/executant-serveur/` (copie publique : `templates/server-runner/`) : le programme (`deployeur/`, Python, bibliothèque
standard seule), ses unités systemd (`systemd/`), l'installateur (`installer.sh`), une configuration d'exemple
(`config.exemple.json`), sa documentation (`docs/INSTALLATION.md`, `docs/ORDRES.md`) et ses tests (`tests/`, sans réseau :
un faux `docker`, un faux transport HTTPS, des dépôts Git locaux ; ceux de l'installateur demandent root et `ssh-keygen`).

- **Tout y est en français** — code, identifiants, messages, documentation, comptes rendus. Le traduire n'est pas
  nécessaire pour s'en servir ; le protocole est décrit en anglais dans la version anglaise de ce guide.
- **Toutes les valeurs sont des exemples** (`monprojet`, `/srv/monprojet`, `exemple/application`, `exemple/ordres`,
  `suite-a`, les zones `donnees` et `echange`, `exemple.org`, le compte `exploitant`) : elles se remplacent dans le bloc
  « Valeurs de ce projet » d'`installer.sh`, et nulle part ailleurs.
- **La pile visée** : Docker Compose, PostgreSQL, une route de santé JSON, des fichiers statiques tirés de dépôts publics.
  Une autre pile s'adapte dans `deployeur/application.py`, `deployeur/base.py` et `deployeur/commandes.py`, par un lot
  d'outillage, cadré par le CdP, construit par le dev, reçu en lisant tout le programme.
- **Elle se reprend dans un dépôt de code du projet** (privé), comme tout livrable : versionnée, avec son `CHANGELOG`,
  ses tests au banc, et ses mises à jour déployées par l'installateur.
