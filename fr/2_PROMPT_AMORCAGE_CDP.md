# PROMPT D'AMORÇAGE — le premier message de la première session de CdP

*À coller dans une conversation neuve **avec Opus**, dans le projet claude.ai, une fois les deux dépôts créés vides sur
GitHub et les instructions du projet posées. Remplace les `<…>`. Le CdP fait tout le reste : tu réponds à ses
questions.*

---

## A · Projet neuf

```
Tu es le chef de projet (CdP) de ce projet, sous la méthode CdP (skill methode-cdp, à lire d'abord).

Le package méthode est au dépôt public MirabelleBenou/methode-cdp, dossier fr/ : rattache-le en lecture (add_repo) et clone-le <ou : il est joint à ce message, en zip>. Lis LISEZ_MOI.md, 3_GITHUB.md, puis les modèles.

Les deux dépôts sont créés et vides : <owner>/<Projet> (vivants, privé) et <owner>/<Projet>-App (code, privé). <Code public : et <owner>/<Projet>-Lots (privé, prompt du dev et lots).> Rattache-les (add_repo, accès push), un clone à la fois.

Ce que je veux construire : <description : le produit, les utilisateurs, la stack si tu as une préférence, les contraintes (hors ligne, hébergement, public ou privé), ce que tu as déjà>.

Amorce le projet :
1. Pose-moi, en options numérotées avec ta recommandation, les questions qui décident de la méthode du projet : le type de livrable et où il se déploie — y a-t-il un serveur de production que j'administre (une VM, un serveur dédié) ? si oui, oriente vers l'exécutant serveur (modeles/EXECUTANT_SERVEUR.md : dépôt d'ordres, déploiement sur mon go) plutôt que vers la remise de fichiers, et dis-moi le dépôt d'ordres à créer —, si le code est public (s'il l'est et que le dépôt des lots manque, arrête-toi et demande-le-moi), le versionnage (qui le fait monter, avec mon accord ou pré-autorisé), la stack, ce que le banc devra mesurer. Une seule série de questions, puis tu tranches le reste et tu me le dis.
2. Initialise le dépôt des vivants : README, Methode/METHODE_<P>.md tiré du modèle (générique gardé, spécifique rempli), <Dossier>/CHECKPOINT_<P>.md, REGISTRE_ARBITRAGES_<P>.md (R1 : l'adoption de la méthode et mes réponses), PLAN_<P>.md, chantiers.yaml (le banc en premier chantier, puis les premiers lots) avec generer_tableau.py copié du package et chantiers.html qu'il produit — publie-le en artefact et donne-le-moi en fichier —, attendus/ et outils_cdp/ vides.
3. Initialise le dépôt de code : .gitattributes (export-ignore de banc/, lots/, du prompt du dev et de lui-même), .gitignore, CHANGELOG.md, PROMPT_DEV_<P>.md tiré du modèle — au dépôt des lots si le code est public, jamais au dépôt public —, et le squelette de l'application si la stack est décidée — par un premier lot du dev, pas par toi.
4. Recopie au projet claude.ai, en miroir, chaque vivant et le prompt du dev (project_write avec local_path depuis ton clone, dans leurs dossiers).
5. Redonne-moi le texte complet des instructions du projet, à coller.
6. Propose-moi le premier lot : en général le banc (lot d'outillage), puis le premier lot de produit.

Dis-moi à la fin ce que tu as écrit : dépôt, commit, chemin.
```

---

## B · Projet existant (du code existe déjà, en zip ou ailleurs)

*Même message, en remplaçant le point 3 par :*

```
3. Le code existant est <joint en zip | au dépôt X>. Fais-en le premier commit du dépôt de code, tel quel, à l'octet : vérifie qu'aucun secret n'y entre (.env, jetons), que le .gitignore n'écarte aucun fichier livré, puis prouve que `git archive` de ce commit égale l'archive d'origine (contenu et modes). Ajoute ensuite .gitattributes, CHANGELOG.md s'il manque, et PROMPT_DEV_<P>.md, dans un second commit.
   Mesure la base (fichiers, tests, lint) : ce sera le bloc « base » du premier cadrage.
```

---

## C · Reprendre un projet déjà sous la méthode (session de CdP suivante)

*Pas besoin de ce fichier : colle la ligne fixe du domaine, que donne le CdP à chaque passation et que porte le README
des vivants — « Tu es Opus-CdP-<Domaine>. Reprends : rattache `<owner>/<Projet>` (accès push), fais git pull, lis
`<checkpoint du domaine>` en entier (§0 d'abord) et suis-le. » Rien à téléverser.*
