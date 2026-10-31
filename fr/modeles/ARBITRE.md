# L'ARBITRE DES VIVANTS — <Projet> · v4
### <date> · <session de coordination> · lu par la tâche planifiée quotidienne · tiré du package méthode CdP

*Une session neuve, lancée chaque matin par une tâche planifiée, qui contrôle les vivants partagés **et les checkpoints**
et **signale sans corriger** : elle lit, elle dépose des chantiers `pour:`, elle **archive** les chantiers en recette
(sa seule écriture mécanique), le lundi elle relit les checkpoints face aux décisions de la semaine, elle tient un
journal, elle résume. Elle ne réserve aucun numéro, ne prend aucun livrable, ne lance aucun dev, n'envoie aucun message
ailleurs.*

> **Mode d'emploi du modèle** — facultatif : utile quand plusieurs CdP écrivent les mêmes vivants (`LISEZ_MOI.md`
> §2 bis et §2 ter du package : inutile en A, facultatif en B, recommandé en C). Le coordinateur le copie en
> `Methode/ARBITRE.md` du dépôt des vivants, remplit les `<…>` et adapte les `⟨…⟩` (chemins, table du §2), crée la
> table des domaines `Methode/domaines.yaml` (modèle `modeles/domaines.yaml`), amorce `Methode/ARBITRE_JOURNAL.md`
> (§1.5), crée `Archives/` et crée la tâche planifiée (§4). Le §0 explique à un lecteur qui découvre la méthode ce
> qu'est l'arbitre et pourquoi ; les §1 à §3 sont la procédure que la session suit à la lettre ; les §4 et §5 servent au
> coordinateur et au porteur. Supprimer cet encadré.

---

## §0 · L'arbitre en neuf questions

*Pour le lecteur humain — le porteur, le coordinateur, un CdP. La session de la tâche planifiée peut passer ce §, qui
n'ajoute aucune règle à la procédure des §1 à §3.*

### 0.1 · Qu'est-ce que c'est ?

Quand plusieurs chefs de projet (CdP) travaillent en même temps, ils écrivent dans les mêmes **vivants partagés** : le
registre des décisions, `chantiers.yaml` (la liste de tout ce qui est à faire, en cours ou fini) et la page qui s'en
régénère, le journal du plan, et un checkpoint par domaine (l'état courant, point d'entrée de la session suivante).
Chaque CdP ne lit que son domaine : **personne ne voit l'ensemble**. L'arbitre est le regard qui manque.

C'est **une session de lecture et de signalement**, lancée chaque matin par une tâche planifiée, sans mémoire d'un
passage à l'autre : tout se reconstitue depuis le dépôt des vivants. Elle n'est ni un CdP ni le coordinateur : **elle
ne corrige rien**, le propriétaire corrige. Une seule écriture, mécanique : l'archivage des chantiers en recette
(§1.4 bis), par `archiver_chantiers.py` — jamais à la main.

- **Ce qu'elle voit** : des numéros de décision en double ou un trou, des identifiants de chantier en double (vivants
  ou archivés), un chantier en vol sans `cdp:`, deux lots en vol sur un même livrable ou une même ressource, un tableau
  qui ne correspond plus au yaml, un journal du plan en avance sur les chantiers (`verifier_vivants.py`, contrôles 1
  à 8) ; **un checkpoint en retard sur les chantiers** (contrôle 9, et la lecture du lundi) ; **un checkpoint trop gros**
  (contrôle 10) ; **les sessions oubliées** qui gardent un témoin.
- **Ce qu'elle ne voit pas** : la qualité d'une décision, l'état du code, la production. Elle ne juge que la forme des
  vivants partagés.

### 0.2 · Pourquoi ça existe ?

Parce que, à plusieurs CdP, les mêmes accidents reviennent, et que chacun est invisible depuis un seul domaine. Ce sont
des cas vécus, sur le premier projet mené ainsi :

1. **Deux sessions ont pris le même numéro de décision.** Chacune l'avait choisi avant son `pull` ; git ne voit pas
   de conflit entre deux lignes distinctes qui portent le même numéro. Trois fois en deux jours. → le contrôle 1.
2. **Des compteurs tenus à la main ont dérivé** d'une entrée à l'autre. → ce qui se calcule ne s'écrit pas (méthode §1 bis) ; le contrôle 1 vérifie la suite des numéros.
3. **Un chantier est resté en vol sans chef de projet déclaré**, et deux lots étaient prêts à partir sur **le même
   livrable**. → les contrôles 5 et 8.
4. **Le tableau des chantiers publié ne correspondait plus au fichier** : le yaml avait changé, la page non, et c'est la
   page que le porteur lit. → le contrôle 6.
