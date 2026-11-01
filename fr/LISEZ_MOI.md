# PACKAGE MÉTHODE CdP · v20
### 1er novembre 2026 · pour démarrer un nouveau projet sous la méthode CdP

*Ce package reproduit une façon de travailler éprouvée lot après lot : un **chef de projet** (CdP, Opus) qui décide
avec toi, cadre, lance le dev et réceptionne ; un **dev** qui construit un lot à la fois ; **toi**,
qui décides et valides à l'écran. Tout circule par GitHub ; tu ne téléverses rien et tu ne lances aucune commande.*

**Par où commencer** : si tu démarres seul avec un CdP, lis d'abord **[`NOYAU.md`](NOYAU.md)** — il se suffit pour démarrer, avec en
dernier la table des extensions (ce que tu n'installes que le jour où le signe vécu se produit). Le reste de ce guide
s'ajoute au noyau, il ne le précède pas. **Les termes** de la méthode sont au **[`GLOSSAIRE.md`](GLOSSAIRE.md)** ; **ce que la méthode
suppose du produit Claude**, et le repli quand une fonction change, à **[`DEPENDANCES_CLAUDE.md`](DEPENDANCES_CLAUDE.md)**. **La méthode a été
éprouvée sur trois projets, dont un complexe** (plusieurs CdP en parallèle sur plusieurs produits, un serveur de
production).

**Le porteur**, dans les modèles et la skill, c'est toi : la personne qui décide et valide. Ce qui est entre `<…>` ou
`⟨…⟩` est à remplir — le CdP le fait à l'amorçage, sauf la skill, que tu personnalises toi-même (§1 et §8).

---

## 1 · Ce qu'il y a dans le package

| fichier | sert à | où il finit |
|---|---|---|
| `LISEZ_MOI.md` | ce mode d'emploi | nulle part, c'est pour toi |
| `NOYAU.md` | **à lire en premier** : la méthode d'un porteur seul avec un CdP (mode A), qui se suffit pour démarrer — rôles, couches et gestes de démarrage, cycle d'un lot, checkpoint et passation, ce qui ne pardonne pas — et la table des extensions | nulle part, c'est pour toi |
| `GLOSSAIRE.md` | chaque terme de la méthode, une ou deux lignes et le document où il vit | nulle part, c'est pour toi |
| `DEPENDANCES_CLAUDE.md` | ce que la méthode suppose du produit Claude, ce qui casse si une fonction change, le repli ; **relevé daté, à relire à chaque version** | nulle part, c'est pour toi |
| [`1_INSTRUCTIONS_PROJET.md`](1_INSTRUCTIONS_PROJET.md) | le texte à coller dans **les instructions du projet claude.ai** | instructions du projet |
| [`2_PROMPT_AMORCAGE_CDP.md`](2_PROMPT_AMORCAGE_CDP.md) | le **premier message** de la première session de CdP ; §D, celui qui ouvre la coordination | collé dans une conversation |
| [`3_GITHUB.md`](3_GITHUB.md) | les dépôts, leur structure, le circuit d'un lot, les pièges | lu par le CdP quand une question l'exige |
| [`modeles/METHODE.md`](modeles/METHODE.md) | la méthode générique, à adapter ; **la seule source des chiffres de la méthode** (§6) | `Methode/METHODE_<P>.md` du dépôt des vivants |
| [`modeles/PROMPT_DEV.md`](modeles/PROMPT_DEV.md) | la commande permanente du dev | racine du dépôt de code |
| [`modeles/CADRAGE.md`](modeles/CADRAGE.md) | le modèle d'un cadrage de lot, et sa forme courte pour un lot de complexité faible | sert au CdP, **jamais cité** par un cadrage |
| [`modeles/LOT_FICHIERS.md`](modeles/LOT_FICHIERS.md) | addendum, arrêt, rapport du dev | sert au CdP et au dev |
| [`modeles/COMMANDE_DEV.md`](modeles/COMMANDE_DEV.md) | la commande du sous-agent dev, et la ligne de repli | sert au CdP |
| [`modeles/CHECKPOINT.md`](modeles/CHECKPOINT.md) | l'état courant, point d'entrée de chaque session | dépôt des vivants |
| [`modeles/REGISTRE_ARBITRAGES.md`](modeles/REGISTRE_ARBITRAGES.md) | les décisions, numérotées R1, R2… | dépôt des vivants |
| [`modeles/PLAN.md`](modeles/PLAN.md) | la feuille de route, et le journal des versions : la seule source du fait d'un lot | dépôt des vivants |
| `modeles/chantiers.yaml` | la source unique des chantiers | dépôt des vivants |
| `modeles/contexte.py` | mesure le contexte de la session du CdP, pour décider la passation (seuils : méthode §6) | `outils_cdp/` du dépôt des vivants |
| `modeles/generer_tableau.py` | **extension « tableau publié »** — la page `chantiers.html` et son fichier de données `chantiers.json` | dépôt des vivants |
| `modeles/verifier_vivants.py` | contrôle les vivants en lecture seule — douze contrôles, décrits dans sa docstring | dépôt des vivants |
| `modeles/archiver_chantiers.py` | sort les chantiers en recette vers l'archive du mois (délai : méthode §6) ; `chercher`, `normaliser` | dépôt des vivants |
| `modeles/domaines.yaml` | **modes B et C** — la table des domaines que lit le contrôle 9 | `Methode/domaines.yaml` du dépôt des vivants |
| [`modeles/ARBITRE.md`](modeles/ARBITRE.md), `modeles/arbitre.py`, `modeles/depot-vivants/arbitre.yml` | **facultatif, mode C** — l'arbitre des vivants, une action GitHub quotidienne | `Methode/` et `.github/workflows/` du dépôt des vivants |
| [`modeles/CONTROLEUR.md`](modeles/CONTROLEUR.md) | **facultatif, mode C** — le contrôleur, une session hebdomadaire qui juge la forme des documents | `Methode/CONTROLEUR.md` du dépôt des vivants |
| [`modeles/EXECUTANT_LOCAL.md`](modeles/EXECUTANT_LOCAL.md) | **le repli** — l'exécutant local sur le PC, quand le pont ne donne pas ta machine | sert au CdP et à l'exécutant |
| [`modeles/EXECUTANT_SERVEUR.md`](modeles/EXECUTANT_SERVEUR.md) | **facultatif** — l'exécutant serveur et le dépôt d'ordres (§2 quater). **Pas de serveur de production : saute-le** | sert au CdP et à toi, à l'installation |
| `../templates/server-runner/` (à la racine du dépôt public, non traduit) | **facultatif** — son implémentation de référence (Python, systemd, installateur, tests), en français | dépôt de code du projet, puis le serveur |
| `modeles/depot-vivants/` | [`README.md`](modeles/depot-vivants/README.md) du dépôt des vivants | dépôt des vivants |
| `modeles/depot-app/` | `.gitattributes`, `.gitignore`, [`CHANGELOG.md`](modeles/depot-app/CHANGELOG.md) du dépôt de code | dépôt de code |
| [`skill/SKILL.md`](skill/SKILL.md) | la skill personnelle `methode-cdp`, **à personnaliser (§1 et §8) puis installer** — **v19** : ce qu'une session sait avant de lire la méthode du projet | tes skills claude.ai |

**L'outillage** : les scripts n'emploient que la bibliothèque standard de Python et sont testés en CI. Deux tests gardent
les documents : `modeles/tests/test_liens.py` (chaque lien relatif mène à un fichier qui existe) et
`modeles/tests/test_parite.py` (chaque chiffre de la méthode n'est écrit qu'à sa source, et chaque document français a
les mêmes titres que son pendant anglais).

---

## 2 · L'architecture : trois couches, du plus général au plus précis

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 1. SKILL PERSONNELLE  methode-cdp          (ton compte, tous les projets) │
│    Qui tu es, les rôles, la posture, le démarrage d'une session.          │
│    → Change rarement. Mise à jour quand la méthode évolue.                │
├──────────────────────────────────────────────────────────────────────────┤
│ 2. INSTRUCTIONS DU PROJET                  (un projet claude.ai)          │
│    Ton profil pour ce projet, ce que tu attends, OÙ sont les vivants,     │
│    QUELS dépôts. Une dizaine de lignes, des pointeurs, pas de règles.     │
│    → Change quand un dépôt ou un document de référence change de nom.     │
├──────────────────────────────────────────────────────────────────────────┤
│ 3. DOCUMENTS VIVANTS + DÉPÔTS              (le projet lui-même)           │
│    METHODE_<P> (prime sur la skill), CHECKPOINT, REGISTRE, PLAN,          │
│    chantiers.yaml ; le code, PROMPT_DEV_<P> et lots/ au dépôt de code.    │
│    → Change à chaque lot clos, par le CdP seul.                           │
└──────────────────────────────────────────────────────────────────────────┘
```

**Règle de précédence** : tes décisions au registre priment sur tout ; la méthode du projet prime sur la skill ; pour un dev,
les conditions pratiques de sa commande priment sur le cadrage et sur le prompt du dev, et le cadrage prime sur le prompt
pour ce que fait le lot.

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
rares messages d'un domaine à l'autre passent par un chantier `pour:`. **Sans coordination, la méthode, le prompt du dev et
le README des vivants gardent un seul propriétaire** : le premier CdP, ou un coordinateur dès que le projet grandit.

**C — plusieurs modules liés, un CdP par domaine et un coordinateur** : des modules qui partagent un livrable (une même
application), une ressource (ta machine), des fichiers ou un serveur. Tout ce qui est en B, plus : un seul lot en vol
par livrable et par ressource (pris par le push de l'entrée en vol ; l'autre lot `attend:`, l'étude et le pré-cadrage
restent libres) ; `touche:` pour un fichier d'un autre domaine ; **la session de coordination** ouvre et ferme les
domaines, donne les lignes fixes, tient la méthode, le prompt du dev, le package, l'outillage des vivants, l'arbitre et le
contrôleur (s'ils existent) ; une fiche produit quand un produit a plusieurs CdP de modules.

**Passer d'un mode à l'autre** : on commence en A ; on passe en B quand un second module indépendant démarre ; en C dès
que deux CdP partagent un livrable, une ressource ou des fichiers, ou qu'un changement transverse apparaît. Rien ne se
migre : on ajoute un checkpoint, une ligne à la table des domaines, et le coordinateur. **Démarrer à plusieurs CdP :
§3 bis ; passer d'un mode à l'autre en cours de route (A → B, B → C, A → C, et le retour) : §3 ter.**

**L'arbitre et le contrôleur des vivants** : deux gardes, inutiles en A, facultatives en B, recommandées en C. L'arbitre est
une action GitHub quotidienne qui mesure ; le contrôleur, une session hebdomadaire qui juge (§2 ter). **Qui archive** les
chantiers en recette : l'arbitre, s'il existe ; sans lui (modes A et B), le CdP ou le coordinateur lance
`archiver_chantiers.py` à sa clôture.

**Trois choses que la méthode fixe pour que les outils s'y retrouvent.** *Le témoin* : l'identifiant court d'une session est
les huit derniers caractères de son identifiant de session (celui de la ligne d'attribution de ses commits) ; toutes les
sessions d'un même compte en partagent le début ; un témoin se juge à son silence, **sauf celui de la coordination**, que
tu gardes ouverte des jours sans commit. *La file* : chaque checkpoint la porte sous un titre stable
`## §<n> · La file`, avec la liste elle-même ; la table des domaines nomme ce titre, une ligne `file:` vide est un trou, et la
coordination y a sa propre entrée. *Ta machine* : quand le projet pilote un jeu ou une application sur ton PC, la session du
CdP s'en sert **par le pont de l'application Claude** (dossiers reliés, terminal s'il est offert, écran que tu valides) ;
l'exécutant local n'est plus que le repli, et un chantier qui a besoin de la machine reste en dette tant que tu n'y es pas.

**Comment les CdP se parlent** :

| canal | ce qu'il porte | qui écrit | qui lit |
|---|---|---|---|
| chantier `pour: <CdP>` dans `chantiers.yaml` | un signalement ou une demande pour un autre domaine ; une leçon pour la méthode (`pour:` le coordinateur) | n'importe quel CdP, l'arbitre, le contrôleur | le CdP visé, après chaque `pull` |
| entrée `en-vol` (`cdp:`, `livrable:`, `ressource:`, `attend:`) | qui tient quel livrable ou quelle ressource | le CdP qui prend, par un push | tous, avant de cadrer |
| registre des décisions | les décisions, numéro réservé par un push | le CdP qui clôt | tous |
| témoin du checkpoint | qui est en activité sur un domaine | la session qui reprend, par un push | le coordinateur, toi, l'arbitre |
| journaux de l'arbitre et du contrôleur (`Methode/ARBITRE_JOURNAL.md`, `Methode/CONTROLEUR_JOURNAL.md`) | une ligne datée par passage, même sans écart : la preuve qu'ils ont tourné | l'arbitre, le contrôleur, en ajout seul | le coordinateur, toi |
| message prêt à coller | un changement de méthode qui touche un CdP en activité (au témoin libre : un chantier `pour:`) | le coordinateur | toi, qui le colles au CdP ; le coordinateur vérifie ensuite sa réponse sur le dépôt |
| **jamais** | un message que tu relaies de mémoire, ni un texte de reprise qui voyage hors du dépôt | — | — |

En A, aucun de ces canaux n'est nécessaire ; en B, les chantiers `pour:` et le registre suffisent ; en C, tous.

---

## 2 ter · L'arbitre et le contrôleur des vivants

*Deux gardes, inutiles en A, facultatives en B, recommandées en C. Leurs modèles répondent seuls à « pourquoi, quand,
combien, comment » : [`modeles/ARBITRE.md`](modeles/ARBITRE.md) §0 et [`modeles/CONTROLEUR.md`](modeles/CONTROLEUR.md).*

- **L'arbitre mesure, chaque jour** : une action GitHub, sans session, qui lance le vérificateur, dépose un chantier
  `pour:` par écart nouveau, archive et tient son journal ; elle échoue quand elle a déposé, et l'e-mail de GitHub te
  prévient. **Son signe** : le premier numéro de décision en double, ou la première session oubliée qui garde un témoin.
- **Le contrôleur juge, chaque lundi** : une session Opus neuve, par tâche planifiée (approbation automatique), qui rend
  au plus cinq constats prouvés sur la forme des documents. **Son signe** : le premier document qui enfle ou se contredit
  sans que personne le dise.
- **Ni l'un ni l'autre ne corrige** : le propriétaire corrige.

---

## 2 quater · Le dépôt d'ordres, pont d'échange de fichiers

*Seulement avec un exécutant serveur ([`modeles/EXECUTANT_SERVEUR.md`](modeles/EXECUTANT_SERVEUR.md)) : sinon, saute
cette section. Le détail — le circuit, les limites, le pourquoi — est au guide de l'exécutant serveur, §3 point 9, §5,
§12 et §13.*

**Le signe** : une donnée produite en session (un paquet de pages rendues, des tuiles) doit arriver sur le serveur, et
tu ne veux pas la déposer à la main. **La règle** : le dépôt d'ordres sert aussi de pont, par un dossier `transferts/` —
aucun dépôt ni clé de plus ; jamais l'historique d'un dépôt de code public.

| la donnée est… | elle arrive par | état |
|---|---|---|
| **produite dans une session** | `transferts/<domaine>/<édition>/` du dépôt d'ordres, puis un ordre `fichiers` | **à venir** (`EXECUTANT_SERVEUR.md` §13) |
| **produite sur ton PC** | `rsync` vers `entree/` du serveur, puis un ordre `fichiers` | en service |
| **publiée ailleurs** | un ordre `fichiers` : `telecharger` | en service |

Le dev ne lit ni n'écrit jamais ce dépôt ; le CdP n'en garde un clone que le temps de déployer (`modeles/METHODE.md` §4 bis).

---

## 3 · Démarrer un nouveau projet — tes gestes, dans l'ordre

**Tes gestes sont au [`NOYAU.md`](NOYAU.md) §2** : les dépôts vides à créer et à protéger, les instructions du projet,
la skill à personnaliser, le prompt d'amorçage. Ce qui s'y ajoute :
- **le code est public** : crée aussi `<Projet>-Lots`, privé ([`3_GITHUB.md`](3_GITHUB.md) §6 B) ; **sur un compte
  gratuit**, ce que la protection de `main` devient : `3_GITHUB.md` §5 ;
- **le package à la portée de la première session** : le CdP le lit lui-même au dépôt public `MirabelleBenou/methode-cdp`
  (dossier `fr/`), en lecture — rien à téléverser ; ou tu joins le zip à la première conversation.

Ensuite, tu ne parles qu'au CdP. Tes seuls gestes manuels restants : **valider à l'écran**, poser **les tags et les
releases**, **supprimer les branches fusionnées** sur GitHub (une session ne peut pas), et déposer le livrable là où il
se déploie — sauf si le projet a un exécutant serveur : tu dis alors « go » en nommant l'action, le CdP déploie.

## 3 bis · Plusieurs CdP — démarrer en B ou en C, ou y passer

*Le §3 démarre un projet à un seul CdP (mode A, §2 bis). Un projet à plusieurs modules démarre de la même façon, puis
on ajoute les domaines un par un : rien ne se migre, on ajoute.*

**Tes gestes, dans l'ordre :**

1. **Démarre en A (§3) avec le premier module**, même si tu sais déjà qu'il y en aura plusieurs. Dis-le au premier CdP
   dès l'amorçage (« d'autres modules viendront : <lesquels> ») : il nomme son domaine et son checkpoint en conséquence
   (`Opus-CdP-<Produit>[-<Module>]`, `<Dossier>/CHECKPOINT_<…>.md`) et ouvre la table des domaines (méthode §1 bis,
   README des vivants). Les vivants communs — méthode, registre, plan, `chantiers.yaml` — servent ensuite à tous.
2. **Pour chaque module de plus (mode B)** :
   - sur GitHub, crée son dépôt de code vide (`<Projet>-<Module>`, privé ou public) — **pas de second dépôt de lots** :
     une suite garde un seul `-Lots`, chaque lot y porte un préfixe de module (`3_GITHUB.md`) ;
   - demande au CdP en place — ou à la coordination, si elle existe — « ouvre le domaine <module> » : il amorce le
     checkpoint du domaine, ajoute sa ligne à la table des domaines et te remet **la ligne fixe** du nouveau CdP (elle
     nomme tous ses dépôts) ;
   - ouvre une conversation neuve avec Opus, **dans le même projet claude.ai**, colle cette ligne fixe, et titre la
     conversation `<nom du CdP> · <chantier>` ;
   - remplace les instructions du projet par le texte que le CdP te redonne (le nouveau checkpoint y est nommé).
3. **Quand les modules se touchent (mode C)** — deux CdP partagent un livrable, ta machine, des fichiers ou un serveur,
   ou un changement touche tous les domaines — **ouvre la coordination** : une conversation neuve avec Opus, le prompt
   `2_PROMPT_AMORCAGE_CDP.md` §D. La session de coordination reprend la méthode, le prompt du dev, le README des vivants
   et le package ; elle crée son checkpoint, tient la table des domaines (y compris `Methode/domaines.yaml`) et te
   redonne les instructions du projet dans leur version à plusieurs CdP (`1_INSTRUCTIONS_PROJET.md`).
4. **En C, installe l'arbitre et le contrôleur** (recommandés, §2 ter) : la coordination les prépare et te les propose ;
   toi, tu laisses actives les notifications de GitHub pour un workflow en échec et tu approuves la tâche planifiée du
   contrôleur (approbation automatique).

**Ensuite, au quotidien :**
- **une conversation par domaine**, titrée `<nom du CdP> · <chantier en cours>` ; tu parles à chaque CdP dans la
  sienne, de son domaine seulement ;
- **relancer un CdP** : une conversation neuve et la ligne fixe de son domaine (README des vivants), si son témoin est
  libre ; s'il est pris, la session précédente vit encore : reprends-la plutôt ;
- **à la coordination** : ouvrir ou fermer un domaine, mettre deux CdP sur un même produit, un sujet transverse, un
  doute, une question de méthode ;
- **tu ne relaies jamais un message d'un CdP à un autre** : ils s'écrivent par des chantiers `pour:` (§2 bis) ;
- **tu ne lis que le tableau des chantiers** : tout sujet d'un domaine y a son entrée (méthode §6), et l'arbitre le
  vérifie chaque matin.

## 3 ter · Passer d'un mode à l'autre, quand le projet grandit (ou rétrécit)

*Un projet commence presque toujours en A et se complexifie avec le temps. **Rien ne se migre : on ajoute** — un
checkpoint, une ligne à la table des domaines, un coordinateur. Les vivants, les numéros de décision, l'historique et
les chantiers restent où ils sont. Un passage se fait **entre deux lots**, jamais avec un lot en vol, et se note au
registre comme une décision.*

**Les signes qu'il est temps :**

| passage | quand |
|---|---|
| **A → B** | un second module **indépendant** démarre (son propre dépôt de code, sa propre release, rien en commun avec le premier) ; ou tu veux faire avancer deux sujets dans deux conversations en même temps |
| **B → C** | deux CdP partagent quelque chose : **un livrable** (la même application), **une ressource** (ta machine, un jeu, un serveur), **des fichiers** ; ou un changement touche tous les domaines (la méthode, le déploiement) ; ou tu te surprends à **relayer un message** d'un CdP à l'autre ; ou des numéros de décision sortent en double |
| **A → C** directement | dès le départ du second module, celui-ci partage un livrable, une ressource ou un serveur avec le premier (par exemple un second module **dans la même application**) |
| **C → B → A** (retour) | un domaine est fini ou en sommeil depuis longtemps ; il ne reste qu'un ou deux CdP actifs, sans rien en commun |

**A → B — tes gestes :**
1. Dans la conversation du CdP en place : « le projet passe en B : un second module, <lequel> ». Il réserve un numéro de
   décision et note le passage.
2. Sur GitHub, crée le dépôt de code du module ; s'il est public et qu'aucun `-Lots` n'existe encore, crée aussi
   `<Projet>-Lots` (privé) — un seul pour toute la suite.
3. Le CdP ouvre le domaine (§3 bis, point 2) et te remet la ligne fixe du nouveau CdP ; tu la colles dans une
   conversation neuve du même projet.
4. Tu remplaces les instructions du projet par le texte qu'il te redonne (version à plusieurs CdP).

**A → B — ce que la session fait :** son domaine prend un nom (`Opus-CdP-<Produit>`) et un checkpoint à lui, avec son
témoin ; la table des domaines naît (méthode §1 bis, README des vivants avec la ligne fixe de chaque CdP) ; les règles
de partage s'appliquent désormais (méthode §1 bis : ajout seul, numéros réservés par un push, messages par chantier
`pour:`, préfixe de module dans le nom des lots) ; la méthode du projet change de version ; le premier CdP **reste
propriétaire de la méthode** tant qu'il n'y a pas de coordination.

