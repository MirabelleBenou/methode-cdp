# LES FICHIERS D'UN LOT — addendum, arrêt, rapport du dev

*Trois modèles courts. Tous vivent dans `lots/v<X.Y>/` du dépôt de code, sur la branche du lot, hors de l'archive de
déploiement.*

---

## A · `ADDENDUM_<n>.md` — écrit par le CdP

```markdown
# ADDENDUM <n> — <titre du lot> · `v<X.Y>`
### <date> · <session de CdP> · répond à `ARRET_<n>.md` | aux retours d'essai du porteur du <date>

**Dev : Sonnet · Medium · même session si elle est ouverte, sinon neuve (qui lit aussi les rapports précédents)**

## Ce que l'addendum remplace
- Le §<x> du cadrage, règle <y> : **remplacé par** … (texte complet, pas un diff).
- Le critère C<z> : **remplacé par** …

## Ce qu'il ajoute
- Règle / critère / fichier autorisé : …

## Où reprendre
À l'étape <k> du déroulé. Le travail déjà commité reste (ou : se reprend depuis le commit `<sha>`).

## Ce qui ne change pas
Tout le reste du cadrage.
```

*Un addendum de retours d'essai porte, mot pour mot, les demandes du porteur, puis les règles qui en découlent.*

---

## B · `ARRET_<n>.md` — écrit par le dev

```markdown
# ARRÊT <n> — <titre du lot> · `v<X.Y>`
### <date heure> · dernier commit poussé `<sha>`

## Ce qui m'arrête
<La règle, le critère ou la porte, cités par leur numéro ; ce qu'ils disent ; ce que j'ai constaté — mesure à l'appui.>

## Pourquoi je ne tranche pas
<Ce que chacune des lectures possibles changerait.>

## Ce que je propose (sans l'avoir fait)
1. <option> — <conséquence>
2. <option> — <conséquence>

## Où j'en suis
<Étapes faites, ce qui est commité, ce qui ne l'est pas.>
```

---

## C · `RAPPORT_DEV.md` — écrit par le dev

```markdown
# RAPPORT DU DEV — <titre du lot> · `v<X.Y>`
### <date> · <modèle, effort> · commit de livraison `<sha complet>`

## 1 · Ce dont je ne suis pas sûr
<Toujours en tête. « Rien » s'il n'y a rien. Tout code existant qui semble faire ce que le cadrage demande de créer.>

## 2 · Les portes (mesurées sur l'archive du commit de livraison)
| porte | attendu | mesuré | |
|---|---|---|---|
| P0 | … | … | OK / ÉCART |

**Mes comptes** : tests ajoutés <n>, clés ajoutées <n>, règles CSS ajoutées <n>, …

## 3 · Les critères du cadrage
- **C1** — tenu / non tenu — <mesure>.

## 4 · La maquette (s'il y en a une)
Images montrées ; mots de validation du porteur ; chaque demande mot pour mot et ce que j'en ai fait ; tours ; empreinte
notée à la validation.

## 5 · Les sorties brutes
<rituel, tests, lint, syntaxe, migration, empreinte — tels quels>

## 6 · Les écarts au cadrage
<Même minimes, avec leur raison.>

## 7 · La méthode
Début <heure>, fin <heure> ; interventions <n> ; ce qui m'a ralenti.
```
