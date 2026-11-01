# <Projet> — les documents vivants

Dépôt privé. **Seules les sessions de chef de projet (CdP) y écrivent.** Le dev n'y a pas accès : il lit le dépôt de
code, `<owner>/<Projet>-App`.

| chemin | porte |
|---|---|
| `Methode/METHODE_<P>.md` | la méthode du projet (prime sur la skill `methode-cdp`) |
| `<Dossier>/CHECKPOINT_<P>.md` | l'état courant, point d'entrée de chaque session de CdP |
| `<Dossier>/REGISTRE_ARBITRAGES_<P>.md` | les décisions, numérotées R1, R2… |
| `<Dossier>/PLAN_<P>.md` | la feuille de route et le journal des versions |
| `<Dossier>/chantiers.yaml` | la source unique des chantiers |
| `<Dossier>/chantiers.html` | ⟨extension : tableau publié⟩ la page lisible, **fixe** (environ 11 Ko, aucune donnée de chantier), régénérée par `generer_tableau.py` à chaque écriture du yaml |
| `<Dossier>/chantiers.json` | ⟨extension : tableau publié⟩ **le fichier de données** de la page, écrit par le même script à côté d'elle (même nom) : les seuls chantiers ouverts, en champs courts, **un fichier de données assez petit pour être lu en entier** (méthode §6) |
| `<Dossier>/archiver_chantiers.py` | date les chantiers en recette et sort vers `<Dossier>/Archives/` ceux qui y sont depuis le délai de la méthode §6 ; `chercher` retrouve un chantier, vivant ou archivé ; `normaliser` met les `.yaml` au format YAML strict |
| `<Dossier>/verifier_vivants.py` | ⟨plusieurs CdP⟩ le contrôle en lecture seule des vivants partagés (douze contrôles, dont le 11 : les `.yaml` sont du YAML valide) ; avec `--domaines`, le contrôle 9 recoupe la file de chaque checkpoint et `chantiers.yaml` |
| `Methode/domaines.yaml` | ⟨plusieurs CdP⟩ la table des domaines que lit le contrôle 9 : par domaine, son CdP, son checkpoint, le titre de la section de sa file, ses modules ; tenue par le coordinateur au pas de la table de la méthode §1 bis |
| `<Dossier>/attendus/<version>/` | les attendus de réception, calculés au cadrage — jamais lus par le dev |
| `<Dossier>/outils_cdp/` | les scripts jetables du CdP (sondes, mesures) et `contexte.py`, la mesure du contexte (seuils : méthode §6) |
| `<Dossier>/Archives/` | les archives figées des vivants devenus longs, dont `CHANTIERS_<AAAA-MM>.yaml` (écrit par l'archivage : on n'y fait qu'ajouter, figé à la fin du mois) |
| `<Dossier>/arbitre.py`, `.github/workflows/arbitre.yml`, `Methode/ARBITRE.md`, `Methode/ARBITRE_JOURNAL.md` | ⟨facultatif, plusieurs CdP⟩ l'arbitre des vivants : une **action GitHub** quotidienne, sans session (le script, son workflow, ce qu'il fait et ne fait pas, son journal d'une ligne par passage) ; elle échoue quand elle a déposé un chantier, et l'e-mail de GitHub prévient |
| `Methode/CONTROLEUR.md`, `Methode/CONTROLEUR_JOURNAL.md` | ⟨facultatif, plusieurs CdP⟩ le contrôleur : une session Opus hebdomadaire, par tâche planifiée, qui juge la forme des documents (contradiction, oubli, doublon, historique inutile) et rend au plus cinq constats en chantiers ; son journal, une ligne par lundi |

**Règles** : noms stables (la version est dans l'en-tête, l'historique dans git) ; `git pull` avant d'écrire ; un commit
« Lot v<X.Y> clos » à chaque clôture, avec la ligne `Contexte : <N> jetons, dont <F> de charge fixe` (méthode §6) ⟨; avec l'extension du miroir,
le projet claude.ai en porte un miroir, recopié par le CdP depuis son clone⟩.

⟨extension : tableau publié — **Le tableau des chantiers a un seul lien** : ⟨le lien de l'artefact⟩. Toute autre page de
chantiers est obsolète ; une page d'essai se supprime, avec l'accord du porteur.⟩

**Contrôler, chercher** : le vérificateur se lance avec `--archives` et, quand plusieurs CdP tiennent chacun un
checkpoint, avec `--domaines` (le contrôle 9 ; `--racine <dossier>` si on le lance ailleurs qu'à la racine du dépôt) ;
un chantier qui n'est plus dans `chantiers.yaml` se cherche par `chercher` (`--partout` : dans toutes les valeurs) ;
la variable `REGISTRE_DEPUIS` du workflow de l'arbitre est le numéro de la première entrée du registre écrite après
l'installation (le contrôle 12 ne mesure que celles-là ; vide, le registre n'est pas mesuré) :
```
python3 -B <Dossier>/verifier_vivants.py --chantiers <Dossier>/chantiers.yaml \
  --registre <Dossier>/REGISTRE_ARBITRAGES_<P>.md ⟨--tableau <Dossier>/chantiers.html \
  --generateur <Dossier>/generer_tableau.py⟩ --journal <Dossier>/PLAN_<P>.md --archives <Dossier>/Archives \
  --domaines Methode/domaines.yaml
python3 -B <Dossier>/archiver_chantiers.py chercher <id ou mot> --chantiers <Dossier>/chantiers.yaml \
  --archives <Dossier>/Archives
```

⟨extension : tableau publié — **Republier le tableau** — **à la clôture seulement**, pas à chaque écriture du yaml (la page fixe et son fichier de
données, au même lien) :
1. **régénérer après le dernier `git pull` / rebase, jamais avant** (cas vécu : un fichier de données tiré avant la base a
   manqué trois chantiers d'une autre session ; le contrôle 6 l'a vu) ; le vérificateur passe, **contrôle 6 OK** — c'est
   lui qui garantit les données, pas une lecture ;
2. **le CdP lit lui-même, en entier, la page et le fichier de données** — l'outil d'artefact l'exige pour tout fichier que
   la session n'a pas écrit, **y compris le fichier de données déjà publié qu'on remplace** ; une lecture « par fichier »
   ne compte pas ;
3. **il relit le diff de ses propres écritures** dans `chantiers.yaml` depuis sa dernière publication ;
4. **il republie la page et le fichier de données ensemble**, au même lien, même si seule la donnée a changé.
Une page ouverte depuis le disque ne charge pas ses données : on la sert (`python3 -m http.server` dans le dossier) ou on
la publie.⟩

**Jamais ici** : secrets, données de production, images.

**Reprendre un domaine** : le porteur colle, dans une conversation neuve du projet avec Opus, la ligne fixe du domaine —
rien à téléverser. **Elle nomme tous les dépôts du domaine** : le garde-fou d'une session refuse un rattachement que
Le porteur n'a pas demandé en toutes lettres ; la ligne collée vaut cette demande. Un dépôt de plus en route : la session
le demande au porteur en une ligne prête (« dis-moi « rattache X » »).

| CdP | checkpoint | ligne fixe |
|---|---|---|
| ⟨Opus-CdP-<Domaine>⟩ | `<Dossier>/CHECKPOINT_<DOMAINE>.md` | `Tu es Opus-CdP-<Domaine>. Reprends : rattache en accès push les dépôts <owner> <Projet>, <Projet>-App⟨, <Projet>-Lots…⟩ (un clone à la fois), fais git pull dans <Projet>, lis <Dossier>/CHECKPOINT_<DOMAINE>.md en entier (§0 d'abord) et suis-le.` |
| ⟨une ligne par CdP, et le coordinateur (méthode §1 bis)⟩ | | |
