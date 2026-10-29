# L'ARBITRE DES VIVANTS — <Projet> · v2
### <date> · <session de coordination> · lu par la tâche planifiée quotidienne · tiré du package méthode CdP

*Une session neuve, lancée chaque matin par une tâche planifiée, qui contrôle les vivants partagés et **signale sans
corriger** : elle lit, elle dépose des chantiers `pour:`, elle **archive** les chantiers en recette (sa seule écriture
mécanique), elle tient un journal, elle résume. Elle ne réserve aucun numéro, ne prend aucun livrable, ne lance aucun
dev, n'envoie aucun message ailleurs.*

> **Mode d'emploi du modèle** — facultatif : utile quand plusieurs CdP écrivent les mêmes vivants (`LISEZ_MOI.md`
> §2 bis du package : inutile en A, facultatif en B, recommandé en C). Le coordinateur le copie en
> `Methode/ARBITRE.md` du dépôt des vivants, remplit les `<…>` et adapte les `⟨…⟩` (chemins, table du §2), amorce
> `Methode/ARBITRE_JOURNAL.md` (§1.5), crée `Archives/` et crée la tâche planifiée (§4). Les §1 à §3 sont la procédure
> que la session suit à la lettre ; les §4 et §5 servent au coordinateur et au porteur. Supprimer cet encadré.

---

## §0 · Ce qu'il est, et ce qu'il voit

- **Une session de lecture et de signalement**, sans mémoire d'un passage à l'autre : tout se reconstitue depuis
  le dépôt des vivants. Elle n'est ni un CdP ni le coordinateur : **elle ne corrige rien**, le propriétaire corrige.
  **Une seule écriture, mécanique : l'archivage** des chantiers en recette (§1.4 bis), par `archiver_chantiers.py` —
  jamais à la main.
- **Ce qu'elle voit** : ce que personne ne voit autrement, puisque chaque CdP ne lit que son domaine — des numéros de
  décision en double ou un trou, des identifiants de chantier en double (vivants ou archivés), un chantier en vol sans
  `cdp:`, deux lots en vol sur un même livrable ou une même ressource, un tableau qui ne correspond plus au yaml, un
  journal du plan en avance sur les chantiers (`verifier_vivants.py`) ; et **les sessions oubliées** qui gardent un
  témoin.
- **Ce qu'elle ne voit pas** : la qualité d'une décision, l'état du code, la production. Elle ne juge que la forme des
  vivants partagés.
- **Ses traces** : un chantier par écart nouveau (§1.4), l'archivage (§1.4 bis), une ligne de journal par passage
  (§1.5), un résumé (§1.6).

---

## §1 · Ce que l'arbitre fait, dans l'ordre

1. **Le dépôt** : rattacher `<owner>/<Projet>` (outil `add_repo`, accès push), puis
   `git clone --depth 1 https://github.com/<owner>/<Projet> vivants` (un seul clone, délai de commande généreux).
   Tout ce qui suit se fait depuis ce clone.
2. **Le contrôle** :
   ```
   python3 -B <Dossier>/verifier_vivants.py --chantiers <Dossier>/chantiers.yaml \
     --registre <Dossier>/REGISTRE_ARBITRAGES_<P>.md --tableau <Dossier>/chantiers.html \
     --generateur <Dossier>/generer_tableau.py --journal <Dossier>/PLAN_<P>.md --archives <Dossier>/Archives
   ```
   Avec `--archives`, les contrôles 3 et 7 lisent aussi les archives (sinon l'archivage ferait un faux écart quinze
   jours après le dernier lot). Code 0 : rien à signaler par ce contrôle. Code 1 : des écarts, une ligne indentée par cas sous le contrôle en
   ÉCART. Code 2 : un fichier manque ou a changé de nom — le dire au journal (§1.5) et dans le résumé, rien d'autre.
3. **Les témoins**, en plus : la ligne « Session en activité » de chaque checkpoint de domaine (table de
   `Methode/METHODE_<P>.md` §1 bis). **Un témoin ne se juge pas à son âge** — une session peut vivre plusieurs jours en
   attendant un geste du porteur — **mais à son silence** :
   ```
   git fetch --depth 300 origin main
   git log origin/main -1 --format=%cI --grep=<identifiant du témoin>
   ```
   `--grep` lit tout le message du commit, lignes d'attribution comprises : ⟨l'identifiant court du témoin y figure
   quand la plateforme ajoute un lien de session à chaque commit ; sinon, convenir d'une marque que chaque CdP met dans
   ses messages⟩. **Aucun commit de cette session depuis plus de 24 heures** — ou aucun du tout, et un témoin posé il y
   a plus de 24 heures — est un **constat** (une session oubliée ou morte), adressé au coordinateur ; la mesure s'écrit
   dans le chantier, avec la date du dernier commit (« dernier commit le … »). Un témoin libre (« aucune — libre
   depuis … ») ne se contrôle pas.
