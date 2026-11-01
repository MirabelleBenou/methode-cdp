# GLOSSAIRE — les mots de la méthode CdP
### 31 octobre 2026 · un terme, une ou deux lignes, le document où il vit

*Les chemins sont ceux du package. Pour démarrer, tu n'as besoin que des termes de la première partie : le noyau
([`NOYAU.md`](NOYAU.md)) les emploie tous ; les autres parties servent quand tu ajoutes une extension (table de `NOYAU.md` §6).*

---

## 1 · Les personnes et les sessions

| terme | ce que c'est | où il vit |
|---|---|---|
| **porteur** | toi : celui qui décide et valide à l'écran, pose les tags et les releases, supprime les branches fusionnées. Il ne parle qu'au CdP (ou à la coordination). | `NOYAU.md` §1 ; [`skill/SKILL.md`](skill/SKILL.md) §2 |
| **CdP** (chef de projet) | la session longue d'Opus qui décide avec toi, mesure, écrit les cadrages, lance le dev, réceptionne, clôt et tient les vivants. Il n'écrit pas le code livré. | `NOYAU.md` §1 ; [`modeles/METHODE.md`](modeles/METHODE.md) §1 |
| **dev** | la session (modèle et effort par défaut : la méthode §6) qui exécute un cadrage, un lot à la fois. Il ne parle qu'au CdP : par ce qu'il pousse et par sa réponse finale. | [`modeles/PROMPT_DEV.md`](modeles/PROMPT_DEV.md) ; `skill/SKILL.md` §6 |
| **sous-agent** | une session que le CdP lance depuis la sienne (outil Agent), sans son contexte, avec une commande en quatre parts. Le dev en est un ; une lecture déléguée aussi. | [`modeles/COMMANDE_DEV.md`](modeles/COMMANDE_DEV.md) §A ; [`DEPENDANCES_CLAUDE.md`](DEPENDANCES_CLAUDE.md) |
| **coordination** (le coordinateur) | la session qui tient la méthode, la table des domaines, le lancement des CdP, le package, l'outillage des vivants, l'arbitre et le contrôleur. Elle ne cadre aucun lot de produit. | [`LISEZ_MOI.md`](LISEZ_MOI.md) §2 bis ; `modeles/METHODE.md` §1 bis |
| **domaine** | un CdP, son périmètre, son checkpoint et son témoin. Une ligne de la table des domaines. | `modeles/METHODE.md` §1 bis ; `modeles/domaines.yaml` |

## 2 · Le lot, du cadrage à la clôture

