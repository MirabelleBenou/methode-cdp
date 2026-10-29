# MÉTHODE — <Projet> · v1
### <date> · <nom de la session de CdP> · tirée du package méthode CdP v<n>

*Comment un lot se décide, se construit, se réceptionne et se clôt.*
- *Elle change par version, après un lot qui l'a prise en défaut ; chaque version cite les décisions du registre qui la
  fondent.*
- *Le côté du dev est au `PROMPT_DEV_<P>.md`, à la racine du dépôt `<Projet>-App`.*
- *Elle prime sur la skill `methode-cdp`, qui porte la partie commune à tous les projets.*

> **Mode d'emploi du modèle** — ce qui est en clair est générique : le garder. Ce qui est entre `⟨…⟩` est propre au
> projet : le remplir à l'amorçage, ou au premier lot qui le décide. Supprimer cet encadré.

**Les dépôts** :

| dépôt | porte | qui y écrit |
|---|---|---|
| `<owner>/<Projet>` (privé) | les vivants : cette méthode, le plan, le registre, `chantiers.yaml`, le checkpoint, les attendus et les scripts du CdP | les sessions de CdP seules |
| `<owner>/<Projet>-App` (⟨privé / public⟩) | le code à la racine (l'archive de déploiement est `git archive` du commit de livraison), le banc dans `banc/` ; ⟨privé :⟩ le prompt du dev et `lots/<version>/` | le CdP sur `main` et pour le cadrage ; le dev sur la branche de son lot |
| ⟨code public seulement :⟩ `<owner>/<Projet>-Lots` (privé) | le prompt du dev, `lots/<lot>/` — **jamais au dépôt public** | le CdP (cadrage, addenda) ; le dev (arrêts, rapport) |
| ⟨serveur de production avec un exécutant serveur :⟩ `<owner>/<Projet>-Ordres` (privé) — le dépôt d'ordres | `ordres/<id>.json`, `resultats/<id>.md`, le format des ordres en `LISEZ_MOI.md` (§4 bis) | le CdP (les ordres) ; l'exécutant serveur (les comptes rendus) ; **jamais le dev** |

⟨Plusieurs dépôts de code :⟩ ils partagent **un seul `<Projet>-Lots`**, et chaque lot y porte un préfixe de module
(`lot/<préfixe>-<lot>`) ; le code part du dépôt du module, sur `lot/<lot>` (`3_GITHUB.md` §6 C).

---

## §1 · Qui fait quoi

- **Le porteur** décide et valide : à l'écran quand le lot montre une maquette, sinon en production. ⟨Avec un exécutant
  serveur : il ne dépose plus rien ; il dit « go » en nommant l'action, puis valide (§4 bis).⟩
  - ⟨S'il lit sur tablette ou téléphone, sans Python : **tout fichier se régénère chez Claude** ; on ne lui fait
    jamais lancer un script ni une commande⟩.
  - On lui écrit court, en **options numérotées avec une recommandation**.
  - **Un texte qu'il colle se remet prêt**, sans champ à remplir ; s'il dépend d'une valeur à venir (un hash, un
    numéro d'arbitrage), la session qui la produit le remet complet.
  - Chaque réponse où le CdP a tranché sans lui finit par **« Décidé sans toi : … »**.
  - **Une décision purement technique peut lui être déléguée** : le CdP tranche, la note au registre et la dit dans sa
    réponse.
- **Le CdP** (Opus, session longue) décide avec le porteur, écrit le cadrage, lance le dev, réceptionne et clôt. Il raisonne
  en développeur **et** en designer : il recommande sur le code et sur le visuel.
  - **Il n'écrit aucun code du livrable ni du banc. Ni dans un cadrage** : un cadrage porte des règles, des critères et
    les textes que l'utilisateur lira, jamais le code tout écrit. Une empreinte qu'on ne prédit pas sans écrire le code
    se prend au compte du dev.
  - Il écrit ses **scripts jetables** de mesure, de sonde ou de maquette, qui ne se transmettent jamais au dev.
  - Il peut éditer la **documentation** en direct, sur l'autorisation du porteur.
- **Le dev** (une session neuve par lot) construit, mesure à froid et livre. **Sonnet par défaut ; Opus pour** ⟨le
  moteur de calcul, une migration délicate, la rédaction…⟩.
  - **Le CdP le lance lui-même, en sous-agent de sa session** : le dev part **sans le contexte du CdP**, avec pour seule
    instruction la commande du §2. Son rapport et ses arrêts reviennent au CdP. **Le porteur ne parle qu'au CdP.**
- **L'outillage est du code** : un outil manquant se commande par un **lot d'outillage**, avec un cadrage court. Le
  banc est tenu par le dev.
- **Plusieurs CdP peuvent travailler en même temps**, un par domaine, sur les mêmes vivants : §1 bis.
- ⟨**L'exécutant serveur** (un programme sur le serveur de production) déploie les ordres du CdP ; il ne décide rien
  (§4 bis).⟩
- Les **contrôles mécaniques** appartiennent au CdP et au dev ; les **contrôles visuels** au porteur.

---

## §1 bis · Plusieurs CdP en même temps

*À deux, « `git pull` avant d'écrire » suffit. À quatre, des numéros de décision sortent en double, des compteurs
dérivent, des versions se répartissent par des messages que le porteur relaie (premier projet, quatre CdP en parallèle).*
*Un seul CdP, des modules indépendants, ou des modules liés avec un coordinateur : ce qui s'applique dans chaque cas est
au `LISEZ_MOI.md` §2 bis du package méthode.*

**Cinq principes** :
1. **Un CdP en activité = un domaine = un checkpoint à lui.** Personne n'écrit dans le checkpoint d'un autre.
2. **Ce qui est partagé s'écrit en ajout seul** (registre, plan, `chantiers.yaml`) : aucun récapitulatif réécrit,
   aucune ligne « dernière mise à jour », aucune version d'en-tête sur un fichier partagé — l'historique est dans git.
3. **Ce qui ne se prend qu'une fois se prend par un push** (un numéro de décision, un livrable) : un push refusé est la
   seule opération atomique dont on dispose.
4. **Ce qui se calcule ne s'écrit pas** : totaux, tableau. Après un conflit, on régénère ; on ne fusionne jamais à la main.
5. **Un fichier qui n'est pas en ajout seul a un seul propriétaire** : cette méthode, le prompt du dev, le README des
   vivants et le package méthode appartiennent à **la session de coordination** (Opus-Coordination).

**Les domaines** : ⟨une ligne par CdP — son nom (`Opus-CdP-<Produit>[-<Module>]`, un module seulement quand un produit
a plusieurs CdP), ce qu'il porte, son checkpoint (`<Dossier>/CHECKPOINT_<PRODUIT>_<MODULE>.md`) ; plus le coordinateur et
son checkpoint⟩. Le README des vivants porte la même table, avec la ligne de reprise de chacun.

**Ouvrir un domaine** : le porteur dit au coordinateur ce qu'il veut faire ; le coordinateur donne la ligne fixe d'un domaine
existant au témoin libre, ou ouvre le domaine (ligne ici et au README, checkpoint amorcé, chantiers rattachés), puis
donne le titre et la ligne de chaque CdP — ou lance la session par une tâche planifiée. Un produit à plusieurs CdP de
modules garde une **fiche produit** (le commun : rituel, banc, circuit, pièges ; jamais l'état), tenue par le
coordinateur. Le coordinateur ne cadre aucun lot de produit ; **il cadre et lance les lots d'outillage de la méthode et
des vivants** (`verifier_vivants.py`, `generer_tableau.py`, l'arbitre — `Methode/ARBITRE.md`, tiré de
`modeles/ARBITRE.md` du package : rôle, procédure, tâche planifiée).

**Les numéros de décision** : avant d'écrire une entrée, pousser seule, sur `main`, la ligne
`| **R<n>** | *réservé — <CdP>, <date>* | | |` après la dernière entrée. Push refusé → `git pull`, numéro suivant ;
accepté → l'entrée se rédige à sa place. Une entrée ne porte pas de total : elle marque `[exécution +1]` ou
`[inverse +1]` (§5).

**Le livrable et sa version** : le livrable est le dépôt de code d'où sort la release. **Un livrable, un seul lot en
vol** : le lot en vol porte dans `chantiers.yaml` `statut: en-vol`, `cdp:` et `livrable:`, et pousser cette entrée
prend le livrable. **Un autre lot du même livrable est suspendu**, même s'il vient d'un autre CdP : il reste `a-cadrer`
avec `attend: <id>`, sans cadrage poussé, branche ni dev, jusqu'à ce que le premier soit validé en production et
fusionné (ou abandonné sur décision du porteur). **L'étude et le pré-cadrage restent libres** : le pré-cadrage (règles,
critères, textes, sans version ni attendus) peut se pousser au dépôt des lots, sous `lots/<lot>/PRECADRAGE.md` ; il
devient le cadrage quand le lot prend le livrable. **Personne ne décide d'un numéro de version à l'avance** : la version
se calcule quand le lot prend le livrable (`main` plus un), s'écrit alors dans `version:` et le cadrage ; un lot
suspendu qui reprend la calcule sur le nouveau `main` et refait sa base. Un fichier d'un autre livrable se déclare
(`touche:`). Un lot sans release (une sonde, une étude jouée, de la documentation) ne porte pas de `livrable:`.

**Une ressource partagée se prend comme un livrable** : la machine du porteur et ce qu'elle fait tourner pour un lot
(l'exécutant local, un jeu, un logiciel piloté) n'accueillent qu'un lot à la fois, quel que soit son domaine. Le lot qui
l'occupe porte `ressource: <nom>` dans son entrée `en-vol` ; un autre attend (`attend: <id>`), l'étude et le
pré-cadrage restant libres. Elle se libère quand l'exécutant a rendu son dernier rapport et que le CdP l'a réceptionné.

**Entre CdP** : un signalement pour un autre domaine devient un chantier de son module, `statut: a-cadrer`,
`pour: <CdP>` ; **après chaque `pull`, un CdP lit les entrées `pour:` qui le visent**. Le porteur ne relaie plus. Une leçon
générique est un chantier `module: methode`, `pour:` la session de méthode.

**Le témoin** : chaque checkpoint porte en tête `Session en activité : <identifiant court>, depuis <heure>` (ou
« aucune — libre depuis <heure> »). La session qui reprend le pose par un push, c'est son premier geste ; une session qui
trouve après un `pull` un autre identifiant que le sien n'écrit plus aux vivants et le dit au porteur ; une session qui
attend un geste du porteur garde le témoin. **Un témoin se juge à son silence, pas à son âge** : une session peut vivre
plusieurs jours en attendant le porteur ; c'est l'absence de tout commit de cette session depuis plus de 24 heures qui
signale une session oubliée (le contrôle de l'arbitre, s'il existe).

**Le titre de la session** : `<nom du CdP> · <chantier en cours>`, changé à chaque chantier ; `-2` pour un second CdP sur
le même domaine, avec son propre checkpoint. La session se renomme si elle le peut, sinon elle donne le titre au porteur
en tête de réponse.

---

## §2 · Le cycle d'un lot

1. **La décision**, avec le porteur, notée au registre à la clôture. Pour un travail structurant, la spec ou le design est
   validé avant toute exécution.
2. **La mesure, puis le cadrage** (§3), et la maquette du CdP s'il y en a une (§3 bis).
   - **Les attendus de la réception se calculent au cadrage**, dans `<Dossier>/attendus/<version>/` du dépôt des vivants
     — jamais au dépôt de code, que le dev lit. Une livraison simulée du CdP peut servir à les calculer : **elle ne se
     transmet jamais**.
   - **Le CdP pousse le cadrage sur la branche du lot** : `lot/v<X.Y>`, partie de la tête de `main`, qui ne porte qu'un
     commit de plus, `lots/v<X.Y>/CADRAGE.md` (et sa maquette). Le cadrage nomme ce commit de base.
   - **Le CdP lance le dev** : outil `Agent`, en arrière-plan, **le modèle et le mode d'effort du cadrage**, et une
     commande en quatre parts (modèle : `COMMANDE_DEV.md`) — qui il est et ce qu'il exécute ; les conditions pratiques,
     qui priment sur le cadrage ; les arrêts ; sa réponse finale.
   - **Repli** : si le CdP ne peut pas lancer de sous-agent, il donne au porteur une ligne à coller au mot près, avec
     au-dessus « **Sonnet · Medium · conversation neuve** » (modèle, effort, session).
   - **Garde-fou** : un sous-agent consomme le crédit de la session du CdP ; la passation se mesure toujours.
3. **Un arrêt du dev** : le dev pousse sa branche et la raison (`ARRET_<n>.md`). Le CdP la lit au dépôt, pousse
   `ADDENDUM_<n>.md` sur la même branche et relance le dev (le même sous-agent s'il est joignable, sinon un neuf, qui lit
   aussi les rapports précédents). **Un addendum ne reprend jamais un lot remis au porteur** (étape 6).
4. **La livraison** : le commit de livraison, puis `RAPPORT_DEV.md` dans un commit à part.
5. **La réception** (§4), puis le verdict au porteur, avec la prédiction pour la production, et **le livrable remis tel
   quel**, sous son nom exact, avec son sha256 — ⟨avec un exécutant serveur : **déployé par un ordre** (§4 bis), la
   remise devenant le repli⟩.
6. **Une livraison = un nouveau numéro.** Ce qui se remet au porteur ou se déploie porte une version qui n'a jamais été
   remise. Un correctif ou des retours d'essai après une remise font **un lot de la version suivante**, qui garde le
   livrable, sur sa propre branche partie de celle du lot, dans la même session de dev si elle est encore
   ouverte. **L'addendum sous la même version ne sert que tant que rien n'a été remis ni déployé** : lever un arrêt,
   corriger un écart de la réception.
7. **La validation en production par le porteur**, puis **la fusion** : `git push origin lot/v<X.Y>:main` en avance rapide,
   jamais `--force` ; enfin **la clôture** (§6), une fois par lot.

---

## §3 · Le cadrage, la commande du dev

**Il porte** (modèle : `CADRAGE.md`) :
- le **modèle**, le **mode d'effort** et la **session** du dev ;
- les décisions du porteur et les règles ;
- **ce qui ne bouge pas**, et la **liste exacte des fichiers** que le lot a le droit de toucher ;
- les critères et la prédiction des portes, **en deltas contre la base mesurée à froid** ;
- le texte du `CHANGELOG`, mot pour mot ;
- les arrêts propres au lot ;
- le commit de base et les pièces qu'il pousse avec lui — rien à téléverser.

**Il est autoportant** : avec le prompt du dev, il se suffit. Il ne cite ni un cadrage précédent ni le modèle de cadrage.

**Le mode d'effort** : Medium par défaut ; High pour une migration, une passe de fond, plusieurs écrans, un écran neuf
avec ses routes, un moteur de calcul, des étapes en cascade ; Faible pour un correctif d'une ligne.

**Mesurer d'abord** :
- **Sur l'état réel vérifié**, jamais sur l'exécution supposée d'un lot précédent. Quand des specs se sont accumulées,
  les consolider en un seul cadrage.
- **Sur les données réelles quand il y en a** : une sonde en lecture seule, éprouvée sur le banc, lancée en production
  (par le porteur, sous forme de script shell à déposer), dont la sortie revient au CdP. La mesure déplace souvent le lot.
- **Avant d'appeler une table, un fichier ou un champ par ce qu'il contient, lire chaque endroit qui y écrit.**
- **Un réglage qui change un comportement non déterministe** (un modèle de langage, un rendu) **se mesure avant de se
  cadrer**, par un script jetable du CdP.

**Chercher ce que le changement casse** :
- **Avant de commander un changement de valeur, de contrat ou de formule, chercher dans les tests et dans le banc les
  valeurs qu'il change**, pas seulement les symboles qu'il touche. Ajouter une lecture ou une écriture à une route
  existante change son contrat.
- **Avant de créer une table, une colonne, une route ou un fichier, chercher celui qui joue déjà ce rôle.**
- **Passer les dettes à déclencheur contre la liste des fichiers du lot** : un fichier que le lot touche peut solder une
  dette au passage.

**Écrire les critères** :
- **Avant d'écrire un critère, le passer sur l'existant.**
- **En deltas contre la base**, jamais en valeurs absolues ; **mesurés sur l'archive livrée**, jamais sur le répertoire
  de travail.
- **Un critère de comptage textuel dit s'il compte les commentaires.**
- **Une prédiction se calcule sous les règles du cadrage**, pas sous une lecture idéale.
- **Une prédiction de calcul est un rejeu** : le moteur rejoué sur la base, chaque règle posée seule puis toutes
  ensemble, la sortie attendue et son sha256 ; le dev retrouve la même sortie.
- **Une règle dupliquée se tient par un critère d'équivalence** : la copie comparée à l'original sur tous les cas du
  banc.
- **Une empreinte de rendu nomme ses conditions** (locale, taille, thème).
- **Une règle de couleur ou de contraste se mesure sur tous les thèmes** avant d'être commandée.
- **Un libellé se mesure à la largeur la plus étroite qui le porte** ; un débord, aux deux bouts de chaque palier.
- **Un cadrage qui fait d'une API non nommée un arrêt nomme toutes celles qu'impose son propre format.**

**Les preuves et le dev** :
- **Pas de critère au pixel contre la base**, sauf pour prouver qu'un refactor est neutre (§3 bis). Contre la maquette
  du CdP, oui.
- **Des images seulement si le visuel vaut d'être vu avant la production** : trois à six, désignées par leur nom ; sinon
  Le porteur valide en production. **Une pièce posée** (photo, tampon, écusson) **se montre en découpes à l'échelle 1**,
  jamais en page réduite.
- **La preuve fonctionnelle passe par les tests** ; un lot purement d'écran se prouve par un contrôle d'écran
  (présence, absence, textes et comptes du DOM), sans capture relue par le dev.
- **Pas de surconception** : aucune recette au-delà de ce qui prouve le lot ; l'outillage ne mange pas le budget du lot.

---

## §3 bis · La maquette du CdP, par le vrai code, avant le lancement

*Le CdP y écrit du code jetable, jamais celui du livrable.*

- **Pour un écran neuf**, on part d'une copie de la base, on y greffe la vue, son script et sa CSS, et on la rend par le
  vrai code, sur des données posées par un **fichier d'état du banc**.
- **Pour une retouche de fichiers statiques** (CSS, gabarit), la copie porte directement les fichiers du lot ; le
  cadrage exige alors du dev **de les reprendre tels quels**, vérifiés par leur sha256.
- **Ce que la maquette fixe passe au cadrage au caractère près.**
- **Un refactor qui doit être neutre se prouve au cadrage** : le CdP rend sur sa copie les écrans touchés contre la base,
  identiques au pixel ; le dev rejoue les mêmes instruments. L'instrument **masque tout ce qui porte la version**.
- **Les images de référence se prennent sur la maquette**, pas sur la base, quand la base porte un défaut qui change le
  rendu ; **un rendu de contrôle n'injecte que la cause attendue**, pour séparer l'effet du bruit.
- **Une ligne en édition préchoisit la valeur neutre**, jamais une valeur calculée nommée.
- **Le porteur valide la maquette avant le lancement.** Quand il rouvre une option écartée après l'avoir vue, **la refaire
  plutôt que la défendre**.

---

## §4 · La réception, à froid

**Préalables** : ⟨les dépôts clonés, la base extraite par `git archive` de `main`, le banc copié, les dépendances
installées sous la bonne version, les services démarrés dans la commande qui s'en sert⟩.

**Les étapes** :
1. **Les attendus**, calculés au cadrage dans `<Dossier>/attendus/<version>/`. **Ils ne se copient jamais sur le
   rapport du dev.** Seule une valeur imprévisible se prend dans son compte, puis se recalcule.
2. **L'archive de livraison** : `git archive` du commit de livraison que nomme le rapport. **C'est le livrable** : celui
   qui se mesure est celui que le porteur dépose.
3. **Les portes, rejouées** sur l'archive déballée : ⟨le rituel du banc, la mesure commune, tests, lint, contrôle de
   syntaxe sur la sortie réellement produite — pas seulement sur les sources⟩.
4. **Le diff, lu contre les règles du cadrage** : chaque règle se retrouve dans le code ; **rien hors des fichiers
   autorisés** ; hors du code, rien ne bouge sauf `lots/v<X.Y>/`.
5. ⟨**La migration**, s'il y en a une : montée, descente, remontée depuis une base semée à la tête précédente.⟩
6. **Le rendu, regardé par le CdP lui-même** : le dev ne relit aucune capture, donc personne d'autre ne voit l'écran
   avant le porteur. Ce que les critères ne mesurent pas ne se voit que là. Avec une maquette : comparaison au pixel.
7. **Le livrable remis au porteur tel quel** : sous son nom exact, avec son sha256 dans le verdict. Un fichier unique à
   déposer (une page HTML) se remet **hors zip**. ⟨Avec un exécutant serveur : l'archive reste produite et gardée ;
   **l'ordre désigne le commit reçu** (et le sha256 pour un fichier statique) ; la remise devient le repli (§4 bis).⟩
8. **Le verdict** : conforme, ou un correctif (version suivante). **Un arrêt juste du dev n'est jamais un reproche** :
   l'exécution a souvent raison contre le cadrage.

---

## §4 bis · Le déploiement ⟨facultatif : projet avec un serveur de production et un exécutant serveur⟩

*Sans serveur de production que le porteur administre : supprimer cette section ; le livrable se remet (§4, étape 7). Le
guide et l'implémentation de référence : `modeles/EXECUTANT_SERVEUR.md` et `modeles/executant-serveur/` du package (copie publique :
`templates/server-runner/`).*

**Le principe** : un programme déterministe sur le serveur (⟨son nom dans ce projet⟩) tire chaque minute les ordres du
dépôt d'ordres, n'exécute qu'une liste blanche d'actions et y pousse son compte rendu. **Aucune IA dans le chemin du
déploiement** ; un agent sur un serveur de production, s'il existe, est borné (ni secrets, ni écriture en base, ni root).

**Le circuit, après une réception sans écart** :
1. **Une application qui a des utilisateurs** : le CdP demande au porteur **un « go » qui nomme l'action** (« go déploiement
   v<X.Y> ») et le cite dans le champ `go` de l'ordre. **Des fichiers statiques à retour instantané** (une page HTML
   autoportante) : déploiement direct, sans go.