5. **Des sessions oubliées gardaient un témoin** et bloquaient la reprise d'un domaine. La première règle jugeait l'âge
   du témoin : elle a signalé deux sessions bien vivantes, qui attendaient seulement un geste du porteur. Elle est
   devenue la règle du *silence* : aucun commit de la session depuis 24 heures. → le §1.3.
6. **Le fichier des chantiers a grossi sans fin** (169 Ko, puis près de 200 Ko, aux trois quarts des chantiers finis).
   → l'archivage automatique, le §1.4 bis.
7. **Les checkpoints ont pris du retard sur les chantiers.** Dix sujets n'existaient que dans des checkpoints — que le
   porteur ne lit pas —, dont une fonctionnalité annoncée « pour la suite » et jamais inscrite ; d'autres files
   annonçaient comme à faire des chantiers déjà finis. → la règle « la file d'un checkpoint ne porte que des chantiers
   inscrits » (méthode §6), le contrôle 9 et la lecture du lundi. Le contrôle 9 lui-même avait ses angles morts : deux
   domaines lui échappaient, l'un dont la section de file ne portait qu'un renvoi (« tout est au §0 »), l'autre qui n'en
   déclarait aucune (`file:` vide). → la section `## §<n> · La file` qui porte la liste elle-même, et le `file:` vide
   devenu un écart du domaine.
8. **Les vivants ont regrossi en quelques jours** : un fichier de chantiers est passé de 95 à 146 Ko en un jour, un
   registre a atteint 206 Ko, un checkpoint 47 Ko — les messages entre CdP s'empilaient dans les entrées, et chaque CdP
   relit tout à chaque reprise. → les plafonds (méthode §6), l'archivage au bout de sept jours, le contrôle 10.

**Pourquoi une session neuve et planifiée, plutôt qu'un CdP qui s'en charge** : elle n'a **aucun enjeu dans un
domaine**, donc aucune raison de minimiser un écart ; elle passe **quand personne ne travaille**, donc sans conflit
d'écriture ; elle laisse **une trace datée même quand tout va bien**, donc son silence ne se confond pas avec une panne ;
elle **ne corrige rien**, donc elle ne peut pas aggraver une erreur — le propriétaire corrige.

### 0.3 · Quand en ai-je besoin ?

| mode (`LISEZ_MOI.md` §2 bis) | arbitre | pourquoi |
|---|---|---|
| **A** — un projet, un CdP | **inutile** | un seul CdP écrit, il voit ce qu'il écrit ; pas de table des domaines à tenir |
| **B** — modules indépendants, un CdP chacun | **facultatif** | utile si les vivants partagés grossissent, ou dès le premier écart (un numéro en double, un tableau désaligné) ; la table des domaines compte alors un domaine par module |
| **C** — modules liés, un coordinateur | **recommandé** | dès que plusieurs CdP écrivent les mêmes vivants le même jour : c'est là que les huit cas ci-dessus arrivent |

Le signe qu'il est temps : le premier numéro de décision en double, ou la première session oubliée qui garde un témoin.

### 0.4 · Qu'est-ce qu'il fait chaque matin, et le lundi ?

**Chaque matin** (le détail est au §1) :
1. il clone les vivants ;
2. il lance `verifier_vivants.py` avec `--archives` **et `--domaines`** : dix contrôles, dont le contrôle 9 des
   checkpoints et le contrôle 10, leur taille ;
3. il juge les témoins à leur silence ;
4. il dépose **un chantier `pour:` par écart nouveau** — sauf le contrôle 9, **groupé en un seul chantier par domaine**
   (le contrôle 10 n'a qu'une ligne par domaine, donc un chantier par domaine aussi) ;
5. il archive les chantiers en recette depuis sept jours ;
6. il ajoute une ligne au journal, même sans écart ;
7. il pousse un seul commit et résume.

**Le lundi**, en plus (§1.4 ter) : il lit chaque checkpoint en entier, face aux décisions des sept derniers jours et aux
chantiers du domaine, et **ne relève que ce qu'une décision ou un chantier contredit**, en citant la phrase et la
preuve, sans avis. Un chantier `arbitre-lecture-<domaine>-<AAAAMMJJ>` par domaine relevé.

### 0.5 · Qu'est-ce qu'il ne fait jamais ?

**Il ne corrige rien, ne décide rien et n'écrit nulle part ailleurs que dans son journal, ses chantiers `pour:` et
l'archivage** (liste complète au §3).

### 0.6 · Comment l'installer, pas à pas, et qui fait quoi ?

Cinq gestes, tous au §4 (le tableau « qui fait quoi » est au §4.9) :
1. **le coordinateur** copie les trois scripts, `Archives/` et ce fichier dans les vivants ;
2. **le coordinateur** écrit la table des domaines (`Methode/domaines.yaml`) et vérifie que chaque checkpoint a sa
   section de file ; **chaque CdP** tient sa file au pas ;
