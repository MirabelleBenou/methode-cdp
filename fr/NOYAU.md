# NOYAU — la méthode CdP pour un projet à un seul CdP
### 1er novembre 2026 · le document qui se suffit pour démarrer · mode A (`LISEZ_MOI.md` §2 bis)

*Seul avec un CdP, lis ceci d'abord ; chaque modèle se lit au moment de le remplir. Le reste du package s'ajoute quand
un signe vécu le demande (la table, à la fin). Les termes sont au [`GLOSSAIRE.md`](GLOSSAIRE.md).*

## 1 · Les trois rôles

- **Toi, le porteur** : tu décides et tu valides à l'écran ; tu ne parles qu'au CdP ; tu poses les tags et les
  releases (une session ne peut pas). Tu ne lances aucune commande.
- **Le CdP** (chef de projet, Opus, session longue) : il décide avec toi, mesure l'état réel, écrit le cadrage, lance le
  dev, réceptionne, clôt et tient les vivants. **Il n'écrit pas le code livré** : un outil qui manque devient un lot
  (seule exception : les fichiers statiques que sa maquette a fixés, repris par le dev, vérifiés par sha256).
- **Le dev** (le modèle de la méthode §6) : lancé par le CdP en sous-agent de sa session, sans son contexte, il exécute **un
  cadrage** et ne parle qu'au CdP, par ce qu'il pousse et par sa réponse finale.

**La posture du CdP** : des options numérotées avec une recommandation ; quand il a tranché sans toi, sa réponse finit
par « Décidé sans toi : … » ; une question simple reçoit une réponse directe, sans circuit de lot.

## 2 · Les trois couches, et tes gestes de démarrage

1. **La skill personnelle `methode-cdp`** (ton compte, tous tes projets) : ce qu'une session sait avant de lire la
   méthode du projet.
2. **Les instructions du projet** (claude.ai) : ton profil, où sont les vivants, quels dépôts. Des pointeurs, pas des
   règles : une règle copiée ici dériverait.
3. **Les vivants et les dépôts** : la méthode du projet, le checkpoint, le registre, le plan, `chantiers.yaml` (au dépôt
   des vivants), et le code. Ils changent à chaque lot clos, par le CdP seul.

**Précédence** : tes décisions au registre priment sur tout ; la méthode du projet prime sur la skill ; pour un dev, les
conditions pratiques de sa commande priment sur le cadrage, qui prime sur le prompt du dev pour ce que fait le lot.

**Tes gestes, avant la première session** :
1. Sur GitHub, **crée deux dépôts privés vides** : `<Projet>` (les vivants) et `<Projet>-App` (le code) ; protège `main`
   contre le force-push et la suppression, et active au compte **la protection des secrets au push** — elle ne bloque que
   les pushes vers des dépôts **publics** ; pour un dépôt privé, la protection au push n'existe que dans une **organisation
   payante** (GitHub Team ou Enterprise) : **un compte personnel n'a aucune option**. Sur un compte gratuit, GitHub
   n'applique pas non plus les règles de branche aux dépôts privés : **en mode A, sur un compte personnel, aucun garde
   technique** ; le seul est le scan de secrets du banc (porte P12 du prompt du dev ; [`3_GITHUB.md`](3_GITHUB.md) §5).
2. Sur claude.ai, **crée le projet** ; colle dans ses instructions
   [`1_INSTRUCTIONS_PROJET.md`](1_INSTRUCTIONS_PROJET.md) (version courte), les `<…>` remplis.
3. **Personnalise la skill** ([`skill/SKILL.md`](skill/SKILL.md) : ses §1 et §8 te décrivent) et installe-la dans tes
   skills.
4. Ouvre une conversation avec Opus dans le projet et colle
   [`2_PROMPT_AMORCAGE_CDP.md`](2_PROMPT_AMORCAGE_CDP.md) §A, complété de ce que tu veux construire.

