# L'ARBITRE DES VIVANTS — <Projet> · v6
### <date> · <session de coordination> · tiré du package méthode CdP v20

***L'arbitre est une action GitHub**, `.github/workflows/arbitre.yml` : chaque jour, sans session, elle lance
`<Dossier>/arbitre.py`, commite et pousse au nom de `github-actions[bot]`, puis **échoue si elle a déposé un
chantier nouveau** — c'est l'e-mail de GitHub qui prévient le porteur ; son résumé est dans la page du passage. Elle
mesure, elle ne juge pas : **le jugement des documents est au contrôleur** ([CONTROLEUR.md](CONTROLEUR.md)). Ce document
dit ce que le script fait, dans l'ordre ; il ne s'exécute pas, il se lit.*

> **Mode d'emploi du modèle** — facultatif : utile quand plusieurs CdP écrivent les mêmes vivants ([LISEZ_MOI.md](../LISEZ_MOI.md)
> §2 ter : inutile en A, facultatif en B, recommandé en C). Le coordinateur le copie en `Methode/ARBITRE.md` du dépôt des
> vivants, remplit les `<…>` et adapte les `⟨…⟩` (la table du §2), puis fait l'installation du §4. À la copie, les liens vers le package se mettent en texte simple. Supprimer cet encadré.

---

## §0 · L'arbitre en neuf questions

*Pour le lecteur humain ; n'ajoute aucune règle au §1.*

1. **Qu'est-ce que c'est ?** Un script, lancé chaque jour par une action planifiée. À plusieurs CdP, chacun ne lit que
   son domaine et **personne ne voit l'ensemble** des vivants partagés (registre, `chantiers.yaml`, tableau, journal du
   plan, un checkpoint par domaine) : il est le regard qui manque. Sans mémoire d'un passage à l'autre, sans jeton de
   modèle, sans secret.
2. **Pourquoi ?** Les mêmes accidents reviennent, invisibles depuis un seul domaine : deux sessions prennent le même
   numéro de décision (contrôle 1) ; un chantier reste en vol sans CdP, ou deux lots visent le même livrable (5 et 8) ;
   le tableau publié ne suit plus le yaml (6) ; une session oubliée garde son témoin ; le fichier des chantiers enfle
   (archivage) ; une file de checkpoint annonce comme à faire un chantier fini (9) ; un checkpoint passe son plafond (10) ; un
   `.yaml` n'est plus du YAML valide (11). Un script n'a aucun enjeu dans un domaine, passe quand personne n'écrit, et
   laisse une trace datée même quand tout va bien.
3. **Quand en ai-je besoin ?** Mode A : jamais. Mode B : dès le premier écart ou quand les vivants grossissent. Mode C :
   dès que plusieurs CdP écrivent les mêmes vivants le même jour. Le signe : le premier numéro de décision en double, ou
   la première session oubliée qui garde un témoin.
4. **Que fait-il ?** Il normalise, contrôle, dépose un chantier par écart nouveau, juge les témoins, archive, régénère
   le tableau, écrit une ligne au journal, résume (§1).
5. **Que ne fait-il jamais ?** Corriger, décider, écrire ailleurs que dans ses chantiers, son journal et l'archivage (§3).
6. **Comment l'installe-t-on ?** Copier le script et son workflow, écrire la table des domaines, amorcer le journal, lancer
   un premier passage (§4).
7. **Ce que ça coûte** : une minute de machine par jour, un commit par jour au plus ; rien au porteur que l'e-mail
   d'un échec ; aux CdP, lire après chaque `pull` les chantiers `pour:` qui les visent.
8. **Comment lire ce qu'il produit ?** Le journal, une ligne par passage, même sans écart — **c'est la preuve qu'il a
   tourné** : date et heure · écarts · constats nouveaux · témoins · archivage · checkpoints · socle (méthode, fiche et
   checkpoints, en Ko ; il doit baisser ou se stabiliser). Un constat est un chantier `a-cadrer`, `pour:` le propriétaire,
   à l'id `arbitre-c<n>-<clé>`.
9. **Comment juger s'il faut le garder ?** Après une semaine : le journal a-t-il une ligne par jour, les constats
   étaient-ils vrais, les CdP en ont-ils fait quelque chose, l'archivage n'a-t-il rien perdu ? **Un faux positif se
   corrige dans le script, pas au cas par cas.**

---