3. **le coordinateur** amorce le journal et pousse ;
4. **le coordinateur ou le porteur** crée la tâche planifiée (heure décalée, prompt, push) ; **le porteur** installe
   l'application mobile et autorise ses notifications ;
5. **le coordinateur** lance le premier passage à la main et lit la ligne du journal et le commit.

### 0.7 · Qu'est-ce que ça coûte ?

- **Pour la machine** : un passage dure **une à deux minutes** ; il pousse **un commit par jour** (le journal, et
  `chantiers.yaml`, le tableau ou `Archives/` quand il y a des constats ou de l'archivage) ; la lecture du lundi coûte
  **quelques dizaines de milliers de jetons de plus**.
- **Pour le porteur** : rien au quotidien. Une ligne de journal par jour, à parcourir si l'on veut. Pour recevoir le
  push : l'application Claude sur le téléphone, ses notifications autorisées.
- **Pour les CdP** : ce qu'ils font déjà — lire après chaque `pull` les chantiers `pour:` qui les visent — et tenir leur
  file au pas des chantiers (une fois, au premier passage, s'ils étaient en retard).
- **Pour le coordinateur** : l'installation, une fois ; la table des domaines à tenir (une ligne par domaine) ; le
  jugement après une semaine.

### 0.8 · Comment lire ce qu'il produit ?

- **Le journal** (`Methode/ARBITRE_JOURNAL.md`) : une ligne par passage, même sans écart — **c'est la preuve qu'il a
  tourné**. Une ligne se lit champ par champ :
  ```
  - 2026-11-02 06:42 · 1 écart(s) · 2 constat(s) nouveau(x) · témoins frais · archivage : 0 daté(s), 3 archivé(s) · checkpoints : <domaine-1> · lecture : <domaine-2>
  ```
  la date et l'heure du passage ; le nombre de contrôles en écart ; le nombre de chantiers déposés ce jour ; le premier
  témoin silencieux (ou « témoins frais ») ; l'archivage ; les domaines signalés aux contrôles 9 et 10 (« à jour » quand il n'y
  en a aucun) ; et **le lundi seulement**, les domaines relevés à la lecture (« rien » sinon). Un jour sans écart :
  `… · 0 écart(s) · 0 constat(s) nouveau(x) · témoins frais · archivage : 0 daté(s), 0 archivé(s) · checkpoints : à jour`.
- **Le résumé** : la réponse finale de la session, visible dans la session de la tâche planifiée. Sans écart, une ligne :
  « Vivants conformes au <date> ».
- **Les chantiers** : un constat est un chantier `statut: a-cadrer`, `pour:` le CdP concerné (ou le coordinateur), à
  l'id reconnaissable — `arbitre-c<n>-<clé>` (contrôle `<n>`), `arbitre-c9-checkpoint-<domaine>-<date>` (le retard d'un
  checkpoint, un seul par domaine), `arbitre-c10-checkpoint-court-<domaine>-<date>` (un checkpoint au-delà de 10 Ko, un
  seul par domaine), `arbitre-lecture-<domaine>-<date>` (la lecture du lundi). Ils apparaissent dans le
  tableau (`chantiers.html`) ; le CdP visé les lit après son `pull`, corrige, passe le chantier en recette ; il sort
  vers `Archives/` sept jours plus tard.
- **Les notifications** : le push n'arrive que si la plateforme juge le passage « notable » ; **pas de notification ne
  veut pas dire pas de passage** — le journal fait foi (§4.6).

### 0.9 · Comment juger s'il faut le garder ?

Après une semaine d'essai (qui compte au moins un lundi), le coordinateur et le porteur choisissent : **garder**, **régler**
ou **arrêter** (§5). On regarde si le journal a une ligne chaque jour, si les constats étaient vrais, si les CdP en ont
fait quelque chose, si l'archivage n'a rien perdu et si le contrôle 9 tombe à « à jour » une fois les checkpoints remis
au pas. **Un faux positif se corrige dans la procédure, pas au cas par cas.**

---

## §1 · Ce que l'arbitre fait, dans l'ordre

1. **Le dépôt** : rattacher `<owner>/<Projet>` (outil `add_repo`, accès push), puis
   `git clone --depth 1 https://github.com/<owner>/<Projet> vivants` (un seul clone, délai de commande généreux).
   Tout ce qui suit se fait depuis ce clone, depuis sa racine.
