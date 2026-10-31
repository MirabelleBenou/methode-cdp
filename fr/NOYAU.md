# NOYAU — la méthode CdP pour un projet à un seul CdP
### 31 octobre 2026 · deux pages qui se suffisent · mode A (`LISEZ_MOI.md` §2 bis)

*Si tu démarres seul avec un CdP, lis ceci et rien d'autre : le reste du package s'ajoute quand un signe vécu le
demande (la table, à la fin). Les termes sont au `GLOSSAIRE.md`.*

## 1 · Les trois rôles

- **Toi, le porteur** : tu décides et tu valides à l'écran ; tu ne parles qu'au CdP ; tu poses les tags et les
  releases (une session ne peut pas). Tu ne lances aucune commande.
- **Le CdP** (chef de projet, Opus, session longue) : il décide avec toi, mesure l'état réel, écrit le cadrage, lance le
  dev, réceptionne, clôt et tient les vivants. **Il n'écrit pas le code livré** : un outil qui manque devient un lot.
- **Le dev** (Sonnet par défaut) : lancé par le CdP en sous-agent de sa session, sans son contexte, il exécute **un
  cadrage** et ne parle qu'au CdP, par ce qu'il pousse et par sa réponse finale.

**La posture du CdP** : il te propose des options numérotées avec une recommandation ; quand il a tranché sans toi, sa
réponse finit par « Décidé sans toi : … » ; une question simple reçoit une réponse directe, sans circuit de lot.

## 2 · Les trois couches

1. **La skill personnelle `methode-cdp`** (ton compte, tous tes projets) : les rôles, la posture, le circuit général.
2. **Les instructions du projet** (claude.ai) : ton profil, où sont les vivants, quels dépôts. Des pointeurs, pas des
   règles : une règle copiée ici dériverait.
3. **Les vivants et les dépôts** : la méthode du projet, le checkpoint, le registre des décisions, le plan,
   `chantiers.yaml` (au dépôt des vivants), et le code. Ils changent à chaque lot clos, par le CdP seul.

**Précédence** : la méthode du projet prime sur la skill ; le cadrage prime sur le prompt du dev pour ce que fait le
lot ; tes décisions au registre priment sur tout.

## 3 · Le cycle d'un lot

1. **L'étude** : le CdP mesure l'état réel (jamais l'état supposé) et décide avec toi, en options numérotées avec une
   recommandation.
2. **Le cadrage** : un seul document qui se suffit — ce que le lot fait, **ce qui ne bouge pas**, la liste exacte des
   fichiers permis, des critères **en deltas contre la base**, les arrêts. Poussé seul sur la branche `lot/<version>`.
3. **Le dev** : il construit, mesure, livre un commit puis un rapport. S'il bute sur un point ambigu, impossible ou
   contraire à l'état réel, **il s'arrête** (`ARRET_<n>.md`) au lieu de trancher.
4. **La réception à froid** : le CdP remesure sur `git archive` du commit livré, lit le diff contre les règles du
   cadrage, regarde lui-même les rendus ; tu valides à l'écran.
5. **La clôture** : fusion en avance rapide après ta validation, une entrée au registre, les chantiers à jour, un
   commit « Lot clos » aux vivants, puis le miroir au projet.

## 4 · Le checkpoint et la passation

Le **checkpoint** dit l'état réel du projet en 10 Ko ; c'est le point d'entrée de chaque session de CdP, qui le lit
d'abord et y pose son **témoin** (« session en activité : <huit derniers caractères de l'identifiant de session> »).

**La passation se mesure** (`modeles/contexte.py`), parce que chaque tour relit tout le contexte : plus il est gros,
plus chaque tour coûte et plus la qualité baisse. **À 450 000 jetons**, le CdP te prévient en tête de réponse et ne
lance plus de lot neuf ; **à 550 000 au plus tard**, à une fin de file naturelle ou au premier signe de saturation, il
**passe la main** : il réécrit le §0 du checkpoint, rend le témoin, pousse, puis te donne la **ligne fixe** à coller dans
une conversation neuve. Chaque passation note les signes de saturation vus (ou « aucun »). Rien ne voyage hors du dépôt.

## 5 · Ce qui ne pardonne pas

- **Rien ne se croit, tout se mesure** : à froid, sur l'archive livrée, en deltas ; jamais recopié du rapport du dev.
- **Une livraison = un nouveau numéro** : ce qui t'est remis ou déployé porte une version jamais remise ; un correctif
  est un lot suivant. Aucun changement de version sans ton accord.
- **Le dev ne pousse que la branche de son lot** : jamais `main`, jamais de tag, jamais `--force`.
- **Un arrêt juste du dev n'est jamais un reproche** : l'exécution a souvent raison contre le cadrage.
- **Les invariants du projet** (un fichier, une empreinte) ne bougent que sur ton autorisation écrite au cadrage.
- **Un dépôt de code public ne reçoit que le code** : le prompt du dev et les lots vont à un dépôt privé.
- **Aucun secret dans un dépôt**, ni donnée de production ; le CdP ne supprime rien sans ton accord.

## 6 · Les extensions : quand en avoir besoin, où les lire

Chacune s'ajoute sans rien migrer. Tant que le signe ne s'est pas produit, ne l'installe pas.

| extension | quand : le signe vécu | où |
|---|---|---|
| **Plusieurs CdP** (modes B et C) | un second module démarre, ou tu veux deux sujets en même temps dans deux conversations | `LISEZ_MOI.md` §2 bis, §3 bis, §3 ter ; `modeles/METHODE.md` §1 bis |
| **L'arbitre des vivants** | des numéros de décision en double, un tableau désaligné, ou une session oubliée qui garde son témoin | `LISEZ_MOI.md` §2 ter ; `modeles/ARBITRE.md` |
| **Le dépôt d'ordres** | une donnée produite en session doit arriver sur le serveur, et tu ne veux pas la déposer à la main | `LISEZ_MOI.md` §2 quater ; `modeles/EXECUTANT_SERVEUR.md` §5 |
| **L'exécutant local** | tu pilotes un jeu ou une application sur ton PC et le pont de l'application Claude ne donne pas ta machine | `modeles/EXECUTANT_LOCAL.md` ; `skill/SKILL.md` §5 bis |
| **L'exécutant serveur et le déploiement** | tu administres un serveur de production et tu déposes le livrable à la main à chaque lot | `modeles/EXECUTANT_SERVEUR.md` ; `modeles/METHODE.md` §4 bis |
| **Le tableau publié** | tu ne lis plus `chantiers.yaml` tel quel : tu veux voir d'un coup d'œil ce qui est à faire | `modeles/METHODE.md` §6 (« Le tableau des chantiers ») ; `modeles/generer_tableau.py` |
| **La fiche produit** | un même produit a plusieurs CdP de modules, et le commun (rituel, banc, pièges) se répète dans chaque checkpoint | `modeles/METHODE.md` §1 bis ; `skill/SKILL.md` §11 |

*Pour démarrer : `LISEZ_MOI.md` §3, puis `2_PROMPT_AMORCAGE_CDP.md` §A.*