## §1 · Ce que le script fait, dans l'ordre

1. **Normaliser** : `archiver_chantiers.py normaliser` met entre guillemets les seules valeurs qu'un lecteur YAML lirait
   mal (format strict, contrôle 11) ; il ne change aucune valeur lue.
2. **Contrôler** : `verifier_vivants.py` avec `--archives` et `--domaines` (douze contrôles ; le 9 recoupe la file de chaque
   checkpoint avec `chantiers.yaml`, le 10 mesure leur taille contre le plafond de la méthode §6, le 11 le format, le 12 la
   taille des entrées de chantier et du registre contre leurs plafonds, `--registre-depuis` si le registre se mesure). Un fichier qui manque :
   code 2, rien n'est écrit, le journal dit « contrôle impossible : <fichier> ».
3. **Déposer un chantier par écart nouveau**, en fin de `chantiers.yaml`, au format strict : id `arbitre-c<n>-<clé>`
   (`<n>` le contrôle, `<clé>` le chantier en cause, `R<n>`, `tableau`, `journal`). **Jamais en double** : un chantier
   vivant de même id suffit ; un id archivé ne se réutilise pas (on ajoute `-<AAAAMMJJ>`). **Le contrôle 9, le
   contrôle 10 et le contrôle 12, un chantier par domaine** (`arbitre-c9-checkpoint-<domaine>-<date>`,
   `arbitre-c10-checkpoint-court-<domaine>-<date>`, `arbitre-c12-entrees-courtes-<domaine>-<date>`), sans nouveau dépôt
   tant qu'un chantier du même nom, ouvert, attend son CdP ; **un défaut de la table elle-même** : un seul chantier `arbitre-c9-table-<date>`, pour le coordinateur.
4. **Les témoins** : la ligne « Session en activité » de chaque checkpoint. **Un témoin ne se juge pas à son âge, mais à son
   silence** : aucun commit portant son identifiant depuis plus de 24 heures. ⟨Le témoin est les huit derniers
   caractères de l'identifiant de session des lignes d'attribution des commits ; sans cette ligne, convenir d'une marque
   que chaque CdP met dans ses messages.⟩ C'est **une information** (journal, résumé), jamais un chantier. **La
   coordination est exclue** : session longue de consultation, muette des jours sans être oubliée.
5. **Le checkpoint en retard** : un chantier du domaine passé en recette après le dernier commit de son checkpoint rejoint le
   chantier du contrôle 9 de ce domaine.
6. **Archiver** : `archiver_chantiers.py archiver` date `recette-le:` et sort vers `<Dossier>/Archives/CHANTIERS_<AAAA-MM>.yaml` les
   chantiers en recette depuis le délai de la méthode §6 (le défaut du script : ne pas passer `--delai`) ; il vérifie qu'il ne perd aucune ligne.
   Une date illisible : un chantier `archivage-<id>`. Code 2 : rien n'est écrit.
7. **Régénérer** le tableau si `chantiers.yaml` a changé, puis contrôler de nouveau.
8. **Le journal**, en fin de `Methode/ARBITRE_JOURNAL.md`, jamais une ligne réécrite :
   ```
   - <AAAA-MM-JJ HH:MM> · <n> écart(s) · <n> constat(s) nouveau(x) · <premier témoin silencieux, ou « témoins frais »> · archivage : <n> daté(s), <m> archivé(s) · checkpoints : <domaines signalés, ou « à jour »> · socle : <n> Ko
   ```
9. **Le résumé et le code de retour** : le résumé (date, écarts, constats nouveaux avec le CdP visé, ceux déjà signalés, le
   commit) va à la page du passage ; la dernière ligne, `Commit : <message>`, est le message du commit unique que le
   workflow pousse (`git pull --rebase`, un seul nouvel essai, jamais de force). **Code 0** : rien de nouveau ; **1** : au
   moins un chantier déposé ; **2** : un fichier manque ou un script échoue. Le workflow échoue sur 1 et 2.

## §2 · À qui adresser un constat