2. **Le contrôle** :
   ```
   python3 -B <Dossier>/verifier_vivants.py --chantiers <Dossier>/chantiers.yaml \
     --registre <Dossier>/REGISTRE_ARBITRAGES_<P>.md --tableau <Dossier>/chantiers.html \
     --generateur <Dossier>/generer_tableau.py --journal <Dossier>/PLAN_<P>.md --archives <Dossier>/Archives \
     --domaines Methode/domaines.yaml
   ```
   Avec `--archives`, les contrôles 3 et 7 lisent aussi les archives (sinon l'archivage ferait un faux écart quinze
   jours après le dernier lot). Avec `--domaines`, le **contrôle 9 « checkpoints »** lit la table des domaines : pour
   chaque domaine, il ouvre le checkpoint, en prend la section de file et la recoupe avec `chantiers.yaml`. Deux
   écarts : **9b**, la file cite un chantier clos (en recette ou archivé) ; **9c**, un chantier ouvert du domaine (à
   venir, à cadrer, dette, en vol — hors messages `pour:`) que le checkpoint ne cite pas entre accents graves. Un
   `file:` vide dans la table est aussi un écart **du domaine** (« aucune section de file déclarée ») : le CdP donne à son
   checkpoint sa section `## §<n> · La file` et la ligne `file:` qui la nomme. Un défaut
   de la table elle-même (checkpoint ou section de file introuvable, entrée sans domaine ou sans checkpoint) est aussi un
   écart. Le **contrôle 10** mesure la taille de chaque checkpoint : au-delà de 10 240 octets (le plafond par défaut,
   `--plafond-checkpoint`), une ligne « <domaine> : <chemin> pèse <n> octets, plafond <p> ». Les chemins de la table se
   lisent depuis la racine du clone : lancé d'ailleurs, ajouter `--racine <le clone>`.
   Code 0 : rien à signaler par ce contrôle. Code 1 : des écarts, une ligne indentée par cas sous le contrôle en
   ÉCART. Code 2 : un fichier manque ou a changé de nom — le dire au journal (§1.5) et dans le résumé, rien d'autre.
3. **Les témoins**, en plus : la ligne « Session en activité » de chaque checkpoint de domaine (table de
   `Methode/METHODE_<P>.md` §1 bis). **Un témoin ne se juge pas à son âge** — une session peut vivre plusieurs jours en
   attendant un geste du porteur — **mais à son silence** :
   ```
   git fetch --depth 300 origin main
   git log origin/main -1 --format=%cI --grep=<identifiant du témoin>
   ```
   `--grep` lit tout le message du commit, lignes d'attribution comprises : ⟨**le témoin est les huit derniers caractères
   de l'identifiant de la session** — celui de la ligne d'attribution de session de ses commits, quand la plateforme en
   ajoute une à chaque commit ; on cherche **cette suite entière, jamais le début** de l'identifiant, que toutes les
   sessions d'un même compte partagent ; sans ligne d'attribution, convenir d'une marque que chaque CdP met dans ses
   messages⟩. **Aucun commit de cette session depuis plus de 24 heures** — ou aucun du tout, et un témoin posé il y
   a plus de 24 heures — est un **constat** (une session oubliée ou morte), adressé au coordinateur ; la mesure s'écrit
   dans le chantier, avec la date du dernier commit (« dernier commit le … »). Un témoin libre (« aucune — libre
   depuis … ») ne se contrôle pas.
