# PACKAGE MÉTHODE CdP · v8
### 27 octobre 2026 · pour démarrer un nouveau projet sous la méthode CdP

*Ce package reproduit une façon de travailler éprouvée lot après lot : un **chef de projet** (CdP, Opus) qui décide
avec toi, cadre, lance le dev et réceptionne ; un **dev** (Sonnet par défaut) qui construit un lot à la fois ; **toi**,
qui décides et valides à l'écran. Tout circule par GitHub ; tu ne téléverses rien et tu ne lances aucune commande.*

**Le porteur**, dans les modèles et la skill, c'est toi : la personne qui décide et valide. Ce qui est entre `<…>` ou
`⟨…⟩` est à remplir — le CdP le fait à l'amorçage, sauf la skill, que tu personnalises toi-même (§1 et §8).

---

## 1 · Ce qu'il y a dans le package

| fichier | sert à | où il finit |
|---|---|---|
| `LISEZ_MOI.md` | ce mode d'emploi | nulle part, c'est pour toi |
| `1_INSTRUCTIONS_PROJET.md` | le texte à coller dans **les instructions du projet claude.ai** | instructions du projet |
| `2_PROMPT_AMORCAGE_CDP.md` | le **premier message** de la première session de CdP | collé dans une conversation |
| `3_GITHUB.md` | les dépôts, leur structure, le circuit d'un lot, les pièges | lu par le CdP à l'amorçage |
| `modeles/METHODE.md` | la méthode générique, à adapter | `Methode/METHODE_<P>.md` du dépôt des vivants, miroir au projet |
| `modeles/PROMPT_DEV.md` | la commande permanente du dev | racine du dépôt de code, miroir au projet |
| `modeles/CADRAGE.md` | le modèle d'un cadrage de lot | sert au CdP, **jamais cité** par un cadrage |
| `modeles/LOT_FICHIERS.md` | addendum, arrêt, rapport du dev | sert au CdP et au dev |
| `modeles/COMMANDE_DEV.md` | la commande du sous-agent dev, et la ligne de repli | sert au CdP |
| `modeles/CHECKPOINT.md` | l'état courant, point d'entrée de chaque session | dépôt des vivants, miroir au projet |
| `modeles/REGISTRE_ARBITRAGES.md` | les décisions, numérotées R1, R2… | dépôt des vivants, miroir au projet |
| `modeles/PLAN.md` | la feuille de route et le journal des versions | dépôt des vivants, miroir au projet |
| `modeles/chantiers.yaml` | la source unique des chantiers (à venir, dettes, livrés) | dépôt des vivants, miroir au projet |
| `modeles/contexte.py` | mesure le contexte de la session du CdP : prévenir à 600 000 jetons, passer la main à 700 000 | `outils_cdp/` du dépôt des vivants |
| `modeles/generer_tableau.py` | fabrique `chantiers.html`, la page lisible des chantiers, à chaque écriture du yaml | dépôt des vivants, miroir au projet |
| `modeles/verifier_vivants.py` | contrôle les vivants partagés (numéros de décision, chantiers, versions réservées, chantiers en vol, tableau, journal) quand plusieurs CdP y écrivent ; lecture seule | dépôt des vivants, lancé par le coordinateur et l'arbitre |
| `modeles/EXECUTANT_LOCAL.md` | l'exécutant Claude Code local sur le PC, piloté par fichiers (`sync\`) | sert au CdP et à l'exécutant |
| `modeles/depot-vivants/` | `README.md` du dépôt des vivants | dépôt des vivants |
| `modeles/depot-app/` | `.gitattributes`, `.gitignore`, `CHANGELOG.md` du dépôt de code | dépôt de code |
| `skill/SKILL.md` | la skill personnelle `methode-cdp`, **à personnaliser (§1 et §8) puis installer** | tes skills claude.ai |

---