| terme | ce que c'est | où il vit |
|---|---|---|
| **lot** | l'unité de travail d'un dev : un cadrage, une branche `lot/v<X.Y>` (ou `lot/<nom du lot>` pour un livrable publié par release), un commit de livraison, un rapport. | [`3_GITHUB.md`](3_GITHUB.md) §3 ; `modeles/METHODE.md` §2 |
| **cadrage** | le document autoportant d'un lot : ce qu'il fait, ce qui ne bouge pas, la liste exacte des fichiers permis, des critères en deltas contre la base, les arrêts. Le dev part de lui. | [`modeles/CADRAGE.md`](modeles/CADRAGE.md) ; `modeles/METHODE.md` §3 |
| **pré-cadrage** | les règles, critères et textes d'un lot qui n'a pas encore pris son livrable, sans version ni attendus ; il devient le cadrage quand le lot le prend. | `modeles/METHODE.md` §1 bis |
| **addendum** | `ADDENDUM_<n>.md`, écrit par le CdP pour lever un arrêt ou corriger un écart, tant que rien n'a été remis ni déployé. | [`modeles/LOT_FICHIERS.md`](modeles/LOT_FICHIERS.md) §A |
| **arrêt** | `ARRET_<n>.md`, écrit par le dev quand un point est ambigu, impossible ou contraire à l'état réel : il s'arrête au lieu de trancher. Un arrêt juste n'est jamais un reproche. | `modeles/LOT_FICHIERS.md` §B |
| **maquette** | le rendu d'un écran avant qu'on le construise : soit celle du CdP, faite par le vrai code ; soit demandée au dev, qui la livre par un arrêt (`MAQUETTE_<n>.md`). | `modeles/METHODE.md` §2 et §3 bis |
| **banc** | l'outillage qui mesure une archive (fichiers, tests, lint, empreintes) ; il se construit par le premier lot, un lot d'outillage. | `NOYAU.md` §3 ; `LISEZ_MOI.md` §5 |
| **portes** | les mesures du banc que le dev passe sur sa livraison (P0 à Pn). | `modeles/PROMPT_DEV.md` §4 (et les portes d'un lot de complexité faible) |
| **attendus** | les résultats attendus de la réception, calculés au cadrage par le CdP, jamais là où le dev lit. | `modeles/METHODE.md` §2 |
| **réception à froid** | le CdP remesure indépendamment, sur `git archive` du commit livré : critères en deltas, diff lu contre les règles, rendus regardés. Ce que le rapport du dev dit ne se recopie jamais. | `modeles/METHODE.md` §4 |
| **relecture indépendante** | pour un lot moyen ou fort, ou qui ajoute une dépendance : un sous-agent neuf, d'un autre modèle que le dev, lit le diff et rend des constats ; le CdP les tranche à la réception. | `modeles/METHODE.md` §4 |
| **clôture** | ce que fait le CdP une fois par lot reçu : fusion en avance rapide après ta validation, registre, chantiers, commit « Lot clos », ⟨avec l'extension du miroir : miroir au projet⟩, checkpoint. | `modeles/METHODE.md` §6 |
| **livrable** | ce qui se remet ou se déploie ; dans les chantiers, le dépôt de code d'où sort la release. Un seul lot en vol par livrable. | `modeles/METHODE.md` §1 bis |
| **ressource partagée** | une machine ou un logiciel qu'un seul lot à la fois peut occuper (ta machine et son jeu) ; elle se prend comme un livrable (`ressource:`). | `modeles/METHODE.md` §1 bis |
| **version** (les deux régimes) | *déployé à chaque lot* (application en production, agent, déployeur) : la version se calcule quand le lot prend le livrable, par la règle de la méthode §1 bis (jamais `main` plus un). *Publié par release* (outil téléchargé en paquet) : le lot ne porte pas de version, sa branche est `lot/<nom du lot>`, il complète la section « Unreleased » du CHANGELOG ; la release se fait à ta demande. Une livraison = un nouveau numéro. | `modeles/METHODE.md` §1 bis, §6 ; [`modeles/depot-app/CHANGELOG.md`](modeles/depot-app/CHANGELOG.md) |

## 3 · Les vivants

| terme | ce que c'est | où il vit |
|---|---|---|
| **vivants** (documents vivants) | ce qui bouge avec le projet : méthode du projet, checkpoint, registre, plan, `chantiers.yaml`. Au dépôt des vivants ⟨, avec l'extension du miroir : et en miroir au projet claude.ai⟩ ; le CdP les écrit seul, à chaque lot clos. | `LISEZ_MOI.md` §2 et §4 ; [`modeles/depot-vivants/README.md`](modeles/depot-vivants/README.md) |
| **checkpoint** | l'état réel du projet, sous un plafond (la méthode §6) : le point d'entrée de chaque session de CdP. Un par domaine. | [`modeles/CHECKPOINT.md`](modeles/CHECKPOINT.md) |
| **ligne fixe** (ligne de reprise) | le message prêt à coller dans une conversation neuve pour reprendre un domaine ; il nomme tous les dépôts du domaine. Elle est en tête du checkpoint et au README des vivants. | `modeles/CHECKPOINT.md` ; `modeles/depot-vivants/README.md` |
| **témoin** | la ligne « Session en activité : <identifiant court> » en tête d'un checkpoint : qui travaille sur le domaine. L'identifiant court est les huit derniers caractères de l'identifiant de session. Il se juge à son silence ; le silence de la coordination ne se juge pas. | `modeles/METHODE.md` §1 bis ; `skill/SKILL.md` §4 |
| **file** | la liste de ce qui reste à faire, dans la section `## §<n> · La file` d'un checkpoint ; elle ne porte que des chantiers inscrits, cités par leur id. | `modeles/METHODE.md` §6 ; `modeles/CHECKPOINT.md` |
| **passation** | le geste par lequel un CdP passe la main à une session neuve, à la mesure du contexte ; les seuils sont à la méthode §6. Jamais avec un dev en vol. | `NOYAU.md` §4 ; `modeles/METHODE.md` §6 |
| **signe de saturation** | ce qui montre qu'un contexte est trop plein : pertes de fil, contradictions, une décision oubliée. Chaque passation note ceux qu'elle a vus (ou « aucun »). | `modeles/METHODE.md` §6 ; `modeles/CHECKPOINT.md` |
| **registre** (des arbitrages) | les décisions, numérotées R1, R2… ; une entrée tient sous son plafond (la méthode §6). | [`modeles/REGISTRE_ARBITRAGES.md`](modeles/REGISTRE_ARBITRAGES.md) |
| **numéro réservé** | un numéro de décision se prend en poussant seule la ligne « réservé » ; le push refusé, on prend le suivant. | `modeles/METHODE.md` §1 bis |
| **plan et journal** | la feuille de route, et le journal des versions : une ligne par lot clos, la seule source du fait d'un lot (dev, durée, arrêts, réception, empreinte, validation) ; ailleurs, on le cite. | [`modeles/PLAN.md`](modeles/PLAN.md) |
| **chantier** | une entrée de `chantiers.yaml` : un sujet à faire, en cours ou fini. Statuts : `a-venir`, `a-cadrer`, `en-vol` (un lot a pris le livrable), `dette`, `recette`. | `modeles/chantiers.yaml` |
| **dette** | un chantier retenu qui attend un déclencheur (« à grouper avec le prochain lot qui touche tel fichier ») ou ta présence (un accès à ta machine). | `modeles/chantiers.yaml` ; `modeles/METHODE.md` §3 |
| **recette** | le statut d'un chantier livré et validé ; le délai de la méthode §6 passé, il sort vers l'archive du mois. | `modeles/METHODE.md` §6 |
| **tableau publié** | la page `chantiers.html`, fixe et sans aucune donnée, et son fichier de données `chantiers.json` à côté, publiés ensemble au même lien. | `modeles/METHODE.md` §6 ; `modeles/generer_tableau.py` |
| **fichier de données** | `chantiers.json`, que le générateur écrit à côté de la page ; la page le lit par `fetch`. | `modeles/generer_tableau.py` ; `modeles/depot-vivants/README.md` |
| **vérificateur** | `verifier_vivants.py` : le contrôle en lecture seule des vivants partagés (douze contrôles, dont le 6, la page et ses données contre leur régénération, et le 11, les `.yaml` en YAML valide). | `modeles/verifier_vivants.py` ; `modeles/depot-vivants/README.md` |
| **fiche produit** | le checkpoint d'un produit qui a plusieurs CdP de modules : le commun (rituel, banc, circuit, pièges), jamais l'état. | `modeles/METHODE.md` §1 bis |

## 4 · Les extensions, le pont et le repli

| terme | ce que c'est | où il vit |
|---|---|---|
| **noyau** | le document qui suffit à un porteur seul avec un CdP pour démarrer, et la table des extensions. | `NOYAU.md` |
| **extension** | ce que la méthode ajoute quand un signe vécu l'appelle : les extensions de `NOYAU.md` §6, chacune avec son signe. | `NOYAU.md` §6 |
| **arbitre** | une action GitHub quotidienne, sans session : elle contrôle les vivants partagés et les checkpoints, dépose un chantier par écart nouveau, archive, tient son journal, et échoue si elle a déposé. | `LISEZ_MOI.md` §2 ter ; [`modeles/ARBITRE.md`](modeles/ARBITRE.md) |
| **contrôleur** | une session Opus neuve, chaque lundi, par tâche planifiée : elle juge la forme des documents (contradiction, oubli, doublon, historique inutile) et rend au plus cinq constats prouvés, en chantiers pour leur propriétaire. | `LISEZ_MOI.md` §2 ter ; [`modeles/CONTROLEUR.md`](modeles/CONTROLEUR.md) |
| **dépôt d'ordres** | un dépôt privé où le CdP pousse ses ordres et d'où l'exécutant serveur les tire ; il sert aussi de pont d'échange de fichiers (`transferts/`). | `LISEZ_MOI.md` §2 quater ; [`modeles/EXECUTANT_SERVEUR.md`](modeles/EXECUTANT_SERVEUR.md) §5 |
| **exécutant serveur** | un programme déterministe sur ton serveur de production : il exécute les ordres d'une liste blanche et pousse un compte rendu. Aucune IA dans le chemin du déploiement. | `modeles/EXECUTANT_SERVEUR.md` ; `modeles/METHODE.md` §4 bis |
| **exécutant local** | une session Claude Code locale sur ton PC, pilotée par fichiers ; le repli quand le pont ne donne pas ta machine. | [`modeles/EXECUTANT_LOCAL.md`](modeles/EXECUTANT_LOCAL.md) |
| **pont** | ce que l'application Claude offre à la session du CdP pour ta machine : dossiers reliés, terminal s'il est offert, écran que tu valides. | `modeles/METHODE.md` §1 ; `DEPENDANCES_CLAUDE.md` |
| **repli** (ligne de repli) | ce qui sert quand la voie normale manque : la ligne que tu colles dans une conversation neuve quand le CdP ne peut pas lancer de sous-agent ; l'exécutant local quand le pont manque ; la remise du livrable quand l'exécutant serveur est muet. | `modeles/COMMANDE_DEV.md` §B ; `modeles/EXECUTANT_LOCAL.md` |
| **mode A / B / C** | trois façons de s'organiser : A, un CdP ; B, des modules indépendants, un CdP chacun ; C, des modules liés, un CdP par domaine et une coordination. | `LISEZ_MOI.md` §2 bis, §3 ter |
