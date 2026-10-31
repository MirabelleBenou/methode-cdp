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
| `<Dossier>/chantiers.html` | la page lisible, régénérée par `generer_tableau.py` à chaque écriture du yaml |
| `<Dossier>/archiver_chantiers.py` | date les chantiers en recette et sort vers `Archives/` ceux qui y sont depuis sept jours ; `chercher` retrouve un chantier, vivant ou archivé |
| `<Dossier>/verifier_vivants.py` | ⟨plusieurs CdP⟩ le contrôle en lecture seule des vivants partagés ; avec `--domaines`, le contrôle 9 recoupe la file de chaque checkpoint et `chantiers.yaml` |
| `Methode/domaines.yaml` | ⟨plusieurs CdP⟩ la table des domaines que lit le contrôle 9 : par domaine, son CdP, son checkpoint, le titre de la section de sa file, ses modules ; tenue par le coordinateur au pas de la table de la méthode §1 bis |
| `<Dossier>/attendus/<version>/` | les attendus de réception, calculés au cadrage — jamais lus par le dev |
| `<Dossier>/outils_cdp/` | les scripts jetables du CdP (sondes, mesures) |
| `<Dossier>/Archives/` | les archives figées des vivants devenus longs, dont `CHANTIERS_<AAAA-MM>.yaml` (écrit par l'archivage : on n'y fait qu'ajouter, figé à la fin du mois) |
| `Methode/ARBITRE.md`, `Methode/ARBITRE_JOURNAL.md` | ⟨facultatif, plusieurs CdP⟩ la procédure de l'arbitre des vivants (tâche planifiée quotidienne, lecture et signalement seuls : vivants partagés et checkpoints) et son journal, une ligne par passage |

**Règles** : noms stables (la version est dans l'en-tête, l'historique dans git) ; `git pull` avant d'écrire ; un commit
« Lot v<X.Y> clos » à chaque clôture ; le projet claude.ai en porte un miroir, recopié par le CdP depuis son clone.

**Contrôler, chercher** : le vérificateur se lance avec `--archives` et, quand plusieurs CdP tiennent chacun un
checkpoint, avec `--domaines` (le contrôle 9 ; `--racine <dossier>` si on le lance ailleurs qu'à la racine du dépôt) ;
un chantier qui n'est plus dans `chantiers.yaml` se cherche par `chercher` (`--partout` : dans toutes les valeurs) :
```
python3 -B <Dossier>/verifier_vivants.py --chantiers <Dossier>/chantiers.yaml \
  --registre <Dossier>/REGISTRE_ARBITRAGES_<P>.md --tableau <Dossier>/chantiers.html \
  --generateur <Dossier>/generer_tableau.py --journal <Dossier>/PLAN_<P>.md --archives <Dossier>/Archives \
  --domaines Methode/domaines.yaml
python3 -B <Dossier>/archiver_chantiers.py chercher <id ou mot> --chantiers <Dossier>/chantiers.yaml \
  --archives <Dossier>/Archives
```

**Jamais ici** : secrets, données de production, images.

**Reprendre un domaine** : le porteur colle, dans une conversation neuve du projet avec Opus, la ligne fixe du domaine —
rien à téléverser. **Elle nomme tous les dépôts du domaine** : le garde-fou d'une session refuse un rattachement que
Le porteur n'a pas demandé en toutes lettres ; la ligne collée vaut cette demande. Un dépôt de plus en route : la session
le demande au porteur en une ligne prête (« dis-moi « rattache X » »).

| CdP | checkpoint | ligne fixe |
|---|---|---|
| ⟨Opus-CdP-<Domaine>⟩ | `<Dossier>/CHECKPOINT_<DOMAINE>.md` | `Tu es Opus-CdP-<Domaine>. Reprends : rattache en accès push les dépôts <owner> <Projet>, <Projet>-App⟨, <Projet>-Lots…⟩ (un clone à la fois), fais git pull dans <Projet>, lis <Dossier>/CHECKPOINT_<DOMAINE>.md en entier (§0 d'abord) et suis-le.` |
| ⟨une ligne par CdP, et le coordinateur (méthode §1 bis)⟩ | | |