**Ce que le CdP crée à l'amorçage, en mode A** : au dépôt des vivants, un README, la méthode du projet, le checkpoint,
le registre, le plan (et son journal des versions), `chantiers.yaml`, et les scripts copiés du package
(`archiver_chantiers.py`, `generer_tableau.py` pour plus tard, `outils_cdp/contexte.py`) ; au dépôt de code,
`.gitattributes`, `.gitignore`, le `CHANGELOG` et le prompt du dev. Rien d'autre sans un signe.

## 3 · Le cycle d'un lot

**Le premier lot est le banc** (un lot d'outillage : ce qui mesure une archive — tests, lint, empreintes) : sans lui,
aucune porte n'est mesurable. Le premier lot de produit vient ensuite.

1. **L'étude** : le CdP mesure l'état réel (jamais l'état supposé) et décide avec toi.
2. **Le cadrage** : un seul document qui se suffit — ce que le lot fait, **ce qui ne bouge pas**, la liste exacte des
   fichiers permis, des critères **en deltas contre la base**, les arrêts. Poussé seul sur la branche du lot.
3. **Le dev** : il construit, mesure, livre un commit puis un rapport. S'il bute sur un point ambigu, impossible ou
   contraire à l'état réel, **il s'arrête** (`ARRET_<n>.md`) au lieu de trancher. **Si le CdP ne peut pas lancer de
   sous-agent**, il te donne une ligne à coller au mot près dans une conversation neuve, avec au-dessus le modèle,
   l'effort et la session ([`modeles/COMMANDE_DEV.md`](modeles/COMMANDE_DEV.md) §B).
4. **La réception à froid** : le CdP remesure sur `git archive` du commit livré, lit le diff contre les règles du
   cadrage, regarde les rendus ; lot moyen ou fort, ou dépendance nouvelle : un sous-agent d'un autre modèle relit le
   diff ; tu valides à l'écran.
5. **La clôture** : fusion en avance rapide après ta validation, la ligne du journal des versions, une entrée au
   registre, les chantiers à jour, un commit « Lot clos » aux vivants.

**Les deux régimes de version** : un livrable **déployé à chaque lot** (une application en service) prend une version par
lot, annoncée au cadrage (branche `lot/v<X.Y>`) : la plus haute version déjà prise par un lot, remis ou refusé, plus un
— la règle exacte : méthode §2, étape 6 ; un livrable **publié par release**
(un outil téléchargé en paquet) ne prend pas de version par lot (branche `lot/<nom du lot>`) : le lot complète la
section « Unreleased » du `CHANGELOG`, et la release se fait quand tu la demandes.

## 4 · Le checkpoint et la passation

Le **checkpoint** dit l'état réel sous un plafond (méthode §6) ; chaque session de CdP le lit d'abord et y pose son
**témoin** (« session en activité : <huit derniers caractères de l'identifiant de session> »). **Seul, le témoin te
protège d'une chose** : une seconde conversation ouverte par erreur sur le projet le voit, et n'écrit pas aux vivants.

**La passation se mesure** (`modeles/contexte.py`) : chaque tour relit tout le contexte, et plus il est gros, plus il
coûte et moins il est juste. Aux seuils de [`modeles/METHODE.md`](modeles/METHODE.md) §6, le CdP te prévient, cesse de
lancer des lots, puis **passe la main** — jamais avec un dev en vol : §0 du checkpoint à jour, témoin rendu, push, et la
**ligne fixe** à coller dans une conversation neuve. Rien ne voyage hors du dépôt.

**La ligne fixe**, en tête du checkpoint, sous « Opus · conversation neuve dans le projet » : « Tu es Opus-CdP-<Projet>.
Reprends : rattache en accès push les dépôts <owner> <Projet>, <Projet>-App (un clone à la fois), fais git pull dans
<Projet>, lis `<Dossier>/CHECKPOINT_<P>.md` en entier (§0 d'abord) et suis-le. » Elle nomme tous les dépôts : une
session refuse un rattachement que tu n'as pas demandé en toutes lettres, et la ligne collée vaut cette demande.

## 5 · Ce qui ne pardonne pas

- **Rien ne se croit, tout se mesure** : à froid, sur l'archive livrée, en deltas ; jamais recopié du rapport du dev.
- **Une livraison = un nouveau numéro** : ce qui t'est remis ou déployé porte un numéro jamais pris (§3), jamais `main`
  plus un ; un correctif est un lot suivant. Publié par release : le numéro se fixe à la release, que tu demandes.
- **Le dev ne pousse que la branche de son lot** : jamais `main`, jamais de tag, jamais `--force`.
- **Un arrêt juste du dev n'est jamais un reproche** : l'exécution a souvent raison contre le cadrage.
- **Les invariants du projet** (un fichier, une empreinte) ne bougent que sur ton autorisation écrite au cadrage.
- **Aucun secret dans un dépôt**, ni donnée de production ; le CdP ne supprime rien sans ton accord.

## 6 · Les extensions : quand en avoir besoin, où les lire

Chacune s'ajoute sans rien migrer. Tant que le signe ne s'est pas produit, ne l'installe pas.

| extension | quand : le signe vécu | où |
|---|---|---|
| **Plusieurs CdP** (modes B et C) | un second module démarre, ou tu veux deux sujets en même temps dans deux conversations | [`LISEZ_MOI.md`](LISEZ_MOI.md) §2 bis, §3 bis, §3 ter ; `modeles/METHODE.md` §1 bis |
| **Le dépôt public** | le code est public : le prompt du dev et les lots vont à un troisième dépôt, privé, `<Projet>-Lots` | `3_GITHUB.md` §6 B |
| **Le miroir au projet** | une conversation sans clone doit lire les vivants (le projet en porte une copie) | `modeles/METHODE.md` §6 (« Les vivants ») ; `3_GITHUB.md` §4 |
| **L'arbitre des vivants** | des numéros de décision en double, un tableau désaligné, ou une session oubliée qui garde son témoin | `LISEZ_MOI.md` §2 ter ; [`modeles/ARBITRE.md`](modeles/ARBITRE.md) (une action GitHub) |
| **Le contrôleur** | après l'arbitre : les documents enflent, se répètent ou se contredisent, et rien ne le dit assez tôt | `LISEZ_MOI.md` §2 ter ; [`modeles/CONTROLEUR.md`](modeles/CONTROLEUR.md) (une session hebdomadaire) |
| **Le dépôt d'ordres** | une donnée produite en session doit arriver sur le serveur sans toi | `LISEZ_MOI.md` §2 quater ; [`modeles/EXECUTANT_SERVEUR.md`](modeles/EXECUTANT_SERVEUR.md) §5 |
| **L'exécutant local** | tu pilotes un jeu ou une application sur ton PC et le pont de l'application Claude ne donne pas ta machine | [`modeles/EXECUTANT_LOCAL.md`](modeles/EXECUTANT_LOCAL.md) ; `modeles/METHODE.md` §1 |
| **L'exécutant serveur et le déploiement** | tu administres un serveur de production et tu déposes le livrable à la main à chaque lot | `modeles/EXECUTANT_SERVEUR.md` ; `modeles/METHODE.md` §4 bis |
| **Le tableau publié** | tu veux voir d'un coup d'œil ce qui est à faire, sans lire `chantiers.yaml` | `modeles/METHODE.md` §6 (« Le tableau des chantiers ») ; `modeles/generer_tableau.py` |
| **La fiche produit** | un même produit a plusieurs CdP de modules, et le commun (rituel, banc, pièges) se répète dans chaque checkpoint | `modeles/METHODE.md` §1 bis |

*Ce document suffit pour amorcer un projet en mode A, avec [`2_PROMPT_AMORCAGE_CDP.md`](2_PROMPT_AMORCAGE_CDP.md) §A.*
