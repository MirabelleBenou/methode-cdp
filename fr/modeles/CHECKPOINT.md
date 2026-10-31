# CHECKPOINT — <Projet> · <domaine> · `v<X.Y>`

**Session en activité : aucune — libre depuis <date, heure>.** *(ou : `<identifiant court>`, depuis <heure> — les huit
derniers caractères de l'identifiant de la session, celui de la ligne d'attribution de session de ses commits)*

> **Reprise** — le porteur colle dans une conversation neuve du projet, avec Opus : « Tu es Opus-CdP-<Domaine>.
> Reprends : rattache en accès push les dépôts <owner> <Projet>, <Projet>-App⟨, <Projet>-Lots, les autres dépôts du
> domaine⟩ (un clone à la fois), fais git pull dans <Projet>, lis `<Dossier>/CHECKPOINT_<DOMAINE>.md` en entier
> (§0 d'abord) et suis-le. » Premier geste : poser le témoin ci-dessus par un push.
> *La ligne nomme **tous les dépôts du domaine** : le garde-fou d'une session refuse un rattachement que le porteur n'a pas
> demandé en toutes lettres, et la ligne collée vaut cette demande.*
### <date, heure> · <session de CdP> · point d'entrée de la session suivante · remplace le checkpoint du <date>

> *Source : dépôt privé `<owner>/<Projet>`, `<Dossier>/CHECKPOINT_<P>.md`. Le projet claude.ai en porte un miroir sous
> le même nom, recopié par le CdP.*
>
> *Le checkpoint dit l'état **réel**, mesuré — pas l'état espéré. Il se réécrit en entier à chaque passation. **Il tient
> en 10 Ko** (10 240 octets) : la ligne fixe, le témoin, l'état, la file, ce qu'il faut pour reprendre ; l'historique part
> à une archive du domaine (`<Dossier>/Archives/CHECKPOINT_<DOMAINE>_ARCHIVE_<date>.md`). Le contrôle 10 du vérificateur
> le signale.*

---

## §0 · Où on en est

- **<Projet> est au `v<X.Y>`.** Empreinte du code `<…>` ; rituel rejoué le <date> : conforme, `<n> passed`.
- **Le dépôt de code** : `main` au `<sha>` ; l'archive de déploiement est `git archive` de `main`.
- **Depuis le checkpoint précédent** : <les lots livrés, en une ligne chacun, avec leur version et leur R>.
- **La méthode** est en v<n> (<ce qui a changé>).
- **Le registre** : les numéros se réservent par un push au moment d'écrire (méthode §1 bis) — jamais d'après ce fichier.
- **Dettes ouvertes** : `<id>` — une demi-ligne chacune (chaque dette a son chantier, cité par son id).
- **À faire par le porteur** :
  - <tag et release à poser, sur quel commit, avec quel texte> ;
  - <livrable à déposer, nom exact et sha256> ;
  - <branches fusionnées à supprimer sur GitHub : …>.
- **En vol** : `<id>` — <ce qui attend un essai ou une réponse extérieure>.

---

## §1 · Le premier geste — clone, rituel

**1. Les dépôts** (un `add_repo` chacun, propriétaire `<owner>`, accès `push`, un clone à la fois) :
- `<Projet>` → `git clone --depth 1 https://github.com/<owner>/<projet> /home/claude/<projet>` ;
- `<Projet>-App` → `git clone --depth 1 https://github.com/<owner>/<projet>-app /home/claude/<projet>-app`.

Lire ce checkpoint, puis `Methode/METHODE_<P>.md` (v<n>).

**2. Le rituel de la base** : <les commandes, une par ligne> — attendu, ligne pour ligne :

```
<sortie attendue du rituel sur la base>
```

Toute divergence s'arrête là et se dit au porteur.

---

## §2 · Le circuit d'un lot

<Le circuit tel qu'il se joue dans CE projet, en six étapes courtes — renvoyer à la méthode pour le détail. Ce qui a
changé depuis la dernière fois en gras.>

---

## §3 · La file — à arbitrer avec le porteur

*Cette section — `## §<n> · La file`, §3 ici — **porte la liste elle-même**, jamais un renvoi (« tout est au §0 »). La
file ne porte que des **chantiers inscrits** (méthode §6) : chaque sujet est cité par son id de `chantiers.yaml`, entre
accents graves. Un sujet qui n'a pas encore de chantier s'inscrit **d'abord** (à venir, à cadrer ou dette), puis se cite ;
un chantier clos (en recette ou archivé) sort de la file. À chaque reprise et à chaque passation, relire cette file face à
`chantiers.yaml`. Le début de ce titre est celui que porte `file:` dans la table des domaines (`Methode/domaines.yaml`) :
si on le renomme, on change la ligne `file:` de son domaine dans le même commit — la seule ligne de la table qu'un CdP
touche.*

- **Décidé, à cadrer en premier** (R<n>) : `<id>` — <…>.
- **Ensuite** : `<id>` — <…>.
- **À venir** : `<id>` — <…>.

---

## §4 · Les pièges vus depuis le dernier checkpoint

- <piège — parade>.
- Les autres pièges sont au §7 de la méthode et restent vrais.

---

## §5 · Le coût du CdP sur cette session

- **Ouverte** le <date heure>, **close** le <date heure>.
- **Travail réalisé** : <…>.
- **Contexte** : environ <n> jetons au dernier tour (cible : sous 700 000).
- **Premiers postes** : <…>.

---

## §6 · Les documents

**Au dépôt `<Projet>`** (source) : <liste, avec leur version>.
**Le tableau des chantiers** : `chantiers.html`, publié en artefact à <lien> — à republier au même lien.
**Au dépôt `<Projet>-App`** : le code, `banc/` (v<n>), `PROMPT_DEV_<P>.md` (v<n>), `lots/…`.
**Au projet, en miroir** : <liste>.
**Au projet, écrits une fois** : <liste>.
**Rien à téléverser à la session suivante** : elle reprend par la ligne fixe, en tête de ce fichier.