**B → C (ou A → C) — tes gestes :**
1. Ouvre la coordination : une conversation neuve, le prompt `2_PROMPT_AMORCAGE_CDP.md` §D, en y listant les domaines
   en activité (en A → C : le seul domaine existant).
2. Dis au CdP qui tenait la méthode, dans sa conversation : « la coordination est ouverte, elle reprend la méthode ».
3. En A → C : demande ensuite à la coordination d'ouvrir le second domaine (tu lui dis lequel ; elle te remet sa ligne
   fixe).
4. Réponds à ses propositions (fiche produit, arbitre) et colle les instructions qu'elle te redonne.

**B → C — ce que la session de coordination fait :** elle reprend la méthode, le prompt du dev, le README des vivants et
le package (le CdP qui les tenait les lui laisse) ; elle crée son checkpoint ; elle tient la table des domaines en trois
endroits (méthode §1 bis, README, `Methode/domaines.yaml`) ; les règles du mode C entrent dans la méthode (un livrable,
un seul lot en vol ; une ressource prise comme un livrable ; `attend:`, `touche:` ; la fiche produit d'un produit à
plusieurs CdP) ; elle propose l'arbitre ; elle prévient chaque CdP en activité par un message prêt à coller, que tu lui remets, et vérifie
ensuite sa réponse sur le dépôt ; un CdP au témoin libre le trouve par un chantier `pour:` à sa reprise (méthode §1 bis).

