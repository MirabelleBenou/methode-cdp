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
| `<Dossier>/attendus/<version>/` | les attendus de réception, calculés au cadrage — jamais lus par le dev |
| `<Dossier>/outils_cdp/` | les scripts jetables du CdP (sondes, mesures) |
| `<Dossier>/Archives/` | les archives figées des vivants devenus longs |

**Règles** : noms stables (la version est dans l'en-tête, l'historique dans git) ; `git pull` avant d'écrire ; un commit
« Lot v<X.Y> clos » à chaque clôture ; le projet claude.ai en porte un miroir, recopié par le CdP depuis son clone.

**Jamais ici** : secrets, données de production, images.

**Reprendre un domaine** : ⟨la table des CdP, de leur checkpoint et de leur ligne fixe de reprise (méthode §1 bis)⟩.