## 2 · L'architecture : trois couches, du plus général au plus précis

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 1. SKILL PERSONNELLE  methode-cdp          (ton compte, tous les projets) │
│    Qui tu es, les rôles, la posture, le circuit GitHub générique.         │
│    → Change rarement. Mise à jour quand la méthode évolue.                │
├──────────────────────────────────────────────────────────────────────────┤
│ 2. INSTRUCTIONS DU PROJET                  (un projet claude.ai)          │
│    Ton profil pour ce projet, ce que tu attends, OÙ sont les vivants,     │
│    QUELS dépôts. Une dizaine de lignes, des pointeurs, pas de règles.     │
│    → Change quand un dépôt ou un document de référence change de nom.     │
├──────────────────────────────────────────────────────────────────────────┤
│ 3. DOCUMENTS VIVANTS + DÉPÔTS              (le projet lui-même)           │
│    METHODE_<P> (prime sur la skill), PROMPT_DEV_<P>, CHECKPOINT,          │
│    REGISTRE, PLAN, chantiers.yaml ; le code et lots/ au dépôt de code.    │
│    → Change à chaque lot clos, par le CdP seul.                           │
└──────────────────────────────────────────────────────────────────────────┘
```

**Règle de précédence** : la méthode du projet prime sur la skill ; le cadrage d'un lot prime sur le prompt du dev pour
ce que fait le lot ; tes décisions au registre priment sur tout.

**Pourquoi trois couches** : la skill t'évite de réexpliquer la collaboration à chaque projet ; les instructions restent
courtes pour ne pas dériver ; les vivants portent ce qui bouge, sous des noms stables, versionnés par git.

**Ce qui ne va pas dans la mémoire de Claude** : la méthode et l'état du projet. La mémoire retient des faits sur toi ;
elle ne remplace pas un document versionné qu'un dev neuf peut lire.

---

## 3 · Démarrer un nouveau projet — tes gestes, dans l'ordre

1. **Sur GitHub, crée deux dépôts privés vides** (sans README) :
   - `<Projet>` — les vivants (méthode, checkpoint, registre, plan, chantiers) ;
   - `<Projet>-App` — le code.
   *Code public (GitHub Pages, licence ouverte) : crée aussi `<Projet>-Lots`, privé — le prompt du dev et les dossiers
   de lots y vont, jamais au dépôt public (`3_GITHUB.md` §6 B).*
2. **Sur claude.ai, crée le projet** et colle dans ses instructions le texte de `1_INSTRUCTIONS_PROJET.md`, une fois
   les `<…>` remplis.
3. **Installe la skill `methode-cdp`** : personnalise d'abord ses §1 et §8 (ce sont eux qui te décrivent : ton
   profil, tes contraintes de poste), puis crée-la dans tes skills claude.ai avec le contenu de `skill/SKILL.md`.
4. **Mets le package à la portée de la première session** — au choix :
   - (recommandé) le CdP le lit lui-même au dépôt public `MirabelleBenou/methode-cdp` (dossier `fr/`), en lecture :
     rien à téléverser ;
   - ou tu téléverses le zip dans la première conversation.
5. **Ouvre une conversation avec Opus dans le projet** et colle `2_PROMPT_AMORCAGE_CDP.md`, complété de ce que tu veux
   construire.
6. **Réponds aux questions du CdP** (options numérotées, une recommandation à chaque fois). Il initialise les deux
   dépôts, écrit la méthode et le prompt du dev du projet, les premiers vivants, et les recopie en miroir au projet.

Ensuite, tu ne parles qu'au CdP. Tes seuls gestes manuels restants : **valider à l'écran**, poser **les tags et les
releases**, **supprimer les branches fusionnées** sur GitHub (une session ne peut pas), et déposer le livrable là où il
se déploie.

---

## 4 · Ce qui va où

| élément | lieu de référence | miroir au projet ? | qui écrit | quand |
|---|---|---|---|---|
| Méthode du projet | dépôt des vivants `Methode/` | oui | CdP | à une version, après un lot qui l'a prise en défaut |
| Prompt du dev | racine du dépôt de code — **dépôt `<Projet>-Lots` si le code est public** | oui | CdP | à une version |
| Checkpoint | dépôt des vivants | oui | CdP | à chaque passation |
| Registre des arbitrages | dépôt des vivants | oui | CdP | à chaque lot clos |
| Plan + journal | dépôt des vivants | oui | CdP | à chaque lot qui prend une version |
| `chantiers.yaml` et `chantiers.html` | dépôt des vivants | oui, et la page en artefact | CdP | à chaque écriture du yaml |
| Attendus de réception | dépôt des vivants `attendus/<version>/` | non | CdP | au cadrage |
| Scripts jetables du CdP | dépôt des vivants `outils_cdp/` | non | CdP | au besoin |
| Code, banc, `CHANGELOG` | dépôt de code | non | dev | dans un lot |
| Cadrage, addenda, arrêts, rapport, maquette | dépôt de code `lots/<version>/` — **dépôt `<Projet>-Lots` si le code est public** | **non** | CdP (cadrage, addenda), dev (arrêts, rapport) | pendant le lot |
| Specs, guide de style, études | projet, écrits une fois | — | CdP | une fois, jamais réécrits |
| Données de production, journaux | **aucun dépôt** | non | toi | téléversés dans la session qui en a besoin |
| Images (tuiles, visuels) | **dans la discussion** | jamais | toi | l'import au projet les corrompt sans prévenir |

**Le projet claude.ai ne porte que** les miroirs des vivants (recopiés par le CdP à chaque clôture, depuis son clone)
et les références écrites une fois, rangés en dossiers par thème (`Methode/`, `<SousProjet>/`, `Archives/`…).

---

## 5 · Ce qui est générique, ce qui est à adapter

**Générique, à garder tel quel** : les rôles ; le cycle d'un lot ; le cadrage autoportant ; les critères en deltas,
mesurés sur l'archive livrée ; les arrêts du dev ; la réception à froid ; le CdP qui regarde lui-même les rendus ;
les vivants au dépôt et leur miroir ; la fusion en avance rapide après ta validation ; les pièges des sessions.

**À adapter au premier lot du projet** (le CdP te le demande à l'amorçage) :
- **le banc** : l'outillage qui mesure une archive (compte de fichiers, tests, lint, i18n, CSS, empreintes) ;
- **les portes** du dev (P0 à Pn) et ce qu'il ne touche jamais ;
- **le versionnage** : qui fait monter la version, de combien, avec ton accord ou pré-autorisé ;
- **le livrable** : zip de déploiement, fichier HTML unique, PDF, archive d'un agent… et où il se dépose ;
- **la preuve propre au type de projet** : rebuild à l'octet pour un HTML buildé, tests et migration pour une app,
  rejeu pour un moteur de calcul, contrôles par le DOM pour une page.

**Le banc se construit par un lot d'outillage**, cadré court par le CdP et construit par le dev — jamais par le CdP.

---

## 6 · Les coûts à attendre (mesurés sur un premier projet)

- un lot ordinaire : 5 à 20 minutes de dev, quelques minutes de réception ;
- un écran avec maquette du CdP : 15 minutes à 1 h 30 de dev, une ou deux passes de maquette avec toi ;
- un addendum lancé par le CdP : quelques minutes, sans un geste de ta part ;
- une session de CdP : passer la main avant ~700 000 jetons de contexte, ou à une fin de file naturelle.

*Un sous-agent dev consomme le crédit de la session du CdP. Le premier projet coûte un lot d'outillage (le banc) avant
le premier lot de produit.*

---

## 7 · Faire vivre le package

- **La source est le dépôt public `MirabelleBenou/methode-cdp`** — ou ta copie, si tu fais évoluer la méthode pour
  toi (un fork, ou un dépôt privé où tu la pousses) ; la skill `methode-cdp` en est la copie installée
  (`skill/SKILL.md` fait foi).
- **Quand la méthode d'un projet change de version sur une leçon générique** (elle vaudrait pour tout projet), le CdP
  de ce projet la reporte ici — modèles, `3_GITHUB.md`, skill — dans un commit « Package vN : … », te le dit, et te
  propose la skill mise à jour. Une leçon propre au projet reste dans sa méthode.
- **Un projet déjà amorcé ne se réaligne pas tout seul** : sa méthode prime ; son CdP reprend une évolution du package
  à sa prochaine version de méthode, s'il y a lieu.
- Version du package dans l'en-tête de ce fichier ; l'historique dans git ; ni tag ni release nécessaires.
- **Les modèles et la skill restent génériques** : aucun nom de projet, aucun numéro d'arbitrage d'un projet.

**Historique** : v1, le 23 octobre 2026. v2, le 26 octobre 2026 — le tableau des chantiers régénéré à chaque
écriture ; un dépôt `-Lots` privé quand le code est public ; l'exécutant local (Claude Code sur le PC, piloté
par fichiers) ; la passation mesurée (prévenir à 600 000 jetons, passer la main à 700 000). v3 — un seul dépôt de
lots pour une suite de plusieurs dépôts de code, préfixe de module dans le nom des lots. v4 — un texte à coller se
remet prêt, sans champ à remplir. v5 — la version publique. v6, le 27 octobre 2026 — plusieurs CdP en même temps
(un checkpoint et un témoin par domaine, numéros et versions réservés par un push, ajout seul, totaux calculés,
messages par chantier) ; la passation sans prompt de reprise, par une ligne fixe par domaine ; le coordinateur.
v7, le 27 octobre 2026 — une livraison = un nouveau numéro, partout : l'addendum ne sert que tant que rien n'a été
remis ni déployé ; le coordinateur cadre l'outillage de la méthode et des vivants ; `verifier_vivants.py`.
v8, le 27 octobre 2026 — un livrable, un seul lot en vol : un autre lot du même livrable est suspendu jusqu'à la
validation et la fusion du premier ; personne n'annonce une version à l'avance, elle se calcule quand le lot prend
le livrable ; le contrôle « livrables » de `verifier_vivants.py`.