**Le retour, quand un domaine se ferme :** demande à la coordination (ou, en B, au CdP qui tient la méthode) « ferme le
domaine <nom> ». Elle marque le checkpoint « clos » (il reste comme référence), retire le domaine de la table aux trois
endroits, **rattache ses chantiers ouverts à un domaine qui vit** (par un chantier `pour:` à son CdP) et note la décision.
Quand il ne reste qu'un CdP actif et rien de partagé, la coordination peut se fermer à son tour : la méthode revient au
dernier CdP, l'arbitre s'arrête (ou continue, s'il rend encore service), tu repasses aux instructions à un seul CdP.

**Ce qui ne bouge jamais, quel que soit le passage** : le dépôt des vivants et ses fichiers ; les numéros de décision
(la suite continue) ; les chantiers (ils changent au plus de domaine) ; les dépôts de code ; la skill — elle renvoie
à la méthode du projet, qui porte les règles du mode.

---

## 4 · Ce qui va où

*La colonne « miroir » ne vaut qu'avec l'extension du miroir au projet ([`NOYAU.md`](NOYAU.md) §6).*

| élément | lieu de référence | miroir au projet ? | qui écrit | quand |
|---|---|---|---|---|
| Méthode du projet | dépôt des vivants `Methode/` | oui | CdP | à une version, après un lot qui l'a prise en défaut |
| Prompt du dev | racine du dépôt de code — **dépôt `<Projet>-Lots` si le code est public** | oui | CdP | à une version |
| Checkpoint (sous son plafond, méthode §6 ; l'historique en archive du domaine) | dépôt des vivants | oui | CdP | son §0 à chaque lot clos ; complété à la passation |
| Registre des arbitrages (plafond d'une entrée et coupe : méthode §6) | dépôt des vivants | oui | CdP | à chaque lot clos |
| Plan + journal des versions (le fait de chaque lot, écrit une fois) | dépôt des vivants | oui | CdP | à chaque lot clos |
| `chantiers.yaml` ⟨et, avec le tableau publié, `chantiers.html` et `chantiers.json`⟩ | dépôt des vivants | oui ⟨, et la page avec son fichier de données en artefact⟩ | CdP | à chaque écriture du yaml ; artefact à la clôture seulement |
| Table des domaines `Methode/domaines.yaml` | dépôt des vivants | oui | coordinateur | un domaine ouvert ou fermé, une section de file renommée |
| `<Dossier>/Archives/CHANTIERS_<AAAA-MM>.yaml` | dépôt des vivants | oui | l'archivage (`archiver_chantiers.py`) | à chaque passage de l'arbitre, sinon à la clôture du CdP |
| Attendus de réception | dépôt des vivants `attendus/<version>/` | non | CdP | au cadrage |
| Scripts jetables du CdP | dépôt des vivants `outils_cdp/` | non | CdP | au besoin |
| Code, banc, `CHANGELOG` | dépôt de code | non | dev | dans un lot |
| Cadrage, addenda, arrêts, rapport, maquette | dépôt de code `lots/<version>/` — **dépôt `<Projet>-Lots` si le code est public** | **non** | CdP (cadrage, addenda), dev (arrêts, rapport, `MAQUETTE_<n>.md`, une ligne par image avec son empreinte) | pendant le lot |
| Specs, guide de style, études | projet, écrits une fois | — | CdP | une fois, jamais réécrits |
| Données de production, journaux | **aucun dépôt** | non | toi | téléversés dans la session qui en a besoin |
| Donnée produite en session, à servir (un paquet, des tuiles) — avec un exécutant serveur | dépôt d'ordres, `transferts/<domaine>/<édition>/` (§2 quater) | non | le CdP qui la produit, **jamais le dev** | à l'édition ; retirée de l'arbre au compte rendu réussi |
| Images (tuiles, visuels) | **dans la discussion** | jamais | toi | l'import au projet les corrompt sans prévenir |

**Le projet claude.ai ne porte que** les références écrites une fois ⟨et, avec l'extension, les miroirs des vivants⟩,
rangés en dossiers par thème (`Methode/`, `<SousProjet>/`, `Archives/`…).

---

## 5 · Ce qui est générique, ce qui est à adapter

**Générique, à garder tel quel** : les rôles ; le cycle d'un lot ; le cadrage autoportant ; les critères en deltas,
mesurés sur l'archive livrée ; les arrêts du dev ; la réception à froid ; le CdP qui regarde lui-même les rendus ;
les vivants au dépôt ; la fusion en avance rapide après ta validation ; les pièges des sessions.

**À adapter au premier lot du projet** (le CdP te le demande à l'amorçage) :
- **le banc** : l'outillage qui mesure une archive (compte de fichiers, tests, lint, i18n, CSS, empreintes) ;
- **les portes** du dev (P0 à Pn) et ce qu'il ne touche jamais ;
- **le versionnage**, selon le régime de chaque livrable (les deux régimes : [`NOYAU.md`](NOYAU.md) §3) ;
- **le livrable** : zip de déploiement, fichier HTML unique, PDF, archive d'un agent… et où il se dépose — ou, s'il
  tourne sur un serveur de production que tu administres, comment il s'y déploie (l'exécutant serveur, facultatif) ;
- **la preuve propre au type de projet** : rebuild à l'octet pour un HTML buildé, tests et migration pour une app,
  rejeu pour un moteur de calcul, contrôles par le DOM pour une page.

**Le banc se construit par le premier lot**, un lot d'outillage, cadré court par le CdP et construit par le dev
([`NOYAU.md`](NOYAU.md) §3).

**Ce qui dépend du produit Claude** : les fonctions de l'application et de ses sessions dont la méthode se sert peuvent
changer ; `DEPENDANCES_CLAUDE.md` dit, pour chacune, ce qui casse et le repli. Relis-le à chaque version du package.

---

## 6 · Les coûts à attendre (mesurés sur un premier projet)

- un lot ordinaire : 5 à 20 minutes de dev, quelques minutes de réception ;
- un écran avec maquette : 15 minutes à 1 h 30 de dev, une ou deux passes de maquette avec toi (faite par le CdP avant le lancement, ou demandée au dev, qui la livre par un arrêt ; le CdP te la montre et relaie ton verdict mot pour mot) ;
- un addendum lancé par le CdP : quelques minutes, sans un geste de ta part ;
- une session de CdP : la passation à une fin de file naturelle ou au seuil de contexte de la méthode §6.

*Un sous-agent dev consomme le crédit de la session du CdP. Le premier projet coûte un lot d'outillage (le banc) avant
le premier lot de produit.*

---

## 7 · Faire vivre le package

- **La source est un dépôt privé ; ce dépôt public en est la copie anonymisée et bilingue** — ou ta copie, si tu fais évoluer la méthode
  pour toi (un fork, ou un dépôt privé où tu la pousses) ; la skill `methode-cdp` en est la copie installée
  (`skill/SKILL.md` fait foi).
- **Quand la méthode d'un projet change de version sur une leçon générique** (elle vaudrait pour tout projet), le CdP
  de ce projet la reporte ici — modèles, `3_GITHUB.md`, skill — dans un commit « Package vN : … », te le dit, et te
  propose la skill mise à jour. Une leçon propre au projet reste dans sa méthode.
- **Un projet déjà amorcé ne se réaligne pas tout seul** : sa méthode prime ; son CdP reprend une évolution du package
  à sa prochaine version de méthode, s'il y a lieu. **Avant de réinstaller la skill v19 sur un projet amorcé plus tôt**,
  son CdP vérifie que la méthode du projet porte ce que la skill v17 disait seule et la complète depuis
  `modeles/METHODE.md` sinon : pour tout projet, la passation (mesure, seuils, ligne fixe), les plafonds des vivants et
  le §0 du checkpoint à chaque lot clos ; avec plusieurs CdP, en plus, le témoin, la file et la coordination.
- Version du package dans l'en-tête de ce fichier ; l'historique dans git ; ni tag ni release nécessaires. **La skill
  prend la version du package qui la publie** : une version du package qui change la skill la republie sous son numéro.
- **Les modèles et la skill restent génériques** : aucun nom de projet, aucun numéro d'arbitrage d'un projet.

**Historique** : v1, le 23 octobre 2026. v2, le 26 octobre 2026 — le tableau des chantiers régénéré à chaque
écriture ; un dépôt `-Lots` privé quand le code est public ; l'exécutant local (Claude Code sur le PC, piloté
par fichiers) ; la passation mesurée. v3 — un seul dépôt de
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
v12, le 29 octobre 2026 — l'archivage des chantiers en recette : `archiver_chantiers.py` date chaque entrée qui
entre en recette et sort vers `Archives/CHANTIERS_<AAAA-MM>.yaml` celles qui y sont depuis 15 jours, `chercher` les
retrouve, `verifier_vivants.py --archives` contrôle les identifiants et le journal sur les archives ; l'arbitre
archive aussi (sinon le CdP ou le coordinateur, à sa clôture) ; un ordre ne s'écrit jamais sur un fichier qui
existe (exécutant serveur).
v13, le 30 octobre 2026 — l'arbitre des vivants expliqué en entier (`modeles/ARBITRE.md` v3 : ce qu'il est, pourquoi —
les cas vécus —, quand, ce qu'il coûte, comment le lire, la mise en place et qui fait quoi, le jugement ; §2 ter) ; le
contrôle 9 « checkpoints » de `verifier_vivants.py` (`--domaines`, `--racine`) et la table des domaines
`modeles/domaines.yaml` ; la lecture du lundi par l'arbitre ; la file d'un checkpoint ne porte que des chantiers
inscrits (méthode §6) ; skill v15.
v14, le 30 octobre 2026 — démarrer ou passer à plusieurs CdP, tes gestes (§3 bis) ; le prompt qui ouvre la
coordination (`2_PROMPT_AMORCAGE_CDP.md` §D) ; les instructions du projet à plusieurs CdP.
v15, le 30 octobre 2026 — passer d'un mode à l'autre en cours de route : les signes, tes gestes, ce que la
session fait, le retour quand un domaine se ferme (§3 ter).
v16, le 30 octobre 2026 — le dépôt d'ordres, pont d'échange de fichiers : par où une donnée arrive sur le serveur —
produite en session (`transferts/<domaine>/<édition>/` du dépôt d'ordres, puis un ordre `fichiers`), produite sur le PC
(`entree/`), publiée ailleurs (`telecharger`), jamais l'historique d'un dépôt de code public ; pourquoi, pas à pas du
CdP, limites (95 Mio par fichier, le clone de l'exécutant) (§2 quater ; `modeles/EXECUTANT_SERVEUR.md` v2).
v17, le 31 octobre 2026 — le dev reste un sous-agent du CdP jusqu'à la maquette, qu'il livre par un arrêt, et ne parle
qu'au CdP (`modeles/PROMPT_DEV.md`, `modeles/COMMANDE_DEV.md`) ; le témoin défini (les huit derniers caractères de
l'identifiant de session) ; la file d'un checkpoint sous un titre stable `## §<n> · La file`, une ligne `file:` vide
signalée, la coordination dans la table des domaines ; la machine du porteur par le pont de l'application Claude,
l'exécutant local en repli (`modeles/EXECUTANT_LOCAL.md` v2) ; des vivants courts : plafonds d'entrée, archivage des
chantiers en recette à sept jours, registre coupé par tranches de 50 numéros, checkpoint de 10 Ko et contrôle 10
(`modeles/ARBITRE.md` v4 : dix contrôles) ; la méthode d'un projet ne porte que sa part commune ; le tableau republié par
un sous-agent léger ; skill v16.
v18, le 31 octobre 2026 — un noyau de deux pages pour un porteur seul avec un CdP (`NOYAU.md`, avec la table des extensions,
leur signe et leur renvoi) ; un glossaire (`GLOSSAIRE.md`) ; les dépendances au produit Claude, leur repli et la date du
relevé (`DEPENDANCES_CLAUDE.md`) ; la coordination n'est plus jugée à son silence (`modeles/ARBITRE.md` v5) ; la passation :
des seuils de contexte pour avertir puis passer la main, les signes de saturation notés ; le tableau publié, une
page fixe et son fichier de données (`chantiers.html`, `chantiers.json`), ce que le CdP lit avant de republier ; deux
régimes de version, déployé à chaque lot ou publié par release (`modeles/depot-app/CHANGELOG.md`, section « Unreleased ») ;
la méthode, éprouvée sur trois projets dont un complexe ; skill v17.
v19, le 31 octobre 2026 — les corrections de la revue indépendante du package v18 : le numéro d'un correctif (la règle de
la méthode §1 bis), le régime « publié par release » jusqu'au bout (`lot/<nom du lot>`), la préséance complète,
la passation jamais avec un dev en vol, le §0 du checkpoint rafraîchi à chaque lot clos, des seuils à une seule source
(méthode §6), la relecture indépendante du code, le dépôt d'ordres cloné après la réception seulement, la protection de
`main` et des secrets ; l'outillage v19 (YAML strict, onze contrôles) ; l'arbitre en action GitHub (`modeles/ARBITRE.md` v6,
réécrit plus court) et le contrôleur (`modeles/CONTROLEUR.md`) ; les dépendances au produit complétées ; des liens relatifs
entre les documents et un test qui les garde. Puis, dans la même v19 : un noyau qui se suffit (`NOYAU.md` : les gestes de
démarrage, le banc en premier lot, la ligne fixe, les deux régimes, le repli sans sous-agent, les vivants du mode A ; le
miroir au projet et le dépôt public passés aux extensions ; l'amorçage en mode A sans tableau publié ni miroir) ; la skill
courte, en v19 comme le package (ce qu'une session sait avant de lire la méthode du projet ; le reste y est déplacé) ; une
seule source par règle (les chiffres de la méthode dans une table de son §6, partout ailleurs un renvoi, et un test de
parité en CI) ; le fait d'un lot écrit une fois, au journal des versions du plan ; des lots de complexité faible légers (la forme
courte du cadrage, sept portes, des attendus seulement quand le lot produit des valeurs à comparer) ; le contrôle 4
vérifie le numéro du lot en vol.
v20, le 1er novembre 2026 — le contrôle 12 de `verifier_vivants.py` : la taille d'une entrée de chantier et d'une entrée du
registre contre leurs plafonds (méthode §6), un chantier par domaine pour l'arbitre ; l'écart (b) du contrôle 4 se lit quelle
que soit la version ; les seuils de passation se comptent au-dessus de la charge fixe mesurée au premier tour, une règle
pour tous (`contexte.py` l'affiche) ; la skill reste v19.
