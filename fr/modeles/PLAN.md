# PLAN DE MISE EN ŒUVRE — <Projet> · v1
### <date> · <session de CdP>

> *La feuille de route par phases, et le journal des versions. Le détail des chantiers vit dans `chantiers.yaml`, les
> décisions au registre : le plan ne les recopie pas, il les cite.*

---

## §1 · Le produit

<Ce que c'est, pour qui, en quelques lignes. Ses modules ou sous-projets. Où il se déploie.>

## §2 · L'architecture

<La stack, les grandes pièces, les flux de données. Ce qui est un invariant (ne bouge que sur autorisation).>

## §3 · Les écrans / les modules

| lettre | écran ou module | état | refs |
|---|---|---|---|
| A | <…> | à venir / livré `v<X.Y>` | R<n> |

## §4 · La direction visuelle

<Les principes tranchés (R<n>), le guide de style s'il existe (référence écrite une fois au projet).>

## §5 · Les phases

| phase | contenu | état |
|---|---|---|
| 0 | le banc (lot d'outillage) | à venir |
| 1 | <…> | |

## §6 · Ce qui est hors périmètre

<Ce qu'on a décidé de ne pas faire, avec la référence R.>

---

## §11 · Le journal des versions

*On ne fait qu'ajouter. Une ligne par lot clos, à sa clôture. **C'est la seule source du fait d'un lot** : le registre,
`chantiers.yaml` et le checkpoint le citent (la version ou le nom du lot), ils ne le redisent pas (méthode §6). Ce journal
ne dit pas qu'une version a été remise puis refusée — la règle du numéro lit les branches de lot et `chantiers.yaml`
(la méthode, §2, étape 6 ; ouvertes et archivées).*

*La forme d'une ligne : la version (un livrable déployé à chaque lot) ou le nom du lot (publié par release, sans version) ;
la date ; le titre ; le dev (modèle, effort) ; la durée ; les arrêts (leur nombre, « aucun ») ; la réception (conforme,
addendum) ; l'empreinte du code livré ; la validation (en production, par le porteur, la date — ou « fusion après
réception » pour un livrable publié par release) ; les R.*

| version ou lot | date | lot | dev | durée | arrêts | réception | empreinte | validation | refs |
|---|---|---|---|---|---|---|---|---|---|
| `v<X.Y>` | <date> | <titre> | <modèle, effort> | <durée> | <n, ou aucun> | <conforme / addendum <n>> | `<empreinte>` | <en production, <date>> | R<n> |