4. **Un chantier par écart nouveau** : pour chaque cas (une ligne indentée sous un contrôle en ÉCART, et chaque témoin
   silencieux), une entrée **en fin** de `<Dossier>/chantiers.yaml` :
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
   ajoute `-<AAAAMMJJ>` (la date du passage). Puis régénérer le tableau
   (`python3 -B <Dossier>/generer_tableau.py <Dossier>/chantiers.yaml <Dossier>/chantiers.html`) et relancer le
   contrôle : le contrôle du tableau doit être OK.
4 bis. **L'archivage, après les constats** — la seule écriture mécanique de l'arbitre, jamais une correction à la main :
   ```
   python3 -B <Dossier>/archiver_chantiers.py archiver --chantiers <Dossier>/chantiers.yaml \
     --archives <Dossier>/Archives
   ```
   La commande date `recette-le: <date du jour>` toute entrée qui vient d'entrer en recette, retire la date d'une entrée
   rouverte, et sort vers `Archives/CHANTIERS_<AAAA-MM>.yaml` (le mois du jour : on n'y fait qu'ajouter, figé à la fin du
   mois) toute entrée en recette depuis 15 jours ou plus ; elle contrôle l'absence de perte avant d'écrire, et relancée à
   la même date elle ne change rien. Code 0 : fait, avec ou sans changement. Code 1 : fait, avec un avertissement — une
   date `recette-le:` illisible, que la commande n'archive ni ne modifie : un chantier `pour:` le coordinateur, comme au 4
   (⟨`a`⟩ pour le contrôle, `archivage-<id>` pour la clé, la ligne de la commande telle quelle). Code 2 : appel invalide,
   fichier ou dossier introuvable, contrôle sans perte en défaut — **rien n'est écrit** : le dire au journal (§1.5) et
   dans le résumé, rien d'autre. Si la commande a daté ou archivé, **régénérer le tableau** (même commande qu'au 4) et
   **relancer le contrôle du 2** (avec `--archives`) : il doit rester sans écart nouveau.
5. **Le journal, à chaque passage, même sans écart** : une ligne ajoutée **en fin** de `Methode/ARBITRE_JOURNAL.md`,
   jamais une ligne réécrite :
   ```
   - <AAAA-MM-JJ HH:MM> · <n> écart(s) · <n> constat(s) nouveau(x) · <le premier témoin silencieux depuis plus de 24 h, ou « témoins frais »> · archivage : <n> daté(s), <m> archivé(s)
   ```
   L'heure est celle du porteur (`TZ=<fuseau> date '+%F %H:%M'`) ; un code 2 du contrôle s'écrit « contrôle impossible :
   <fichier> », un code 2 de l'archivage « archivage : impossible, <message> ». Puis **un seul commit** : « Arbitre
   <date> : vivants conformes » (le journal seul) ou « Arbitre <date> : <n> constat(s) » (le journal, `chantiers.yaml`,
   `chantiers.html`) ; quand l'archivage a daté ou archivé, le message ajoute « , archivage : <n> daté(s), <m> archivé(s) »
   et le commit porte aussi `chantiers.yaml`, `chantiers.html` et `Archives/` ; `git fetch origin main`, rebaser,
   pousser. Un push refusé : `git pull --rebase`, un seul nouvel essai ; un conflit : rien n'est forcé, le dire dans
   le résumé. **C'est ce journal qui prouve que l'arbitre a tourné** — pas la notification (§4.6).
6. **Le résumé** : la réponse finale de la session, courte — la date, le nombre d'écarts, les constats nouveaux (un par
   ligne, avec le CdP visé), ceux déjà signalés et toujours là, l'archivage (« <n> daté(s), <m> archivé(s) »), le commit
   poussé. Sans écart : « Vivants conformes au <date> », une ligne.

---

## §2 · À qui adresser un constat

| ce qui est en cause | `pour:` |
|---|---|
| un chantier d'un domaine (son `module:`) | le CdP de ce domaine (table de la méthode §1 bis) ⟨une ligne par domaine, au besoin⟩ |
| un chantier en vol | le `cdp:` qu'il porte, s'il en porte un ; sinon le CdP de son module |
| un écart sur un livrable ou une ressource partagée (deux lots en vol) | les CdP des lots en cause, un chantier chacun |
| un module sans CdP ouvert | le coordinateur |
| tout le reste : registre, tableau, journal du plan, journal de l'arbitre, témoins, `methode` | le coordinateur |

---

## §3 · Ce que l'arbitre ne fait jamais

