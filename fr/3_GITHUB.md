# GITHUB DANS LA MÉTHODE
### Les dépôts, leur structure, le circuit d'un lot, ce qui ne passe pas depuis une session

*Les dépôts remplacent tout ce qui se téléversait : le code, les vivants, les cadrages et les rapports. Une session de
CdP ou de dev part d'un clone et repart par un push. Le bac à sable ne garde rien d'une session à l'autre : tout se
reconstitue depuis les dépôts.*

---

## 1 · Les familles de dépôts

| dépôt | visibilité | porte | qui y écrit |
|---|---|---|---|
| **`<owner>/<Projet>`** — les vivants | privé | `README.md` ; `Methode/METHODE_<P>.md` ; `<Dossier>/` : checkpoint, registre, plan, `chantiers.yaml`, statuts des sous-projets ; `<Dossier>/attendus/<version>/` ; `<Dossier>/outils_cdp/` ; `<Dossier>/Archives/` | **les sessions de CdP seules** |
| **`<owner>/<Projet>-App`** — le code | privé (public : §6 B) | le code à la racine ; `banc/` ; `PROMPT_DEV_<P>.md` ; `lots/<version>/` ; `.gitattributes`, `.gitignore`, `CHANGELOG.md` | le CdP sur `main` (fusion, cadrage) ; le dev sur la branche de son lot |

**Le dépôt de code est public** (GitHub Pages, licence ouverte) : **le prompt du dev et `lots/` n'y vont jamais** — ils
nomment le porteur, décrivent la méthode et citent le registre. Ils vont dans un troisième dépôt, privé (§6 B). Un fichier
poussé sur un dépôt public y reste dans l'historique même retiré ensuite : la règle vaut **dès le premier commit**.

**Pourquoi deux dépôts** : le dev lit tout le dépôt de code ; il ne doit pas lire les attendus de la réception, ni les
décisions en cours, ni les autres chantiers. Les vivants restent au CdP.

**Une troisième famille, facultative — le dépôt d'ordres** : quand le projet a un serveur de production et un exécutant
serveur (`modeles/EXECUTANT_SERVEUR.md`), le CdP y déploie par des ordres.

| dépôt | visibilité | porte | qui y écrit |
|---|---|---|---|
| **`<owner>/<Projet>-Ordres`** — les ordres | privé | `ordres/<id>.json` ; `resultats/<id>.md` ; `LISEZ_MOI.md`, le format des ordres | **le CdP** (les ordres) et **le serveur** (les comptes rendus, par une clé de déploiement en écriture sur ce seul dépôt) ; **jamais le dev** |

Le serveur lit le dépôt de code par une seconde clé de déploiement, **en lecture seule**. Chaque CdP qui déploie
rattache le dépôt d'ordres en écriture ; le dev ne le rattache pas. Un ordre ne se réécrit jamais ; son identifiant se
prend par le push, comme un numéro de décision.

---

## 2 · La structure du dépôt de code

```
<Projet>-App/
├── <le code livré>            ← exactement ce que porte l'archive de déploiement
├── CHANGELOG.md               ← dans l'archive
├── banc/                      ← export-ignore : l'outillage de mesure, son README d'abord
├── PROMPT_DEV_<P>.md          ← export-ignore : la commande permanente du dev
├── lots/                      ← export-ignore
│   └── v<X.Y>/
│       ├── CADRAGE.md         ← le CdP, un seul commit sur la branche du lot
│       ├── ADDENDUM_<n>.md    ← le CdP, pour lever un arrêt ou un écart, avant la remise
│       ├── ARRET_<n>.md       ← le dev, avant de s'arrêter
│       ├── RAPPORT_DEV.md     ← le dev, après le commit de livraison
│       └── maquette/          ← la maquette du CdP, ou les images montrées
├── .gitattributes             ← export-ignore de lui-même aussi
└── .gitignore
```

**`.gitattributes`** (modèle dans `modeles/depot-app/`) :

```
banc/               export-ignore
lots/               export-ignore
PROMPT_DEV_*.md     export-ignore
.gitattributes      export-ignore
```

**L'archive de déploiement est `git archive` du commit de livraison** : `banc/`, `lots/` et le prompt n'y entrent pas.
C'est elle que le dev mesure, que le CdP remesure, et que tu déploies — la même, à l'octet.

---

## 3 · Le circuit d'un lot, par les branches

```
main ──●────────────────────────────────────────────●  (avance rapide après ta validation)
        \                                          /
lot/vX.Y ●─ CADRAGE ─ … travail … ─ LIVRAISON ─ RAPPORT
          (CdP)       (dev)        (dev)        (dev)
                         └ ARRET_1 (dev) ─ ADDENDUM_1 (CdP) ┘  si besoin
```

