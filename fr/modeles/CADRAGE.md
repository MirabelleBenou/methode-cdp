# CADRAGE — <titre du lot> · `v<X.Y>`
### <date> · <session de CdP> · branche `lot/v<X.Y>` de `<owner>/<Projet>-App` · base `<sha court de main>`

> **Modèle pour le CdP — un cadrage ne le cite jamais.** Le cadrage est autoportant : avec le prompt du dev, il se
> suffit. Il porte des règles, des critères et les textes que l'utilisateur lira — **jamais le code tout écrit**.
> **La version** : `v<X.Y>` n'existe que pour un livrable **déployé à chaque lot** (elle se calcule quand le lot prend le
> livrable, par la règle de la méthode §1 bis, jamais `main` plus un ; le cadrage l'annonce). Pour un livrable
> **publié par release**, le lot ne porte pas de version : retirer `v<X.Y>` du titre, nommer la branche et le dossier
> d'après le lot (`lot/<nom du lot>`, `lots/<nom du lot>/`), et le §6 complète la section « Unreleased » du `CHANGELOG`
> — c'est elle que vérifie la porte P8 du prompt du dev — avec, si le lot produit une donnée dérivée, « À déposer après
> la release : … » (méthode §1 bis, « Le livrable et sa version »).
> Supprimer cet encadré.

**Dev : ⟨modèle⟩ · ⟨effort⟩ · session neuve** *(par défaut, ceux de la table de la méthode §6 ; Opus pour ⟨…⟩ ; High
pour une migration, plusieurs écrans, un moteur, des étapes en cascade ; un lot de complexité faible : la forme courte,
en fin de ce modèle)*

---

## §0 · Les pièces

- **La base** : `main` au `<sha complet>`. Si la tête de `main` n'est pas ce commit : arrêt.
- **Sur cette branche** : ce cadrage ; ⟨`maquette/…` ; fixtures ; images à ouvrir, par leur nom — les seules⟩.
- **À lire avant de construire** : ⟨les fonctions, par leur nom, dans les gros fichiers⟩.

## §1 · Ce que fait le lot, et pourquoi

*Deux à cinq phrases : la demande du porteur (avec ses mots quand ils décident), ce que la mesure a montré, ce que voit
l'utilisateur à la fin.*

## §2 · Les décisions et les règles

*Numérotées, testables. Ce que le porteur a tranché (avec la référence R du registre), puis ce que le CdP a tranché.*

1. **⟨Règle⟩** — ⟨précision, cas limites, ce qui se passe quand la donnée manque⟩.
2. …

**Les textes affichés, au caractère près** (FR / EN) :

| clé | FR | EN |
|---|---|---|
| ⟨…⟩ | ⟨…⟩ | ⟨…⟩ |

## §3 · Ce qui ne bouge pas

- ⟨Les modules, routes, contrats, écrans, empreintes qui doivent rester identiques — et comment on le prouve.⟩
- ⟨L'invariant du projet : inchangé.⟩

## §4 · Les fichiers

**La liste exacte** de ce que le lot modifie, ajoute ou retire — rien d'autre (porte P9) :

| fichier | change | ce qui y change |
|---|---|---|
| ⟨…⟩ | modifié / ajouté / retiré | ⟨fonctions, zones⟩ |
| ⟨le fichier de verrouillage d'une dépendance nouvelle, s'il y en a une⟩ | ajouté / modifié | ⟨la dépendance, sa version⟩ |

## §5 · Les critères et la prédiction

**Le bloc « base »** (sortie du rituel sur la base, ligne pour ligne) :

```
⟨…⟩
```

**Les portes, en deltas contre la base** :

| porte | base | attendu | delta |
|---|---|---|---|
| ⟨tests⟩ | ⟨n⟩ | ⟨n + k⟩ | +k |
| ⟨…⟩ | | | |