- Corriger une entrée, un numéro, un checkpoint ou un témoin : il signale, le propriétaire corrige. **Seule exception,
  mécanique : l'archivage** (§1.4 bis) — `archiver_chantiers.py` date, dédate et sort les entrées en recette ; l'arbitre
  ne touche jamais à la main une entrée en recette ni une ligne `recette-le:`.
- Écrire ailleurs qu'en fin de `chantiers.yaml`, dans `chantiers.html` régénéré, en fin d'`ARBITRE_JOURNAL.md`, et ce
  que fait `archiver_chantiers.py` (les lignes `recette-le:`, les entrées sorties, `Archives/CHANTIERS_<AAAA-MM>.yaml`).
- Réserver un numéro de décision, prendre un livrable ou une ressource, cadrer, lancer un dev.
- Ouvrir une autre session, envoyer un message hors du dépôt (messagerie, e-mail écrit par lui).
- Pousser plus d'un commit par passage, ou forcer un push.

---

## §4 · La tâche planifiée — la configuration, pas à pas

*Pour le coordinateur et le porteur ; la session de l'arbitre ne lit pas ce §.*

1. **Avant** : `verifier_vivants.py`, `archiver_chantiers.py` et `generer_tableau.py` copiés dans les vivants ;
   `Archives/` créé (git ne suit pas un dossier vide : un fichier vide `Archives/.gitkeep`) ; ce fichier copié en
   `Methode/ARBITRE.md` et adapté ; `Methode/ARBITRE_JOURNAL.md` amorcé, poussé :
   ```
   # Journal de l'arbitre des vivants

   *Une ligne par passage, ajoutée en fin par la tâche « Arbitre des vivants » (`Methode/ARBITRE.md` §1.5). Jamais
   réécrit. Format : date et heure · écarts · constats nouveaux · témoins · archivage.*
   ```
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
   puis lis `Methode/ARBITRE.md` en entier et suis-le à la lettre : contrôle par `verifier_vivants.py`, témoins des
   checkpoints jugés à leur silence, un chantier `pour:` par écart nouveau (jamais en double), chantiers en recette
   archivés par `archiver_chantiers.py`, tableau régénéré, une ligne en fin de `Methode/ARBITRE_JOURNAL.md` à chaque
   passage, même sans écart, un seul commit poussé. Tu ne corriges rien d'autre ; tu ne réserves aucun numéro, ne prends aucun livrable, ne lances aucun dev, n'ouvres aucune
   autre session et n'envoies aucun message ailleurs. Les commits se terminent par la ligne
   `Co-Authored-By: Claude <noreply@anthropic.com>`. Ta réponse finale est le résumé pour le porteur, en français et
   court : la date, le nombre d'écarts, les constats nouveaux (un par ligne, avec le CdP visé), ceux déjà signalés et
   toujours présents, l'archivage, le commit poussé ; sans écart, une seule ligne « Vivants conformes au <date> ».
   ```
   Le prompt ne change pas quand la procédure change : il la lit.
6. **Les notifications** : dans l'onglet Notifications de la tâche, **cocher push** — l'application Claude installée et
   connectée sur le téléphone du porteur, ses notifications autorisées par le système. **L'e-mail peut ne pas arriver**
   (constaté : un passage réussi, avec des constats, sans aucun e-mail), et **la plateforme décide seule si un passage
   est « notable »** : un passage sans rien de neuf n'envoie souvent rien. **Le journal est la preuve qu'il a tourné**,
   pas la notification : une ligne par jour, ou rien.
7. **Le premier passage** se lance à la main, le jour de la création ; le coordinateur vérifie la ligne du journal et
   le commit. Ensuite, chaque matin, une ligne de plus.
8. **Un passage manqué** (pas de ligne au journal) : une limite d'utilisation peut faire échouer un passage matinal ;
   si ça se répète, déplacer l'heure. Un échec isolé ne se rattrape pas : le passage suivant contrôle tout.

---

## §5 · L'essai et le jugement

- **Une semaine d'essai**, du <date> au <date>, puis le coordinateur juge avec le porteur : **garder, régler ou
  arrêter**. Les éléments : le journal (a-t-il tourné chaque jour ?), les constats (vrais ou faux), ce que les CdP en
  ont fait, **et l'archivage** : les entrées sorties étaient-elles bien finies, rien ne manque-t-il aux vivants
  (`archiver_chantiers.py chercher`), le contrôle reste-t-il sans écart avec `--archives` ?
- **Un faux positif se corrige dans la procédure, pas au cas par cas.** Exemple vécu : la première règle des témoins
  jugeait leur âge (« pris depuis plus de 24 heures ») ; elle a signalé deux sessions bien vivantes qui attendaient le
  porteur. La règle est devenue celle du silence (§1.3).
- Une évolution de la procédure change ce fichier (version en tête), jamais le prompt de la tâche.