4. **Un chantier par écart nouveau** : pour chaque cas (une ligne indentée sous un contrôle en ÉCART — **sauf le
   contrôle 9, groupé plus bas, et le contrôle 10, qui a son propre id** — et chaque témoin silencieux), une entrée **en fin** de `<Dossier>/chantiers.yaml` :
   ```
   - id: arbitre-c<n>-<clé>
     titre: <le cas, en une ligne>
     module: <module du chantier en cause, sinon methode>
     categorie: doc
     statut: a-cadrer
     pour: <CdP, §2>
     priorite: moyen
     complexite: faible
     cout: aucun ; une correction dans les vivants
     mesure: Signalé par l'arbitre le <date> (contrôle <n>). <la ligne de verifier_vivants.py, telle quelle>. <ce qu'il faut faire, en une phrase>.
     refs: Methode/ARBITRE.md
   ```
   `<n>` : le numéro du contrôle (⟨`t` pour les témoins⟩) ; `<clé>` : l'id du chantier en cause, ou `R<n>`, ou
   `tableau`, `journal`, `temoin-<domaine>`. **Si un chantier de même `id` existe déjà, ne rien ajouter** : le constat
   est déjà signalé — il compte parmi « déjà signalés et toujours là » dans le résumé. Un chantier peut avoir été
   archivé : le chercher par `archiver_chantiers.py chercher <id>` (mêmes `--chantiers` et `--archives` qu'au 4 bis) ;
   **un id archivé ne se réutilise pas** — si le cas revient après sa correction, déposer un nouveau chantier dont l'id
   ajoute `-<AAAAMMJJ>` (la date du passage).

   **Le contrôle 9, groupé par domaine** : ses lignes ne font pas un chantier chacune. Pour chaque domaine qui a au
   moins une ligne, **un seul** chantier `arbitre-c9-checkpoint-<domaine>-<AAAAMMJJ>`, `pour:` le `cdp` du domaine dans
   `Methode/domaines.yaml`, module `methode`, titre « Le checkpoint de <domaine> est en retard sur ses chantiers », la
   `mesure` portant **toutes** les lignes du domaine telles quelles (mises bout à bout sur la même ligne, séparées par
   « ; »), puis « citer chaque chantier ouvert de ton domaine par son id dans ton checkpoint, retirer de ta file les
   chantiers clos (méthode §6) ». **Si un chantier `arbitre-c9-checkpoint-<domaine>-*` existe déjà sans être en
   recette, ne rien ajouter** pour ce domaine : le CdP n'a pas encore repris. **Un défaut de la table elle-même** —
   checkpoint introuvable, section de file introuvable, entrée sans domaine ou sans checkpoint — ne va pas au CdP : la
   table est au coordinateur. Toutes ces lignes font **un seul** chantier `arbitre-c9-table-<AAAAMMJJ>`, `pour:` le
   coordinateur, jamais redéposé tant qu'un `arbitre-c9-table-*` est ouvert (le CdP a peut-être renommé son checkpoint ou
   sa section : le coordinateur aligne la table, ou demande au CdP de revenir au titre convenu).

   **Le contrôle 10, un chantier par domaine** : pour chaque ligne « <domaine> : <chemin> pèse <n> octets, plafond <p> »,
   un chantier `arbitre-c10-checkpoint-court-<domaine>-<AAAAMMJJ>`, `pour:` le `cdp` du domaine dans
   `Methode/domaines.yaml`, module `methode`, titre « Le checkpoint de <domaine> dépasse son plafond de 10 Ko », la
   `mesure` portant la ligne telle quelle puis « faire partir l'historique à une archive du domaine pour revenir sous
   10 Ko (méthode §6) ». **Si un chantier `arbitre-c10-checkpoint-court-<domaine>-*` existe déjà sans être en recette, ne
   rien ajouter** pour ce domaine : le CdP n'a pas encore repris.

   Puis régénérer le tableau (`python3 -B <Dossier>/generer_tableau.py <Dossier>/chantiers.yaml <Dossier>/chantiers.html`)
   et relancer le contrôle : le contrôle du tableau doit être OK. Le commit se fait au §1.5.
4 bis. **L'archivage, après les constats** — la seule écriture mécanique de l'arbitre, jamais une correction à la main :
   ```
   python3 -B <Dossier>/archiver_chantiers.py archiver --chantiers <Dossier>/chantiers.yaml \
     --archives <Dossier>/Archives
   ```
   La commande date `recette-le: <date du jour>` toute entrée qui vient d'entrer en recette, retire la date d'une entrée
   rouverte, et sort vers `Archives/CHANTIERS_<AAAA-MM>.yaml` (le mois du jour : on n'y fait qu'ajouter, figé à la fin du
   mois) toute entrée en recette depuis sept jours ou plus (le délai par défaut : **ne pas passer `--delai`**) ; elle contrôle l'absence de perte avant d'écrire, et relancée à
   la même date elle ne change rien. Code 0 : fait, avec ou sans changement. Code 1 : fait, avec un avertissement — une
   date `recette-le:` illisible, que la commande n'archive ni ne modifie : un chantier `pour:` le coordinateur, comme au 4
   (⟨`a`⟩ pour le contrôle, `archivage-<id>` pour la clé, la ligne de la commande telle quelle). Code 2 : appel invalide,
   fichier ou dossier introuvable, contrôle sans perte en défaut — **rien n'est écrit** : le dire au journal (§1.5) et
   dans le résumé, rien d'autre. Si la commande a daté ou archivé, **régénérer le tableau** (même commande qu'au 4) et
   **relancer le contrôle du 2** (avec `--archives` et `--domaines`) : il doit rester sans écart nouveau.
4 ter. **La lecture des checkpoints, le lundi seulement** (`TZ=<fuseau> date +%u` vaut `1` ; les autres jours, rien) :
   lire **chaque checkpoint** de `Methode/domaines.yaml` **en entier**, face (a) aux entrées du registre des **sept
   derniers jours** (les dates sont dans le texte de chaque décision) et (b) aux chantiers de son domaine. Relever
   **seulement** ce qui se prouve par une citation :
   - une phrase que contredit une décision ou un chantier — un domaine rattaché, une règle changée, un sujet clos encore
     annoncé, un nom de CdP ou de fichier qui a changé ;
   - un sujet de la file écrit en clair, sans chantier.

   Chaque relevé : la phrase du checkpoint entre guillemets, et la décision ou l'id qui la contredit. **Pas d'avis**, pas
   de style, pas de « on pourrait ». Pour chaque domaine qui a au moins un relevé, **un seul** chantier
   `arbitre-lecture-<domaine>-<AAAAMMJJ>`, `pour:` son `cdp`, module `methode`, titre « Le checkpoint de <domaine> contredit
   les vivants », les relevés dans la `mesure` (sur une ligne, séparés par « ; »). **Si un chantier
   `arbitre-lecture-<domaine>-*` existe déjà sans être en recette, ne rien ajouter** pour ce domaine : le relevé de la
   semaine passée attend encore son CdP. Puis régénérer le tableau et relancer le
   contrôle du 2, comme au 4.