**Les critères du lot** (chacun passé d'abord sur l'existant, chacun mesurable sur l'archive) :

- **C1** — ⟨ce qui se mesure, comment, valeur attendue⟩.
- **C2** — …
- ⟨**Relecture indépendante** — pour un lot de complexité moyenne ou forte, ou qui ajoute une dépendance : un sous-agent
  neuf, d'un autre modèle que le dev, lit le diff (sécurité, dépendances, lisibilité, tests manquants) ; le CdP tranche
  ses constats à la réception (méthode §4, point 4). Une dépendance nouvelle est inscrite au registre.⟩

⟨**La prédiction** : rejeu, empreinte, sortie attendue et son sha256, conditions (locale, largeur, thème).⟩

## §6 · Le `CHANGELOG`

Texte de l'entrée, mot pour mot — *une entrée `v<X.Y>` pour un livrable déployé à chaque lot ; pour un livrable publié
par release, il complète la section « Unreleased », sans version, et y inscrit « À déposer après la release : <quoi,
d'où, vers où> » pour toute donnée dérivée* :

```
⟨…⟩
```

## §7 · Les arrêts propres au lot

En plus de ceux du prompt du dev :
- ⟨…⟩

## §8 · Les preuves

- ⟨Tests ajoutés (leur nombre et ce qu'ils couvrent) ; contrôle d'écran par le DOM ; bout en bout ; maquette ou non.⟩
- ⟨Images : aucune / les trois à six à montrer, par leur nom, en découpes à l'échelle 1 pour une pièce posée.⟩

## §9 · La livraison

- Le commit de livraison, puis `lots/v<X.Y>/RAPPORT_DEV.md` dans un commit à part, poussés sur `lot/v<X.Y>`.
- Le livrable : ⟨`git archive` du commit de livraison / le fichier `<nom>` hors zip⟩.

---

### Liste de contrôle du CdP avant de pousser (à retirer du cadrage)

- [ ] La base mesurée à froid aujourd'hui, pas supposée.
- [ ] Les tests et le banc cherchés pour **les valeurs** que le lot change, pas seulement les symboles.
- [ ] Rien de ce que le lot crée ne double un existant.
- [ ] Les dettes à déclencheur passées contre la liste du §4.
- [ ] Chaque critère essayé sur l'existant ; chaque critère textuel dit s'il compte les commentaires.
- [ ] La prédiction calculée sous les règles du cadrage ; les attendus — seulement si le lot produit des valeurs à
  comparer (méthode §2) — écrits au dépôt des vivants, pas ici.
- [ ] Les API, fichiers et fonctions que la règle impose, tous nommés.
- [ ] Une règle de couleur mesurée sur tous les thèmes ; un libellé à la largeur la plus étroite.
- [ ] Aucun code tout écrit.
- [ ] La version calculée quand le lot prend le livrable (la règle de la méthode §1 bis, pas `main` plus un) — ou
  aucune version, pour un livrable publié par release.
- [ ] Lot de complexité moyenne ou forte, ou dépendance nouvelle : la relecture indépendante prévue, le fichier de
  verrouillage dans la liste du §4.
- [ ] Modèle, effort, session en tête.

---

## La forme courte — un lot de complexité faible

*Un correctif d'une ligne, un libellé, une valeur (méthode §3) : ce cadrage-ci, d'une page au plus, remplace le modèle
ci-dessus. Il garde ce qui ne se négocie pas — la base, la liste des fichiers, des critères en deltas, les arrêts — et
n'appelle que les portes d'un lot de complexité faible (prompt du dev §4). « Faible » est la complexité du lot, jamais
un effort : l'en-tête porte un vrai effort, celui de la table de la méthode §6, ou Low pour un correctif d'une ligne
(méthode §3). Pas d'attendus (méthode §2), pas de bloc « base » complet :
la ligne de la porte P0 suffit.*

```markdown
# CADRAGE — <titre du lot> · `v<X.Y>` · forme courte
### <date> · <session de CdP> · branche `lot/v<X.Y>` de `<owner>/<Projet>-App` · base `<sha court de main>`

**Dev : ⟨modèle⟩ · ⟨effort⟩ · session neuve** — complexité faible ; portes : P0, P1, P5, P7, P8, P9, P11 ⟨+ celles que
ce lot nomme⟩.

- **La base** : `main` au `<sha complet>` ; ⟨la ligne du rituel qui fait P0⟩. Si la tête n'est pas ce commit : arrêt.
- **Ce que fait le lot** : ⟨une ou deux phrases ; la demande du porteur avec ses mots⟩.
- **Les fichiers permis** : ⟨la liste exacte⟩ — rien d'autre (P9).
- **Les critères**, en deltas : C1 ⟨…⟩ ; C2 ⟨…⟩ ⟨; C3⟩.
- **Les arrêts** : ceux du prompt du dev ⟨, et …⟩.
- **Le `CHANGELOG`**, mot pour mot : ⟨…⟩.
```
