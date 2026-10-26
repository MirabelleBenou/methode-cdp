# CADRAGE — <titre du lot> · `v<X.Y>`
### <date> · <session de CdP> · branche `lot/v<X.Y>` de `<owner>/<Projet>-App` · base `<sha court de main>`

> **Modèle pour le CdP — un cadrage ne le cite jamais.** Le cadrage est autoportant : avec le prompt du dev, il se
> suffit. Il porte des règles, des critères et les textes que l'utilisateur lira — **jamais le code tout écrit**.
> Supprimer cet encadré.

**Dev : Sonnet · Medium · session neuve** *(Opus pour ⟨…⟩ ; High pour une migration, plusieurs écrans, un moteur, des
étapes en cascade)*

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

⟨**La prédiction** : rejeu, empreinte, sortie attendue et son sha256, conditions (locale, largeur, thème).⟩

## §6 · Le `CHANGELOG`

Texte de l'entrée, mot pour mot :

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
- [ ] La prédiction calculée sous les règles du cadrage ; les attendus écrits au dépôt des vivants, pas ici.
- [ ] Les API, fichiers et fonctions que la règle impose, tous nommés.
- [ ] Une règle de couleur mesurée sur tous les thèmes ; un libellé à la largeur la plus étroite.
- [ ] Aucun code tout écrit.
- [ ] Modèle, effort, session en tête.