5. **Le journal, à chaque passage, même sans écart** : une ligne ajoutée **en fin** de `Methode/ARBITRE_JOURNAL.md`,
   jamais une ligne réécrite :
   ```
   - <AAAA-MM-JJ HH:MM> · <n> écart(s) · <n> constat(s) nouveau(x) · <le premier témoin silencieux depuis plus de 24 h, ou « témoins frais »> · archivage : <n> daté(s), <m> archivé(s) · checkpoints : <domaines signalés aux contrôles 9 et 10, ou « à jour »>
   ```
   `<n> écart(s)` est le nombre que donne la dernière ligne du contrôle (« VIVANTS · <n> écart(s) »). Le lundi, la ligne ajoute **à la fin** ` · lecture : <domaines relevés, ou « rien »>` ; les autres jours, rien. Un
   « constat nouveau » est un chantier déposé ce jour (les entrées que l'archivage date ou sort ne comptent pas). L'heure est celle
   du porteur (`TZ=<fuseau> date '+%F %H:%M'`) ; un code 2 du contrôle s'écrit « contrôle impossible : <fichier> », un
   code 2 de l'archivage « archivage : impossible, <message> ». Puis **un seul commit** : « Arbitre
   <date> : vivants conformes » (le journal seul) ou « Arbitre <date> : <n> constat(s) » (le journal, `chantiers.yaml`,
   `chantiers.html`) ; quand l'archivage a daté ou archivé, le message ajoute « , archivage : <n> daté(s), <m> archivé(s) »
   et le commit porte aussi `chantiers.yaml`, `chantiers.html` et `Archives/` ; `git fetch origin main`, rebaser,
   pousser. Un push refusé : `git pull --rebase`, un seul nouvel essai ; un conflit : rien n'est forcé, le dire dans
   le résumé. **C'est ce journal qui prouve que l'arbitre a tourné** — pas la notification (§4.6).
6. **Le résumé** : la réponse finale de la session, courte — la date, le nombre d'écarts, les constats nouveaux (un par
   ligne, avec le CdP visé), ceux déjà signalés et toujours là, l'archivage (« <n> daté(s), <m> archivé(s) »), les
   domaines signalés aux contrôles 9 et 10 et, le lundi, ceux relevés à la lecture, le commit poussé. Sans écart : « Vivants
   conformes au <date> », une ligne.

---

## §2 · À qui adresser un constat

| ce qui est en cause | `pour:` |
|---|---|
| un chantier d'un domaine (son `module:`) | le CdP de ce domaine (table de la méthode §1 bis) ⟨une ligne par domaine, au besoin⟩ |
| un chantier en vol | le `cdp:` qu'il porte, s'il en porte un ; sinon le CdP de son module |
| un écart sur un livrable ou une ressource partagée (deux lots en vol) | les CdP des lots en cause, un chantier chacun |
| le retard d'un checkpoint (contrôle 9) ; sa taille (contrôle 10) ; la lecture du lundi | le `cdp` du domaine dans `Methode/domaines.yaml`, un chantier par domaine |
| un module sans CdP ouvert | le coordinateur |
| tout le reste : registre, tableau, journal du plan, journal de l'arbitre, témoins, table des domaines, `methode` | le coordinateur |

---

## §3 · Ce que l'arbitre ne fait jamais

- Corriger une entrée, un numéro, un checkpoint, un témoin ou la table des domaines : il signale, le propriétaire
  corrige. **Seule exception, mécanique : l'archivage** (§1.4 bis) — `archiver_chantiers.py` date, dédate et sort les
  entrées en recette ; l'arbitre ne touche jamais à la main une entrée en recette ni une ligne `recette-le:`.
- Écrire ailleurs qu'en fin de `chantiers.yaml`, dans `chantiers.html` régénéré, en fin d'`ARBITRE_JOURNAL.md`, et ce
  que fait `archiver_chantiers.py` (les lignes `recette-le:`, les entrées sorties, `Archives/CHANTIERS_<AAAA-MM>.yaml`).
- Juger un checkpoint sur le style ou l'opportunité : la lecture du lundi ne relève que ce qu'une décision ou un chantier
  contredit, avec la citation et la preuve.
- Réserver un numéro de décision, prendre un livrable ou une ressource, cadrer, lancer un dev.
- Ouvrir une autre session, envoyer un message hors du dépôt (messagerie, e-mail écrit par lui).
- Pousser plus d'un commit par passage, ou forcer un push.

---

## §4 · La tâche planifiée — la configuration, pas à pas