2. Il pousse `ordres/<id>.json` ; l'identifiant `AAAA-MM-JJ-NN` est **le suivant au dépôt, pris par le push** (push
   refusé → `pull`, numéro suivant). **Un ordre ne s'écrit jamais sur un fichier qui existe** : l'identifiant se lit
   **après** `git pull`, jamais sur une liste lue avant ; l'écriture refuse l'écrasement (`set -o noclobber` avant
   `cat >`, ou un test `[ -e ordres/<id>.json ]` qui arrête tout) ; avant le push, `git diff --cached --name-status` ne
   montre qu'**une ligne `A ordres/<id>.json`** — un `M` arrête tout. Un ordre ne se réécrit jamais : pour corriger, un
   nouvel ordre. *(Leçon vécue : une session a pris un identifiant sur une liste lue avant son `pull` et a écrasé, par
   `cat >`, l'ordre déjà joué d'une autre session ; le push n'a rien refusé — une modification, pas un ajout.)*
3. Il lit `resultats/<id>.md` par une **attente bornée** (une à deux minutes en temps normal), jamais une boucle sans fin.
4. Il dit au porteur la version servie, la santé, la sauvegarde prise, les comptes avant et après ; le porteur valide à l'écran ;
   **puis** la fusion dans `main` (§2, étape 7).
5. **Le retour** : `revenir` — sur go pour l'application, refusé après une migration ; sans go pour un fichier statique.
   **Les opérations de fichiers** : action `fichiers`, dans les zones déclarées sur le serveur ; vider la corbeille sur go.
6. **Un compte rendu en échec** : le CdP le dit, avec le nom de la sauvegarde ; une file arrêtée ne se rouvre que sur la
   décision du porteur. **Jamais de restauration de base par l'exécutant serveur** : procédure manuelle ⟨où elle est écrite⟩.

**Le repli** : l'exécutant serveur en panne, le livrable se remet au porteur tel quel (§4, étape 7) et la procédure manuelle
s'applique. **Chaque CdP qui déploie rattache le dépôt d'ordres en écriture ; le dev ne le lit ni ne l'écrit jamais.**

⟨Ce qui est propre au projet : les actions en service, les fichiers statiques et les zones, les tables comptées, la
procédure manuelle, la date de mise en service.⟩

---

## §5 · Ce qui ne pardonne pas

- **Rien ne se croit, tout se mesure**, sur l'archive déballée à froid. Les portes se lisent en deltas.
- **La version** : ⟨qui la fait monter — script `release` côté dev, pré-autorisé, +1 cran par lot / seulement avec
  l'accord explicite du porteur⟩. Un lot qui ne change pas le code (méthode, banc) ne prend pas de version.
- ⟨Les invariants du projet : un fichier, un module ou une empreinte qui ne bougent que sur autorisation écrite du
  porteur portée par le cadrage.⟩
- **Les textes produits restent neutres en genre** : jamais présumer le genre d'une personne d'après un pseudonyme.
- ⟨Avec un exécutant serveur : jamais d'ordre d'application sans le go du porteur qui nomme l'action ; jamais d'action
  hors de la liste blanche ; un ordre ne se réécrit pas ; ni secret ni donnée de production dans un ordre ou au dépôt
  d'ordres ; les invariants des données (`EXECUTANT_SERVEUR.md` §8).⟩
- ⟨Code public : le prompt du dev et `lots/` au dépôt privé des lots, jamais au public ; zéro référence privée dans le
  diff poussé (prénom, profil, méthode, registre) — un fichier poussé reste dans l'historique public.⟩
- **Le compte de « l'exécution a raison »** se tient au registre : chaque arrêt ou signalement juste du dev s'y ajoute.
  Un défaut du CdP vu en production ouvre le compte inverse.

---

## §6 · La clôture et les documents

**À chaque lot clos, une fois** :
- la ligne du journal du plan, pour un lot qui prend une version ;
- le registre (la décision, et « ce que le lot apprend » quand il y a une leçon) ;
- `chantiers.yaml`, **puis `chantiers.html` régénéré** (ci-dessous) ;
- **un commit « Lot v<X.Y> clos »** au dépôt des vivants, puis **le miroir au projet** ;
- le checkpoint **du domaine**, à la passation.

Deux lots reçus le même jour peuvent se clore ensemble.

**Les vivants** :
- vivent au dépôt des vivants **sous des noms stables** ; la version est dans l'en-tête, l'historique dans git ;
- se modifient par remplacements ciblés, ou se remplacent en entier en retirant l'obsolète ;
- **restent courts** : quand l'un redevient long, ce qui ne vit plus part dans une **archive neuve**
  (`Archives/<NOM>_ARCHIVE_<plage>.md`), figée, jamais réécrite ; pour `chantiers.yaml`, l'archivage est automatique
  (ci-dessous) et `chercher` retrouve une entrée ;
- **le projet en porte un miroir**, recopié à chaque clôture par `project_write` avec `local_path` depuis le clone ;
  **jamais depuis le texte servi par l'outil du projet**.

**Les chantiers en recette — l'archivage** :
- à la clôture, l'entrée passe en `statut: recette`, puis **n'est plus touchée à la main** : la ligne `recette-le: <date>`
  est posée par `archiver_chantiers.py` (elle ne s'écrit ni ne se corrige à la main), et retirée par lui d'une entrée
  rouverte ;
- une entrée en recette depuis 15 jours sort vers `<Dossier>/Archives/CHANTIERS_<AAAA-MM>.yaml` (le mois du passage ;
  on n'y fait qu'ajouter, figé à la fin du mois) ; le script contrôle l'absence de perte avant d'écrire ;
- **qui archive** : l'arbitre, s'il existe, à chaque passage (`Methode/ARBITRE.md` §1.4 bis) ; **sans arbitre**, le CdP
  ou le coordinateur lance à sa clôture
  `python3 -B <Dossier>/archiver_chantiers.py archiver --chantiers <Dossier>/chantiers.yaml --archives <Dossier>/Archives`,
  puis régénère le tableau et commite ;
- **un id archivé ne se réutilise pas** ;
- le vérificateur se lance avec `--archives <Dossier>/Archives` : un id à la fois vivant et archivé est un écart, et la
  dernière version du journal se cherche aussi dans les archives.

**Le tableau des chantiers** — la page lisible de `chantiers.yaml` :
- **Chaque fois que le CdP écrit `chantiers.yaml`** — à la clôture, mais aussi en cours d'échange (un chantier ajouté,
  un statut qui change) —, il régénère dans le même geste `chantiers.html` par
  `python3 -B <Dossier>/generer_tableau.py <Dossier>/chantiers.yaml <Dossier>/chantiers.html`. Un `chantiers.yaml`
  modifié sans sa page n'est pas fini.
- Il commite les deux ensemble au dépôt des vivants, recopie les deux au projet en miroir, **publie la page en artefact
  au même lien** (le lien est noté au §6 du checkpoint) et **la remet en fichier `.html`** dans la discussion.
- Republier un artefact d'une conversation précédente exige de le relire d'abord (l'outil le demande) : le CdP le lit une
  fois par session, le compare à la régénération, puis republie le même fichier au même lien.
- `generer_tableau.py` ne se modifie pas pour un projet : titre et libellés se lisent dans l'en-tête de
  `chantiers.yaml`.

**Où vit chaque document** :
- **au dépôt des vivants** : les vivants, les statuts des sous-projets, les attendus, les scripts du CdP ;
- **au dépôt de code** : le code, le banc, le prompt du dev, et sous `lots/` les cadrages, addenda, arrêts, rapports et
  maquettes — hors de l'archive de déploiement ;
- **au projet, écrits une fois** : specs, guide de style et addenda, études, notes de référence ; ils ne se réécrivent
  jamais ;
- **nulle part** : les rapports du dev et les cadrages ponctuels ne vont pas au projet.

**Le CdP dépose lui-même au projet** : il dit ce qu'il a écrit (dépôt, commit, chemin) ; **il ne supprime rien sans
l'accord explicite du porteur**, sauf la version qu'il vient de remplacer ; un document neuf se crée dans son dossier,
jamais à la racine ; un ancien rejoint son dossier à sa prochaine mise à jour.

| dossier du projet | porte |
|---|---|
| `Methode/` | cette méthode, le prompt du dev (miroir), les chartes communes |
| `<Dossier>/` | le plan, le registre, `chantiers.yaml` et `chantiers.html`, `generer_tableau.py`, le checkpoint, les notes de référence |
| `<Dossier>/Archives/` | les archives figées |
| `<Dossier>/Specs/` · `<Dossier>/GuideDeStyle/` | les références du produit |
| ⟨`<SousProjet>/`⟩ | ⟨un dossier par sous-projet⟩ |

**Ce qui se téléverse encore** dans la session qui en a besoin : les données de production, qui n'entrent dans aucun
dépôt. **Plus de prompt de reprise** (la passation, ci-dessous). **Les images** passent dans la discussion, jamais par les fichiers du projet.

**La passation se mesure, elle ne se devine pas** :
- **Ce qui se mesure** : la taille du contexte au dernier tour, par `python3 -B <Dossier>/outils_cdp/contexte.py` (copié
  du package). Ce n'est pas le cumul consommé depuis le début de la session, qui grossit bien plus vite.
- **Quand** : à chaque clôture de lot, avant chaque cadrage ou lancement de dev, et au moins tous les dix échanges.
- **À 600 000 jetons, le CdP prévient le porteur**, en tête de sa réponse : « Contexte : ~N jetons — passation à prévoir ».
  Il ne lance plus de lot neuf ; il finit celui en cours.
- **À 700 000 jetons au plus tard**, ou à une fin de file naturelle avant, **il passe la main**, sans attendre qu'on le
  lui demande, d'un bloc, en une réponse :
  1. le §0 du checkpoint du domaine réécrit sur l'état réel (où on en est, ce qui bloque, ce qui attend le porteur), et la
     ligne fixe en tête vérifiée : elle nomme **tous les dépôts du domaine** (§7) ;
  2. le témoin remis à « aucune — libre depuis <heure> » ;
  3. push, puis le miroir au projet ;
  4. **la ligne fixe du domaine**, sous « **Opus · conversation neuve dans le projet** » : « Tu es <CdP>. Reprends :
     rattache en accès push les dépôts <owner> <dépôts du domaine> (un clone à la fois), fais git pull dans <dépôt des
     vivants>, lis `<checkpoint du domaine>` en entier (§0 d'abord) et suis-le. » — la ligne exacte de chaque domaine
     est au README des vivants et en tête de son checkpoint.
- **Rien ne voyage hors du dépôt** : pas de prompt de reprise, ni « prochain numéro », ni version à venir dans un texte
  remis au porteur — un texte qui recopie l'état vieillit pendant que les autres CdP avancent.
- **La reprise peut être lancée par la session elle-même** : une tâche planifiée unique dont le prompt est la ligne
  fixe ; le porteur ouvre la session dans sa liste de tâches. Quand le porteur n'est pas là pour l'ouvrir, la ligne fixe suffit.
- **Au premier signe de saturation** avant le seuil (pertes de fil, contradictions, une décision oubliée) : même
  passation, tout de suite.
- Le contexte d'un sous-agent dev ne compte pas dans celui du CdP ; son crédit, si.

---

## §7 · Les pièges du bac à sable

**Général** :
- **Le bac à sable ne garde rien d'une session à l'autre** : tout se reconstitue depuis les dépôts.
- **Une commande a un délai** (jusqu'à 600 s, à constater) ; au-delà, arrière-plan et **fichier témoin** écrit à la fin
  (une sonde `pgrep -f …` se trouve elle-même).
- **Plusieurs versions d'un interpréteur peuvent coexister** : la version par défaut n'est pas forcément celle de la
  production ; ⟨épingler la bonne⟩.
- **Exécuter un script crée des caches** (`.pyc`…) qui faussent les comptes : mesurer d'abord, tester sur une copie.
- **`cut -c` coupe l'UTF-8** : les documents se lisent avec un vrai langage.
- **Les fichiers du projet ne sont pas sur le disque** : l'outil du projet les rend en texte.
- **Un chantier introuvable dans `chantiers.yaml` est peut-être archivé** : le chercher par
  `python3 -B <Dossier>/archiver_chantiers.py chercher <id ou mot> --chantiers <Dossier>/chantiers.yaml --archives <Dossier>/Archives`
  (`--partout` : dans toutes les valeurs), jamais en recréant l'entrée.
- ⟨Avec un exécutant serveur : rattacher le dépôt d'ordres en écriture en début de session ; relire `resultats/` par
  une attente bornée, jamais une boucle sans fin.⟩

**Git et GitHub** : voir `3_GITHUB.md` §5 du package — tags, releases et suppressions de branche par le porteur ; clone
d'une seule branche ; lignes d'attribution ; aucun secret. **La ligne fixe d'un domaine nomme tous ses dépôts**, en
accès push : le garde-fou d'une session refuse un rattachement que le porteur n'a pas demandé en toutes lettres, et la
ligne qu'il colle vaut cette demande. Un dépôt de plus en route : la session le demande au porteur en une ligne prête
(« dis-moi « rattache X » »).

⟨**Propres au projet** : à compléter lot après lot — chaque piège payé une fois s'écrit ici.⟩

---

## §8 · Le coût visé

- **Un lot ordinaire** : une dizaine à une vingtaine de minutes de dev, une réception de quelques minutes.
- **Un écran avec maquette du CdP** : de 15 minutes à 1 h 30 de dev ; la maquette validée en un ou deux tours.
- **Un addendum lancé par le CdP** : quelques minutes, sans un geste du porteur.
- **Le CdP note son propre coût** à chaque passation : contexte mesuré, premiers postes.

---

*Rédigé par <session> le <date>, à l'amorçage du projet (R1), depuis le package méthode CdP v<n>.*
