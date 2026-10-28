# Les ordres et les comptes rendus

Le déployeur lit des **ordres** dans un dépôt Git privé (le dépôt d'ordres, branche `main`), n'exécute qu'une **liste
blanche d'actions** et y écrit son **compte rendu**. Aucune IA dans le chemin : mêmes entrées, même résultat. Il ne se
connecte qu'en sortie.

```
ordres/<id>.json        écrits par le chef de projet, jamais réécrits
resultats/<id>.md       écrits par le déployeur (un par ordre)
LISEZ_MOI.md            une copie de ce document
```

## 1 · Un ordre

Un ordre est **un objet JSON** dans `ordres/<id>.json`.

| champ | règle |
|---|---|
| `id` | `AAAA-MM-JJ-NN` (une date valide, puis deux chiffres) ; **égal au nom du fichier** sans `.json` |
| `action` | une des actions ci-dessous |
| `demande_par` | texte non vide : qui demande |
| …et les champs de l'action | exactement ceux listés : **un champ inconnu ou manquant refuse l'ordre** |

Le déployeur valide l'ordre **en entier avant toute action**. Action inconnue, champ inconnu ou manquant, valeur hors
forme (commit qui n'a pas 40 caractères hexadécimaux en minuscules, `sha256` qui n'en a pas 64, suite ou zone inconnue,
`go` manquant ou vide là où il est exigé, chemin absolu ou contenant `..`) : **refus, rien ne bouge**, le compte rendu dit
pourquoi. Un ordre ne se joue qu'une fois : pour corriger, on écrit un nouvel ordre avec un nouvel `id`.

Les ordres d'une file se jouent **un à la fois, par ordre d'`id`**.

### Les deux files

- **`deploiement`** : `etat`, `adopter`, `deployer-application`, `deployer-suite`, `revenir`, `reprendre-file`.
- **`fichiers`** : `fichiers`.

Chaque file a son minuteur et son verrou : une opération de fichiers longue ne retarde jamais un déploiement. Un ordre
illisible ou d'action inconnue est refusé par la file `deploiement`.

Une file peut être **arrêtée** (après un échec qui touche aux données, voir plus bas). Tant qu'elle l'est, tout ordre de
cette file est refusé (« file arrêtée depuis l'ordre … »), **sauf `etat` et `reprendre-file`**.

Un ordre trouvé « en cours » au journal au début d'un passage (passage précédent coupé par un redémarrage ou une panne)
passe au statut **`interrompu`** et **n'est jamais rejoué**.

## 2 · Les actions de la file `deploiement`

### `etat` — lecture seule, toujours accepté

```json
{
  "id": "2026-10-27-01",
  "action": "etat",
  "demande_par": "chef de projet"
}
```

Le compte rendu donne : la version servie (santé), l'état des conteneurs du projet et le résultat des contrôles du projet,
le commit servi selon le déployeur, la révision de migration et les comptes de toutes les tables, la place libre du
dossier Compose et de chaque zone, les trois dernières sauvegardes de chaque famille, le sha256 de chaque suite servie et
de son fichier précédent, l'état des deux files, les ordres joués depuis 7 jours.

### `adopter` — déclarer le commit déjà servi

```json
{
  "id": "2026-10-27-02",
  "action": "adopter",
  "demande_par": "chef de projet",
  "commit": "0123456789abcdef0123456789abcdef01234567"
}
```

Le déployeur ne connaît pas encore le commit servi. `adopter` le déclare : il compare **chaque fichier de l'archive du
commit au fichier du dossier Compose** (identité d'un fichier = son sha256 **et** son bit d'exécution pour le
propriétaire ; aucun autre bit). Tous identiques : le commit devient « servi », son manifeste et son archive sont gardés ;
les fichiers du dossier hors archive sont listés. Un seul écart : refus, rien n'est retenu. Pas de `go` : rien ne change
hors de l'état du déployeur. Refusé si un commit servi est déjà connu.

### `deployer-application` — déployer l'application (sur `go`)

```json
{
  "id": "2026-10-27-03",
  "action": "deployer-application",
  "demande_par": "chef de projet",
  "commit": "0123456789abcdef0123456789abcdef01234567",
  "version": "1.2.3",
  "go": "go de l'exploitant, 27 octobre"
}
```

`go` est obligatoire (texte non vide). Les étapes, dans l'ordre ; **la première qui échoue arrête l'ordre** :

1. **préconditions** : un commit servi est connu ; le bon projet Compose (étiquettes du conteneur de la base, trois volumes,
   montage de la base) ; place libre suffisante ; le commit existe dans le miroir de l'application (toutes les branches) ;
   l'archive contient `VERSION` égal à `version` et le fichier Compose ; **elle ne contient aucun chemin protégé**
   (`.env`, `backups/`, et ceux de la configuration) ;
2. **comptes avant** (toutes les tables) et **révision de migration avant** ; une table d'histoire absente refuse l'ordre ;
3. **sauvegarde** : dump de la base et archive des écussons, relus (`TABLE DATA`, archive relue en entier) ; un contrôle
   qui échoue garde les fichiers en `.echec` et refuse l'ordre ;
4. **pose des fichiers** : fichiers de l'archive posés (755 si exécutable dans l'archive, 644 sinon) ; ne sont retirés que
   les fichiers du manifeste servi absents de la nouvelle archive ; **un fichier inconnu des deux manifestes n'est jamais
   touché** (il est listé) ; les chemins protégés jamais ;
5. `build` du service applicatif ;
6. `up -d --no-deps` du service applicatif ;
7. **santé** : l'URL de santé répond la version de l'ordre (toutes les 5 s, au plus `delai_sante_s`) et le journal de
   l'application depuis l'étape 6 ne contient ni `Échec` ni `Traceback` ;
8. **échec après l'étape 6** : si la révision de migration est **inchangée**, retour automatique (fichiers du commit servi,
   build, up, santé de l'ancienne version) et statut `échec, revenu` ; si elle a **changé**, **aucun retour** : le nouveau
   code reste en place, il devient « servi » (et l'ancien « précédent », comme à l'étape 10), la file s'arrête
   (`échec, file arrêtée`) et le compte rendu dit « le commit `<sha>` est en place mais la file est arrêtée » et nomme la
   sauvegarde de l'étape 3 et la dernière sauvegarde avant migration ;
9. **comptes après** : une table d'histoire en baisse arrête la file, même si la santé est bonne ; comme à l'étape 8, le
   nouveau commit, qui reste en place, devient « servi » avant l'arrêt ;
10. **succès** : le commit devient « servi », l'ancien devient « précédent » (avec sa révision), purge des sauvegardes du
    déployeur (jamais sous trois, jamais une autre famille).

En cas d'échec avant l'étape 5 ou au build, les fichiers du commit servi sont remis (`échec, revenu`) ; aucun conteneur
n'a changé. **Le déployeur ne restaure jamais la base.**

### `deployer-suite` — déployer une suite (fichier HTML autoportant)

```json
{
  "id": "2026-10-27-04",
  "action": "deployer-suite",
  "demande_par": "chef de projet",
  "suite": "suite-a",
  "commit": "0123456789abcdef0123456789abcdef01234567",
  "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}
```

La suite est une clé de la configuration (dépôt public, chemin du fichier dans le dépôt, dossier et nom servis). Le fichier
est téléchargé en HTTPS au commit demandé ; **si son sha256 diffère de l'ordre : refus, le fichier servi est intact**. Sinon
l'ancien fichier est copié en `<nom>.prec<extension>` (temporaire puis `os.replace`) puis le nouveau est posé de la même
façon : le fichier servi ne manque jamais. Aucun redémarrage. Pas de `go`.

### `revenir` — retour arrière

Application (sur `go`) :

```json
{
  "id": "2026-10-27-05",
  "action": "revenir",
  "demande_par": "chef de projet",
  "cible": "application",
  "go": "go de l'exploitant"
}
```

Le retour ramène le commit « précédent » en rejouant exactement les étapes 1 à 10 de `deployer-application`. **Refus si la
révision de migration actuelle diffère de celle notée quand le précédent était servi** : une migration a été appliquée
depuis, la base ne se restaure pas par le déployeur ; le compte rendu nomme la sauvegarde à utiliser pour la procédure
manuelle.

Suite (`go` facultatif) :

```json
{
  "id": "2026-10-27-06",
  "action": "revenir",
  "demande_par": "chef de projet",
  "cible": "suite-a"
}
```

Le fichier précédent redevient le servi ; l'ancien servi devient le précédent. Refus s'il n'y a pas de fichier précédent.

### `reprendre-file` — rouvrir une file arrêtée (sur `go`)

```json
{
  "id": "2026-10-27-07",
  "action": "reprendre-file",
  "demande_par": "chef de projet",
  "file": "deploiement",
  "go": "go de l'exploitant"
}
```

`file` vaut `deploiement` ou `fichiers`. Le compte rendu rappelle l'ordre qui avait arrêté la file. Refus si la file n'est pas
arrêtée. Cet ordre est toujours joué par la file `deploiement`.

## 3 · L'action `fichiers` (file `fichiers`)

```json
{
  "id": "2026-10-27-08",
  "action": "fichiers",
  "demande_par": "chef de projet",
  "operations": [
    {"operation": "creer-dossier", "zone": "donnees", "chemin": "cartes/nouvelles"},
    {"operation": "lister", "zone": "donnees", "chemin": "cartes", "profondeur": 2}
  ]
}
```

`operations` : de 1 à 50 opérations, jouées dans l'ordre ; **la première en erreur arrête l'ordre**, le compte rendu dit
laquelle et ce qui a été fait avant. Chaque opération porte une clé `operation`. `go` (texte non vide) est facultatif dans
l'ordre, **obligatoire si une opération est `vider-la-corbeille`**.

**Les zones** sont déclarées dans la configuration de la machine (nom → chemin absolu), **jamais dans l'ordre**. Tous les
chemins d'un ordre sont relatifs à une zone. Sont refusés : un chemin absolu, un composant `..`, un caractère nul, et tout
lien symbolique qui fait sortir de la zone. **Rien ne s'efface** (tout part dans `<zone>/_corbeille/<id de l'ordre>/…`),
**rien ne s'exécute** (aucun bit d'exécution posé : fichiers en 644, dossiers en 755), **jamais d'écrasement silencieux**
(cible existante : refus, sauf `si_existe` à `remplacer`, qui met l'ancienne à la corbeille d'abord). Une opération qui
écrit est refusée si elle laisserait moins que `place_min_go` libres dans la zone. Ce qui est créé appartient au
propriétaire de la racine de la zone.

| opération | champs | effet |
|---|---|---|
| `lister` | `zone`, `chemin`, `profondeur`? (1 à 3) | arborescence, tailles, au plus 500 entrées, place libre |
| `empreinte` | `zone`, `chemins` (1 à 50) | sha256 de chaque fichier |
| `creer-dossier` | `zone`, `chemin` | crée le dossier, parents compris |
| `telecharger` | `zone`, `chemin`, `source`, `sha256`? | télécharge ; sha256 vérifié s'il est donné ; cible existante : refus |
| `copier`, `deplacer` | `zone`, `de`, `vers`, `zone_vers`?, `si_existe`? | fichier ou dossier, dans une zone ou de l'une à l'autre |
| `decompresser` | `zone`, `archive`, `vers` | `.tar`, `.tar.gz`, `.tgz`, `.zip` vers un dossier qui n'existe pas encore |
| `basculer` | `zone`, `prepare`, `servi` | `servi` part à la corbeille, `prepare` prend sa place par renommage |
| `mettre-a-la-corbeille` | `zone`, `chemin` | vers `<zone>/_corbeille/<id de l'ordre>/<chemin>` |
| `vider-la-corbeille` | `zone`, `id_corbeille`? | la seule suppression réelle ; `go` obligatoire dans l'ordre |

Sources de `telecharger` (HTTPS seulement ; redirections suivies seulement vers les mêmes hôtes) :

- `github:<propriétaire>/<dépôt>@<commit de 40 hex>:<chemin>` pour un dépôt de la liste `depots_publics` ;
- `https://github.com/<propriétaire>/<dépôt>/releases/download/…` pour un dépôt de cette liste ;
- `https://<hôte>/…` pour un hôte de `hotes_autorises`.

```json
{
  "id": "2026-10-27-09",
  "action": "fichiers",
  "demande_par": "chef de projet",
  "operations": [
    {"operation": "telecharger", "zone": "echange", "chemin": "depot/suite_a.html",
     "source": "github:exemple/depot@0123456789abcdef0123456789abcdef01234567:dist/suite_a.html",
     "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
    {"operation": "telecharger", "zone": "echange", "chemin": "depot/outil.zip",
     "source": "https://github.com/exemple/depot/releases/download/v1.0/outil.zip"},
    {"operation": "telecharger", "zone": "echange", "chemin": "depot/fond.tar.gz",
     "source": "https://exemple.org/fonds/fond.tar.gz"}
  ]
}
```

```json
{
  "id": "2026-10-27-10",
  "action": "fichiers",
  "demande_par": "chef de projet",
  "operations": [
    {"operation": "empreinte", "zone": "echange", "chemins": ["depot/suite_a.html", "depot/outil.zip"]},
    {"operation": "copier", "zone": "echange", "de": "depot/suite_a.html", "vers": "sauvegarde/suite_a.html"},
    {"operation": "copier", "zone": "echange", "de": "depot/outil.zip", "zone_vers": "donnees", "vers": "outils/outil.zip",
     "si_existe": "remplacer"}
  ]
}
```

```json
{
  "id": "2026-10-27-11",
  "action": "fichiers",
  "demande_par": "chef de projet",
  "operations": [
    {"operation": "deplacer", "zone": "echange", "de": "depot/fond.tar.gz", "zone_vers": "donnees",
     "vers": "archives/fond.tar.gz"},
    {"operation": "decompresser", "zone": "donnees", "archive": "archives/fond.tar.gz", "vers": "cartes/fond-v2"},
    {"operation": "basculer", "zone": "donnees", "prepare": "cartes/fond-v2", "servi": "cartes/fond"}
  ]
}
```

La décompression est sûre : chaque membre est lu avant l'extraction ; sont refusés tout chemin absolu, `..`, lien
symbolique ou physique, fichier spécial, et toute archive dont la taille décompressée annoncée (plus 10 %) dépasse la place
libre ; l'extraction se fait dans un dossier temporaire voisin, renommé à la fin.

```json
{
  "id": "2026-10-27-12",
  "action": "fichiers",
  "demande_par": "chef de projet",
  "operations": [
    {"operation": "mettre-a-la-corbeille", "zone": "donnees", "chemin": "cartes/ancien"},
    {"operation": "vider-la-corbeille", "zone": "donnees", "id_corbeille": "2026-10-20-03"}
  ],
  "go": "go de l'exploitant pour vider la corbeille"
}
```

## 4 · Le compte rendu

`resultats/<id>.md`, en français. **La première ligne est `Statut : …`** avec l'un de :

| statut | sens |
|---|---|
| `réussi` | l'ordre a été joué jusqu'au bout |
| `refusé` | validation ou précondition en échec, ou opération de fichiers en erreur : rien d'autre n'a bougé que ce que dit le compte rendu |
| `échec, revenu` | échec après le début des gestes ; le retour a remis l'ancien état |
| `échec, file arrêtée` | échec qui touche aux données (migration appliquée, table d'histoire en baisse, retour impossible) ; la file est arrêtée. Si le nouveau code reste en place, il est enregistré « servi » ; sinon (remise des fichiers impossible, retour automatique en échec, révision illisible…) l'état est **incertain** : le compte rendu dit « état réel à constater par `etat` », `application.json` porte un champ `incertain` (ordre, raison, date), `etat` le signale et `revenir` est refusé jusqu'au prochain déploiement réussi |
| `interrompu` | le passage a été coupé pendant l'ordre ; jamais rejoué |
| `en cours` | compte rendu intermédiaire d'une opération longue (au plus un toutes les 5 minutes) |

Suivent : l'ordre recopié, début et fin, version du déployeur ; selon l'action, la version servie avant et après, les
commits, la santé, la sauvegarde prise (noms, tailles, contrôles), les comptes table par table (**baisses en gras**), la
révision de migration avant et après, les fichiers posés, retirés et inconnus laissés, la place libre ; en échec, l'étape, la
raison, ce qui a été remis en place et **ce que l'exploitant doit décider** ; enfin les 50 dernières lignes utiles du
journal de l'application.

Exemple (extrait) d'un déploiement réussi :

```markdown
Statut : réussi

# Compte rendu de l'ordre 2026-10-27-03

## Ordre

(l'ordre recopié)

- début : 2026-10-27T18:00:03Z
- fin : 2026-10-27T18:01:41Z
- version du déployeur : 0.1.1

## Résumé

- version servie avant : 1.2.2 (commit 89abcdef…)
- cible : version 1.2.3 (commit 01234567…)
- révision de migration avant : 0039
- révision de migration après : 0039 (inchangée)
- version servie après : 1.2.3 (commit 01234567…) ; santé : bonne

## Sauvegarde

- monprojet_deploiement-0039_20261027-180003.dump (3.1 Mio ; 30 entrées TABLE DATA pour 29 tables)
- monprojet_deploiement-0039_20261027-180003_ecussons.tar.gz (212.0 Kio ; 14 membres relus sans erreur)

## Comptes des tables

| table | avant | après |
|---|---:|---:|
| membres (histoire) | 120 | 120 |
```

Exemple (extrait) d'un refus :

```markdown
Statut : refusé

# Compte rendu de l'ordre 2026-10-27-13

## Raison du refus

- l'archive contient des chemins protégés : .env

## Ce que l'exploitant doit décider

- l'ordre est refusé, rien n'a bougé hors ce qui est dit ci-dessus ; corriger puis envoyer un nouvel ordre
```

Exemple (extrait) d'une opération de fichiers :

```markdown
Statut : réussi

# Compte rendu de l'ordre 2026-10-27-08

## Opérations

- 1. creer-dossier : ok
  - créé : cartes/nouvelles
- 2. lister : ok
  - dossier 0 o cartes/nouvelles
  - 1 entrée(s) ; place libre de la zone : 612.3 Gio
```

## 5 · Le filtre

Avant d'écrire quoi que ce soit au dépôt, tout texte issu d'un journal ou d'une commande passe par un filtre qui masque
(`***`) : la valeur de toute affectation dont la clé contient `TOKEN`, `SECRET`, `PASSWORD`, `PASSWD`, `PASS`, `KEY`,
`AUTH`, `COOKIE`, `SESSION`, `DSN` ou `DATABASE_URL` (sans égard à la casse) ; le mot de passe d'une URL ; un en-tête
`Authorization:` ou `Cookie:` ; un paramètre d'URL `token=`, `code=`, `state=` ; une URL de webhook Discord ; une chaîne
`sk-ant-…` ; tout bloc de 32 caractères base64 ou hexadécimaux et plus. Le déployeur ne lit jamais le fichier
d'environnement de l'application.