*Pour le coordinateur et le porteur ; la session de l'arbitre ne lit pas ce §.*

1. **Avant** : `verifier_vivants.py`, `archiver_chantiers.py` et `generer_tableau.py` copiés dans les vivants ;
   **la table des domaines `Methode/domaines.yaml` créée** (modèle `modeles/domaines.yaml` : une entrée par CdP,
   **la coordination comprise**, le début exact du titre de la section de file de chaque checkpoint dans `file:`) et **chaque checkpoint pourvu de cette
   section** (modèle `modeles/CHECKPOINT.md`) ; `Archives/` créé (git ne suit pas un dossier vide : un fichier vide
   `Archives/.gitkeep`) ; ce fichier copié en `Methode/ARBITRE.md` et adapté ; `Methode/ARBITRE_JOURNAL.md` amorcé,
   poussé :
   ```
   # Journal de l'arbitre des vivants

   *Une ligne par passage, ajoutée en fin par la tâche « Arbitre des vivants » (`Methode/ARBITRE.md` §1.5). Jamais
   réécrit. Format : date et heure · écarts · constats nouveaux · témoins · archivage · checkpoints · lecture (le lundi).*
   ```
   **Qui tient la table des domaines** : le coordinateur, au pas de la table de la méthode §1 bis — **à chaque domaine
   ouvert ou fermé, et à chaque section de file renommée**. Une table en retard fait un écart au contrôle 9.