| ce qui est en cause | `pour:` |
|---|---|
| un chantier d'un domaine (son `module:`) | le CdP de ce domaine (table de la méthode §1 bis) ⟨une ligne par domaine, au besoin⟩ |
| un chantier en vol | le `cdp:` qu'il porte |
| deux lots en vol sur un livrable ou une ressource | les CdP des lots en cause, un chantier chacun |
| le retard (contrôle 9) ou la taille (contrôle 10) d'un checkpoint | le `cdp` du domaine dans `Methode/domaines.yaml` |
| la taille des entrées (contrôle 12) | le `cdp` du domaine ; le coordinateur pour le registre et les entrées hors domaine |
| tout le reste : registre, tableau, journaux, table des domaines, `methode` | le coordinateur (l'entrée de la table dont le `cdp` contient « Coordination ») |

## §3 · Ce que l'arbitre ne fait jamais

- Corriger une entrée, un numéro, un checkpoint, un témoin ou la table : il signale, le propriétaire corrige. Seule
  écriture mécanique : l'archivage et la normalisation (`archiver_chantiers.py`), jamais à la main.
- Écrire ailleurs qu'en fin de `chantiers.yaml`, dans le tableau régénéré, en fin de journal et dans `<Dossier>/Archives/`.
- Juger un document (contradiction, doublon, historique, style) : c'est le contrôleur.
- Réserver un numéro de décision, prendre un livrable, lancer un dev, ouvrir une session, envoyer un message.
- Pousser plus d'un commit par passage, ou forcer un push.

## §4 · L'installation, pas à pas

*Pour le coordinateur et le porteur.*

1. **Copier** dans `<Dossier>/` (le dossier des vivants, celui de `chantiers.yaml`) `arbitre.py`, `verifier_vivants.py`,
   `archiver_chantiers.py` et `generer_tableau.py` (modèles du package : l'arbitre trouve les trois autres à côté de
   lui) ; créer `<Dossier>/Archives/` (un `.gitkeep`).
2. **Écrire la table des domaines** `Methode/domaines.yaml` (modèle `modeles/domaines.yaml`) : une entrée par CdP,
   la coordination comprise ; **chaque checkpoint** a sa section `## §<n> · La file` (modèle [`modeles/CHECKPOINT.md`](CHECKPOINT.md)), que
   `file:` nomme. Le coordinateur la tient : à chaque domaine ouvert, fermé, ou section renommée.
3. **Amorcer** `Methode/ARBITRE_JOURNAL.md` (un titre et une ligne d'explication), copier ce fichier en `Methode/ARBITRE.md`.
4. **Copier le workflow** `modeles/depot-vivants/arbitre.yml` en `.github/workflows/arbitre.yml` du dépôt des vivants et
   n'y adapter que le bloc `env:` (les chemins). Il tourne chaque jour à 5 h 42 UTC, ou à la main (« Run workflow »),
   avec le seul droit d'écrire dans le dépôt (`contents: write`). **Sur un compte gratuit** (règles de branche :
   `3_GITHUB.md` §5), l'action pousse sur la branche par défaut, sans règle à contourner.
5. **Prévenir les CdP** qu'ils recevront des chantiers `pour:` de l'arbitre. **Le premier passage est bavard** sur un
   projet avancé : tous les chantiers ouverts que les checkpoints ne citent pas encore tombent d'un coup (un chantier par
   domaine) ; ensuite, seul le nouveau.
6. **Lancer le premier passage à la main** (onglet Actions) ; vérifier la ligne du journal et le commit « Arbitre <date> : … ».
7. **Les e-mails de GitHub** : le porteur laisse actives les notifications d'un workflow en échec. **L'échec est le signal** ;
   le journal fait foi, pas l'e-mail. Un passage manqué (pas de ligne) ne se rattrape pas : le suivant contrôle tout.

| geste | qui | quand |
|---|---|---|
| copier les scripts, `<Dossier>/Archives/`, le workflow ; écrire la table des domaines | coordinateur | avant |
| donner à chaque checkpoint sa section de file, chaque sujet cité par son id | chaque CdP | avant le premier passage, puis à chaque reprise |
| lancer le premier passage ; lire le journal et le commit | coordinateur | jour 1 |
| lire les chantiers `pour:` après chaque `pull` ; corriger | chaque CdP | en continu |
| tenir la table des domaines | coordinateur | à chaque changement |

## §5 · L'essai et le jugement

Une semaine, puis le coordinateur juge avec le porteur : **garder, régler ou arrêter**. On regarde le journal (une ligne
par jour), la vérité des constats, ce que les CdP en ont fait, l'archivage (rien ne manque : `archiver_chantiers.py
chercher`), le contrôle 9 qui tombe à « à jour » une fois les files remises au pas. La décision s'écrit au registre.
