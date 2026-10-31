# CHANGELOG — <Projet>

*Une entrée par version, la plus récente en tête. Le texte de chaque entrée vient du cadrage, mot pour mot ; le dev y
ajoute ses lignes de fichiers en sous-puces à deux espaces de retrait.*

*Deux régimes (méthode §1 bis, « Le livrable et sa version »). **Déployé à chaque lot** : chaque lot ouvre son entrée
`v<X.Y>`, la version qu'il a calculée en prenant le livrable ; garde alors la section « Unreleased » vide, ou supprime-la.
**Publié par release** : un lot ne porte pas de version, il complète la section « Unreleased », en tête ; à la release,
que le porteur demande, le CdP fixe le numéro par la règle ci-dessous, renomme « Unreleased » en `v<X.Y.Z> — <date>` et
ouvre en tête une nouvelle section « Unreleased », vide.*

**Règle de numérotation** (livrable publié par release) : ⟨par exemple : majeur si un fichier produit change de forme,
mineur pour une fonction nouvelle, correctif sinon⟩.

## Unreleased

- <texte du cadrage, mot pour mot>
  - `<fichier>` — ce qui y a changé (fonctions, règles).

## v<X.Y> — <date>

- <texte du cadrage, mot pour mot>
  - `<fichier>` — ce qui y a changé (fonctions, règles).