2. **Qui la crée** : le coordinateur, depuis sa session (l'outil de création de tâche planifiée), ou le porteur, depuis
   sa liste de tâches planifiées. Nom : « Arbitre des vivants ». **Une session neuve à chaque passage**, Opus.
3. **L'heure** : une heure fixe chaque matin, dans le fuseau du porteur, **décalée de l'heure ronde** (par exemple
   6 h 42 — en cron `CRON_TZ=<fuseau> 42 6 * * *`) : les tâches lancées à l'heure pile se bousculent et partent en
   retard. Assez tôt pour que le journal soit là quand le porteur et les CdP commencent.
4. **Le dépôt** : rattaché en accès push **par le prompt lui-même** — le prompt nomme le dépôt en toutes lettres, ce
   qui vaut la demande que le garde-fou d'une session exige avant un rattachement. **Les passages ne doivent pas
   attendre d'approbation** : personne n'est là pour la donner ; régler l'approbation automatique dans les réglages de
   la tâche, si l'organisation le permet, sinon le passage s'arrête au premier geste à approuver.
5. **Le prompt**, à recopier une fois les `<…>` remplis :
   ```
   Tu es l'arbitre des vivants du projet <Projet>, une session de lecture et de signalement seuls. Rattache le dépôt
   privé <owner>/<Projet> (outil add_repo, accès push), clone-le avec
   `git clone --depth 1 https://github.com/<owner>/<Projet> vivants` (un seul clone, délai de commande de 10 minutes),
   puis lis `Methode/ARBITRE.md` en entier et suis-le à la lettre : contrôle par `verifier_vivants.py` (avec
   `--archives` et `--domaines`), un chantier `pour:` par écart nouveau (jamais en double) — celui du contrôle des
   checkpoints groupé en un seul par domaine —, témoins des checkpoints jugés à leur silence, chantiers en recette
   archivés par `archiver_chantiers.py`, tableau régénéré, le lundi seulement la lecture des checkpoints face aux
   décisions de la semaine, une ligne en fin de `Methode/ARBITRE_JOURNAL.md` à chaque passage, même sans écart, un seul
   commit poussé. Tu ne corriges rien d'autre ; tu ne réserves aucun numéro, ne prends aucun livrable, ne lances aucun
   dev, n'ouvres aucune autre session et n'envoies aucun message ailleurs. Les commits se terminent par la ligne
   `Co-Authored-By: Claude <noreply@anthropic.com>`. Ta réponse finale est le résumé pour le porteur, en français et
   court : la date, le nombre d'écarts, les constats nouveaux (un par ligne, avec le CdP visé), ceux déjà signalés et
   toujours présents, l'archivage, les domaines signalés au contrôle des checkpoints et, le lundi, ceux relevés à la
   lecture, le commit poussé ; sans écart, une seule ligne « Vivants conformes au <date> ».
   ```
   Le prompt ne change pas quand la procédure change : il la lit. (Il ne change que si la procédure gagne ou perd une
   famille de gestes, comme ici le contrôle des checkpoints et la lecture du lundi.)
6. **Les notifications** : dans l'onglet Notifications de la tâche, **cocher push** — l'application Claude installée et
   connectée sur le téléphone du porteur, ses notifications autorisées par le système. **L'e-mail peut ne pas arriver**
   (constaté : un passage réussi, avec des constats, sans aucun e-mail), et **la plateforme décide seule si un passage
   est « notable »** : un passage sans rien de neuf n'envoie souvent rien. **Le journal est la preuve qu'il a tourné**,
   pas la notification : une ligne par jour, ou rien.
7. **Le premier passage** se lance à la main, le jour de la création ; le coordinateur vérifie la ligne du journal et
   le commit. **Sur un projet déjà avancé, le premier contrôle 9 est bavard** : tous les chantiers ouverts que les
   checkpoints ne citent pas encore tombent d'un coup (quinze lignes sur le premier essai, dans six domaines : six chantiers —
   un par domaine, d'où le groupement). Le premier contrôle 10 l'est aussi : les checkpoints déjà au-delà de 10 Ko tombent d'un coup, un
   chantier par domaine. Prévenir les CdP avant, ou accepter ce premier lot de chantiers : ensuite, les contrôles 9 et 10
   ne signalent plus que le nouveau. Ensuite, chaque matin, une ligne de plus.
8. **Un passage manqué** (pas de ligne au journal) : une limite d'utilisation peut faire échouer un passage matinal ;
   si ça se répète, déplacer l'heure. Un échec isolé ne se rattrape pas : le passage suivant contrôle tout.
9. **Qui fait quoi** — la liste de contrôle :

   | geste | qui | fait quand | preuve que c'est fait |
   |---|---|---|---|
   | copier `verifier_vivants.py`, `archiver_chantiers.py`, `generer_tableau.py` dans les vivants ; créer `Archives/` | coordinateur | avant | les fichiers au dépôt, `Archives/.gitkeep` |
   | écrire `Methode/domaines.yaml`, une entrée par CdP, la coordination comprise | coordinateur | avant | le contrôle 9 se lance sans défaut de table |
   | donner à chaque checkpoint sa section de file, chaque sujet cité par son id | chaque CdP | avant le premier passage, puis à chaque reprise et passation | le contrôle 9 ne signale plus son domaine |
   | copier et adapter `Methode/ARBITRE.md` ; amorcer `Methode/ARBITRE_JOURNAL.md` ; pousser | coordinateur | avant | les deux fichiers au dépôt |
   | créer la tâche planifiée (nom, heure décalée, prompt, session neuve) ; régler l'approbation automatique | coordinateur ou porteur | le jour 1 | la tâche dans la liste des tâches planifiées |
   | installer l'application mobile, autoriser ses notifications ; cocher push | porteur | le jour 1 | un passage notable arrive en notification |
   | prévenir les CdP qu'ils recevront des chantiers `pour:` de l'arbitre | coordinateur | avant le premier passage | un message prêt à coller, remis au porteur |
   | lancer le premier passage à la main ; vérifier la ligne du journal et le commit | coordinateur | le jour 1 | la ligne et le commit « Arbitre <date> … » |
   | lire les chantiers `pour:` qui le visent après chaque `pull` ; corriger | chaque CdP | en continu | le chantier passe en recette |
   | tenir la table des domaines : domaine ouvert, fermé, section de file renommée | coordinateur | à chaque changement | pas d'écart « table » au contrôle 9 |
   | parcourir le journal ; juger **garder, régler, arrêter** | coordinateur et porteur | après la semaine d'essai (§5) | la décision, écrite |

---

## §5 · L'essai et le jugement

- **Une semaine d'essai**, du <date> au <date> — **elle doit compter un lundi**, pour que la première lecture des
  checkpoints soit jugée —, puis le coordinateur juge avec le porteur : **garder, régler ou arrêter**. Les éléments : le
  journal (a-t-il tourné chaque jour ?), les constats (vrais ou faux), ce que les CdP en ont fait, **l'archivage** (les
  entrées sorties étaient-elles bien finies, rien ne manque-t-il aux vivants — `archiver_chantiers.py chercher` —, le
  contrôle reste-t-il sans écart avec `--archives` ?), **le contrôle 9** (les lignes étaient-elles vraies : un chantier
  ouvert réellement absent du checkpoint, un chantier clos réellement cité ? les CdP ont-ils remis leur file au pas, le
  contrôle tombe-t-il à « à jour » ?), **le contrôle 10** (les checkpoints signalés étaient-ils vraiment au-delà de
  10 Ko, et sont-ils revenus dessous une fois leur historique archivé ?) **et la première lecture du lundi** (chaque relevé portait-il une citation et une
  preuve ? y a-t-il eu un avis déguisé ou un faux relevé ?).
- **Un faux positif se corrige dans la procédure, pas au cas par cas.** Exemple vécu : la première règle des témoins
  jugeait leur âge (« pris depuis plus de 24 heures ») ; elle a signalé deux sessions bien vivantes qui attendaient le
  porteur. La règle est devenue celle du silence (§1.3).
- Une évolution de la procédure change ce fichier (version en tête), pas le prompt de la tâche — sauf si la procédure gagne
  ou perd une famille de gestes (§4.5).
