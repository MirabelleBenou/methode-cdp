# PACKAGE MÉTHODE CdP · v11
### 29 octobre 2026 · pour démarrer un nouveau projet sous la méthode CdP

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
| `modeles/ARBITRE.md` | **facultatif, mode C** — l'arbitre des vivants : une session neuve lancée chaque matin par une tâche planifiée, qui contrôle les vivants partagés et signale sans corriger ; sa procédure, son journal, la configuration de la tâche (heure, prompt, notifications), l'essai | `Methode/ARBITRE.md` du dépôt des vivants, lu par la tâche planifiée |
| `modeles/EXECUTANT_LOCAL.md` | l'exécutant Claude Code local sur le PC, piloté par fichiers (`sync\`) | sert au CdP et à l'exécutant |
| `modeles/EXECUTANT_SERVEUR.md` | **facultatif** — l'exécutant serveur : un programme déterministe sur le serveur de production, piloté par un dépôt d'ordres ; le CdP déploie sur ton « go » (guide pas à pas). **Pas de serveur de production : sautez-le** | sert au CdP et à toi, à l'installation |
| `../templates/server-runner/` (à la racine du dépôt public, non traduit) | **facultatif** — son implémentation de référence (Python, systemd, installateur, tests), en français, valeurs d'exemple | dépôt de code du projet, puis le serveur |
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

## 2 bis · Trois façons de s'organiser

```
A · UN CdP          B · MODULES INDÉPENDANTS     C · MODULES LIÉS
porteur             porteur                      porteur
   │                   │                            │
  CdP ── dev        ┌──┴─────┐                Coordinateur ── méthode,
   │               CdP-1   CdP-2                    │      domaines, arbitre
vivants + code     (chacun son dev)           ┌─────┼─────┐
                       │       │             CdP-a  CdP-b  CdP-c
                    vivants partagés         vivants partagés ;
                    en ajout seul,           livrables, ressources
                    un checkpoint chacun ;   et fichiers communs
                    code et livrables à part
```

**A — un projet, un CdP** : une application à un seul module. Un checkpoint, un témoin, aucune règle de partage à
appliquer ; le CdP tient aussi la méthode et le package. Le plus simple : y rester tant qu'un seul domaine avance à la
fois.

**B — plusieurs modules indépendants, un CdP chacun** : par exemple une application web et deux outils autonomes, chacun
son dépôt de code et sa release. Un checkpoint et un témoin par domaine ; les vivants partagés en ajout seul (registre,
plan, chantiers) ; le numéro de décision pris par un push ; pas de livrable commun, donc pas d'attente entre eux ; les
rares messages d'un domaine à l'autre passent par un chantier `pour:`. La méthode garde **un seul propriétaire** : une
session désignée (le premier CdP, ou un coordinateur dès que le projet grandit).

**C — plusieurs modules liés, un CdP par domaine et un coordinateur** : des modules qui partagent un livrable (une même
application), une ressource (ta machine), des fichiers ou un serveur. Tout ce qui est en B, plus : un seul lot en vol
par livrable et par ressource (pris par le push de l'entrée en vol ; l'autre lot `attend:`, l'étude et le pré-cadrage
restent libres) ; `touche:` pour un fichier d'un autre domaine ; **la session de coordination** ouvre et ferme les
domaines, donne les lignes fixes, tient la méthode, le prompt du dev, le package, l'outillage des vivants et l'arbitre
(le contrôle quotidien des vivants, s'il existe) ; une fiche produit quand un produit a plusieurs CdP de modules.

**Passer d'un mode à l'autre** : on commence en A ; on passe en B quand un second module indépendant démarre ; en C dès
que deux CdP partagent un livrable, une ressource ou des fichiers, ou qu'un changement transverse apparaît. Rien ne se
migre : on ajoute un checkpoint, une ligne à la table des domaines, et le coordinateur.

**L'arbitre : quand il compte.** Une session neuve, lancée chaque matin par une tâche planifiée, qui contrôle les
vivants partagés (`verifier_vivants.py`, les témoins), dépose un chantier `pour:` par écart nouveau, tient un journal
daté et résume — **elle signale, elle ne corrige rien**. **Inutile en A** : un seul CdP écrit, il voit ce qu'il écrit.
**Facultatif en B** : utile si les vivants partagés grossissent. **Recommandé en C**, dès que plusieurs CdP écrivent
les mêmes vivants le même jour : des numéros de décision en double, des chantiers en vol sans `cdp:`, un tableau
désaligné, des sessions oubliées qui gardent un témoin — ce que personne ne voit autrement, puisque chaque CdP ne lit
que son domaine. Le coordinateur l'installe et le juge avec toi après une semaine d'essai ; procédure, prompt de la
tâche et notifications : `modeles/ARBITRE.md`.

**Comment les CdP se parlent** :

| canal | ce qu'il porte | qui écrit | qui lit |
|---|---|---|---|
| chantier `pour: <CdP>` dans `chantiers.yaml` | un signalement ou une demande pour un autre domaine ; une leçon pour la méthode (`pour:` le coordinateur) | n'importe quel CdP, l'arbitre | le CdP visé, après chaque `pull` |
| entrée `en-vol` (`cdp:`, `livrable:`, `ressource:`, `attend:`) | qui tient quel livrable ou quelle ressource | le CdP qui prend, par un push | tous, avant de cadrer |
| registre des décisions | les décisions, numéro réservé par un push | le CdP qui clôt | tous |
| témoin du checkpoint | qui est en activité sur un domaine | la session qui reprend, par un push | le coordinateur, toi, l'arbitre |
| journal de l'arbitre (`Methode/ARBITRE_JOURNAL.md`) | une ligne datée par passage, même sans écart : la preuve qu'il a tourné | l'arbitre, en ajout seul | le coordinateur, toi |
| message prêt à coller | un changement de méthode qui touche un CdP en activité | le coordinateur | toi, qui le colles au CdP ; il vérifie ensuite son chantier `pour:` |
| **jamais** | un message que tu relaies de mémoire, ni un texte de reprise qui voyage hors du dépôt | — | — |

En A, aucun de ces canaux n'est nécessaire ; en B, les chantiers `pour:` et le registre suffisent ; en C, tous.

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
se déploie — sauf si le projet a un exécutant serveur (`modeles/EXECUTANT_SERVEUR.md`) : tu dis alors « go » en nommant
l'action, le CdP déploie, tu valides à l'écran ; la remise du livrable ne sert plus qu'en repli.

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
- **le livrable** : zip de déploiement, fichier HTML unique, PDF, archive d'un agent… et où il se dépose — ou, s'il
  tourne sur un serveur de production que tu administres, comment il s'y déploie (l'exécutant serveur, facultatif) ;
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
v9, le 27 octobre 2026 — une ressource partagée (la machine du porteur et son jeu) se prend comme un livrable ;
un lot sans release ne porte pas de livrable ; la synthèse de fin de discussion ; le contrôle 8 compte les ressources.
v10, le 28 octobre 2026 — l'exécutant serveur : un programme déterministe sur le serveur de production tire ses
ordres d'un dépôt privé, le CdP déploie sur le go du porteur, la remise devient le repli ; guide et implémentation
de référence facultatifs ; la question du serveur à l'amorçage ; trois façons de s'organiser (§2 bis).
v11, le 29 octobre 2026 — l'arbitre des vivants : rôle, quand il compte, configuration de la tâche planifiée,
journal, notifications ; la ligne fixe nomme tous les dépôts du domaine ; le témoin se juge à son silence.