1. **Le CdP crée `lot/v<X.Y>` depuis la tête de `main`** et y pousse **un seul commit** : `lots/v<X.Y>/CADRAGE.md` (et
   sa maquette s'il y en a une). Le cadrage nomme le commit de base (la tête de `main`).
2. **Le CdP lance le dev en sous-agent** (`modeles/COMMANDE_DEV.md`) : modèle et effort du cadrage, clone dans un dossier
   à part, rien d'autre en contexte. *Repli : une ligne que tu colles dans une conversation neuve.*
3. **Un arrêt** : le dev pousse sa branche avec `ARRET_<n>.md` et s'arrête. Le CdP lit, pousse `ADDENDUM_<n>.md` sur la
   même branche, relance le dev.
4. **La livraison** : le dev pousse son commit de livraison, **puis** `RAPPORT_DEV.md` dans un commit à part (le rapport
   n'entre pas dans l'archive, l'empreinte n'en dépend pas).
5. **La réception** : le CdP refait `git archive` du commit de livraison, remesure à froid, relit le diff, regarde les
   rendus. Il te remet le livrable sous son nom exact, avec son sha256.
6. **Après ta validation en production** : `git push origin lot/v<X.Y>:main` — **avance rapide, jamais `--force`**.
   Puis la clôture des vivants, un commit « Lot v<X.Y> clos » au dépôt des vivants, le miroir au projet.

**Une livraison = un nouveau numéro** : un correctif ou des retours d'essai après une remise font un lot de la version
suivante, sur sa propre branche partie de celle du lot, un commit et un rapport chacun. L'addendum sous la même version ne
sert que tant que rien n'a été remis ni déployé.

---

## 4 · Le CdP au dépôt des vivants

- Il le rattache (`add_repo`, accès `push`) et le clone en début de session : **c'est sa copie de travail**.
- `git pull` avant d'écrire, `git fetch origin main` avant de pousser.
- Il modifie par remplacements ciblés ; **la version d'un document est dans son en-tête, l'historique dans git** ; les
  noms de fichiers restent stables.
- **Un seul CdP, des modules indépendants, ou des modules liés avec un coordinateur** : `LISEZ_MOI.md` §2 bis dit
  ce qui s'applique dans chaque cas.
- **Plusieurs CdP peuvent partager les vivants**, un par domaine (méthode §1 bis) : chacun son checkpoint et son
  témoin ; registre, plan et chantiers en ajout seul ; un numéro de décision se réserve par un push ; un livrable n'a qu'un lot en vol, sa version se
  calcule quand le lot le prend ; `pull` avant
  chaque écriture, un conflit se voit au `pull` au lieu de s'écraser.
- **Le miroir au projet** : à chaque clôture, chaque fichier modifié se recopie par l'outil du projet en envoyant le
  fichier depuis le clone (`project_write` avec `local_path`), sous le même nom. **Jamais depuis le texte que rend
  l'outil du projet** : il rend tout en texte, sans preuve à l'octet. Un « Sync now » GitHub du projet n'est pas
  automatique — le miroir par le CdP t'évite ce geste.
- Il dit dans sa réponse ce qu'il a écrit : dépôt, commit, chemin.

---

## 5 · Ce qui ne passe pas depuis une session — et les autres pièges

| piège | ce qui se passe | la parade |
|---|---|---|
| **Tags et releases** | le push d'un tag coupe, l'API répond 403 | **tu les poses sur GitHub**, avec le texte que te donne le CdP |
| **Suppression de branche** | refus 403 | tu supprimes les branches fusionnées ; le checkpoint les liste |
| **Création de dépôt** | impossible depuis une session | tu crées le dépôt vide ; la session le rattache |
| **Un dépôt par session** | chaque session rattache ses dépôts (`add_repo`) | un clone à la fois, délai de commande généreux |
| **Rattachement non demandé** | le garde-fou d'une session refuse un dépôt que tu n'as pas demandé en toutes lettres | **la ligne fixe d'un domaine nomme tous ses dépôts**, en accès push : la ligne que tu colles vaut la demande ; un dépôt de plus en route, la session te le demande en une ligne prête (« dis-moi « rattache X » ») |
| **Session de dev ouverte à la main** | elle peut échouer à rattacher un dépôt privé | le sous-agent du CdP hérite des dépôts de sa session |
| **Clone d'une seule branche** | `git fetch origin main` ne crée pas `origin/main` | écrire `git fetch origin main:refs/remotes/origin/main` |
| **Branche de lot qui suit `origin/main`** | le hook de fin de tour croit à des commits non poussés | fixer `branch.<lot>.merge` et ajouter la branche au `remote.origin.fetch` |
| **Lignes d'attribution** | la session impose ses lignes dans les commits | sur un dépôt public, elles se voient : à savoir |
| **Secrets** | un `.env` poussé est publié pour toujours | seul `.env.example` porte des valeurs, factices ; vérifier avant le premier push |
| **Dossier `dist/` ignoré mais suivi** | `git add` ne le prend pas | `git add -f` |
| **Rejet HTTP 413 au push** | push d'une copie pas à jour | `git fetch origin main` avant de pousser |
| **Casse du nom de dépôt** | la session clone en minuscules | les deux marchent ; l'adresse canonique est celle de la création |

---

## 6 · Variantes

**A · Projet sans code** (documentation, campagne, données) : un seul dépôt, celui des vivants ; les livrables y vivent
sous `livrables/`, versionnés par commit. Pas de dev en sous-agent si le CdP ne produit que des documents — la règle « le
CdP n'écrit pas le livré » s'applique au code, pas à la documentation, que le CdP peut éditer sur ton autorisation.

**B · Code public** (licence ouverte, GitHub Pages) : **trois dépôts**, que tu crées vides avant l'amorçage.

| dépôt | visibilité | porte |
|---|---|---|
| `<Projet>` | privé | les vivants, comme d'habitude |
| `<Projet>-App` | **public** | le code, ses tests, le banc s'il ne nomme personne, `.gitattributes`, `.github/` — et rien d'autre |
| `<Projet>-Lots` | privé | `PROMPT_DEV_<P>.md` à la racine ; `lots/<lot>/` (cadrage, addenda, arrêts, rapport, maquette) sur la branche `lot/<lot>` |

- **Le circuit** : le CdP pousse le cadrage sur `lot/<lot>` du dépôt des lots ; il nomme le commit du dépôt public d'où
  part le code. Le dev lit le prompt et le cadrage au dépôt des lots, clone le dépôt public, y pousse le code sur sa
  propre branche `lot/<lot>`, et pousse arrêts et rapport au dépôt des lots. Le sous-agent hérite des trois dépôts.
- **Le dev ne lit pas les vivants** : c'est pour cela que le prompt et les lots ne vont pas au dépôt des vivants, où sont
  les attendus de la réception.
- **Un outil simple peut se passer de prompt du dev** : le cadrage se suffit alors, et nomme les fonctions à lire dans un
  gros fichier de build.
- Après ta validation : avance rapide de `main` public (à l'octet de l'archive reçue) ; au jalon, le `CHANGELOG` et ce
  que sert GitHub Pages, puis **tu poses le tag et la release**.
- **Le CdP relit chaque diff poussé au public** : aucun prénom, aucun profil, aucune référence à la méthode, au registre
  ou à un autre projet. Les lignes d'attribution des commits, imposées par la session, s'y voient.

**C · Plusieurs sous-projets** : un seul dépôt des vivants, un dossier par sous-projet, un seul registre et un seul
`chantiers.yaml` (un champ `module`), un statut par sous-projet ; un dépôt de code par livrable déployé à part.

- **Un seul dépôt de lots pour toute la suite** (`<Projet>-Lots`, privé), même quand les dépôts de code sont plusieurs,
  publics ou privés : chaque lot y porte **un préfixe de module** — branche `lot/<préfixe>-<lot>`, dossier
  `lots/<préfixe>-<lot>/` — et son code part du dépôt de code du module, sur `lot/<lot>`. Les prompts du dev des modules
  y vivent aussi, à la racine. Un dépôt de code privé y gagne : il ne porte plus que le code et le banc.
- **Pourquoi un seul** : un `-Lots` par dépôt de code multiplie les rattachements, les clones et les règles de circuit ;
  un seul garde une règle pour tous, et le CdP n'a qu'un endroit où verser cadrages et rapports.
- **En le formant après coup** : partir de l'historique d'un `-Lots` existant (avance rapide sur le dépôt neuf, vide),
  copier les autres dossiers de lots dans un commit, contrôler chaque empreinte d'arbre (`git rev-parse <ref>:lots/<x>`),
  et retirer `lots/` du dépôt de code en vérifiant que la liste (chemin, mode, sha256) de `git archive` ne bouge pas.
  Les dossiers déjà clos gardent leur nom ; seuls les lots à venir prennent le préfixe.

---

## 7 · Ce qui ne va jamais dans un dépôt

*Et dans un dépôt public, en plus : le prompt du dev et `lots/` (§6 B).*

- les secrets, jetons, mots de passe, `.env` réels ;
- les données de production (journaux, dumps, exports) : elles se téléversent dans la session qui en a besoin ;
- les images à faire valider par toi : elles passent dans la discussion (ou dans `lots/<version>/maquette/` quand le
  cadrage les commande).
