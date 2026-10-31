# L'exécutant local, le repli — Claude Code sur le PC, piloté par fichiers · v2
### 25 octobre 2026 · éprouvé sur un projet réel (captures d'écran d'un jeu installé sur le PC)

> **Le pont d'abord.** Depuis que l'application Claude offre un **pont** quand la machine du porteur est reliée — dossiers
> reliés (lire, écrire), terminal s'il est offert, écran par l'usage de l'ordinateur, le porteur validant l'accès dans la
> conversation du CdP —, **la session du CdP travaille elle-même sur la machine** (méthode §1, skill §5 bis). **Ce
> document décrit désormais le repli**, pour quand le pont ne s'offre pas. Raison de ce rang : piloté par fichiers,
> l'exécutant s'est bloqué quand le porteur était loin de sa machine — demandes d'accès à l'écran refusées, attente sans fin.

*Pour le travail qui doit tourner **sur le PC du porteur** (un jeu, une application installée, l'écran, un matériel) et que le
CdP, dans le cloud, ne peut pas exécuter. Le reste de la méthode ne change pas : le CdP cadre et réceptionne, l'exécutant
exécute, le porteur décide.*

---

## 1. Quand s'en servir

- **Quand le pont est offert**, le CdP travaille lui-même sur la machine : ce document ne sert pas.
- **Quand le pont ne s'offre pas** (la machine n'est pas reliée, ou son terminal n'est pas offert), le CdP voit au mieux
  les dossiers du PC (dossiers connectés à la conversation : lister, lire, écrire des fichiers), mais **n'y a pas de
  terminal** : il ne lance rien sur la machine.
- Le contrôle de l'écran par le CdP ne remplace pas un shell : les terminaux et éditeurs y sont en clic seulement (pas de
  frappe).
- Dès qu'il faut **exécuter** sur le PC (un script Python, un programme, une capture d'écran en pleine résolution) et que
  le pont ne le permet pas, on passe par une **session Claude Code locale** : app Desktop, onglet Code, environnement
  **Local**. C'est l'exécutant.
- Un lot qui ne touche que du code dans un dépôt reste au dev en sous-agent, dans le cloud (méthode §5).

## 2. Les rôles

| | fait | ne fait pas |
|---|---|---|
| **CdP** (cloud) | écrit cadrages et addenda dans l'espace du projet ; lit les sorties ; donne le feu vert ; répond aux questions ; re-mesure à froid ; verse au dépôt | n'exécute rien sur le PC, au repli |
| **Exécutant** (Claude Code local, Sonnet) | lit le cadrage, exécute, écrit son état et ses questions en fichiers, rédige le rapport | ne décide rien hors cadrage ; ne parle pas au porteur dans son chat une fois la synchro lancée |
| **Le porteur** | colle **une ligne** par cadrage ou addendum ; accepte les autorisations ; fait les gestes physiques demandés (lancer le jeu, un réglage à l'écran) | ne relaie pas les messages entre les deux |

## 3. L'espace du projet sur le PC

**Jamais dans les dossiers d'une application** (jeu, logiciel) : tout vit sous `<racine>\<Projet>\`, créé par le CdP —
`<racine>` est un dossier à toi, le même pour tous tes projets (par exemple `D:\Claude_AI`).

```
<racine>\<Projet>\
  README.md    ce rangement
  cadrages\    cadrages et addenda — écrits par le CdP, l'exécutant n'y écrit pas
  rapports\    rapports de l'exécutant
  tools\       scripts de l'exécutant (+ config.json local, jamais publié)
  out\         données produites (restent sur le PC : ce sont des données, pas du code)
  sync\        le dialogue par fichiers (§4)
```

Seule exception : ce qu'une application impose de placer chez elle (un hook, une ligne de configuration), avec
sauvegarde du fichier modifié et une ligne ajoutée au plus.

## 4. Le protocole de synchronisation

Tout passe par `sync\`. L'exécutant interroge ces fichiers **toutes les 5 s, sans limite de durée**.

| fichier | écrit par | sens |
|---|---|---|
| `STATUS.txt` | exécutant | une ligne horodatée réécrite à chaque étape : `2026-10-25 13:30:02 \| ATTENTE_GO \| hook OK, check.png prêt`. États : `ATTENTE_GO`, `<ÉTAPE> <n>/<total>`, `QUESTION`, `ARRET`, `TERMINE` |
| `check.png` (ou tout fichier de contrôle) | exécutant | un échantillon du résultat **avant** le gros du travail, que le CdP regarde |
| `GO.txt` | CdP | feu vert ; l'exécutant le supprime après l'avoir lu |
| `QUESTION.txt` | exécutant | une question ou un arrêt du cadrage ; `STATUS` passe à `QUESTION` |
| `ANSWER.txt` | CdP | la réponse ; l'exécutant la supprime après l'avoir lue |

Règles :
1. **Aucune question dans le chat** de l'exécutant une fois la synchro lancée : son chat ne s'affiche pas sur le web et
   Le porteur n'est pas devant.
2. **Le CdP regarde le contrôle avant de donner le feu vert** — c'est là qu'on voit une fenêtre devant le jeu, un
   mauvais mode d'affichage, une échelle fausse.
3. Si l'exécutant a besoin du **premier plan** (capture d'écran), il met lui-même l'application devant et vérifie le
   focus avant chaque action ; trois échecs de suite → `QUESTION`.
4. Ce qui dépend du porteur (un geste, une décision) : le CdP le lui demande dans sa conversation, puis répond par
   `ANSWER.txt`.

## 5. Le déroulé type

1. Le CdP dépose `cadrages\CADRAGE_<lot>.md` (forme du `modeles/CADRAGE.md`, plus le §4 ci-dessus ou un renvoi à un
   addendum de synchronisation).
2. Le porteur ouvre une session Claude Code locale **sur `<racine>\<Projet>`**, Sonnet, effort du cadrage, session neuve,
   et colle :
   `Lis cadrages\CADRAGE_<lot>.md et exécute-le strictement. Tu es exécutant : au moindre point ambigu ou hors cadrage, arrête-toi et dis-le. Dialogue par fichiers dans sync\.`
3. L'exécutant prépare, écrit `check.png`, passe à `ATTENTE_GO`.
4. Le CdP regarde, écrit `GO.txt`, suit `STATUS` (une vérification par minute environ, par des attentes en tâche de fond).
5. L'exécutant termine, écrit `rapports\RAPPORT_<lot>.md` (qui commence par « Ce dont je ne suis pas sûr »), passe à
   `TERMINE`.
6. Le CdP **re-mesure à froid** sur les sorties, regarde les rendus, puis verse cadrages et rapports au dépôt `-Lots`
   et le code livré au dépôt de code (relecture du diff avant tout dépôt public).
7. Un addendum : le CdP le dépose dans `cadrages\`, le porteur colle une ligne (`Lis cadrages\ADDENDUM_<n>_<lot>.md et
   applique-le. Dialogue toujours par fichiers.`).

## 6. Pièges vus

- **L'exécutant s'arrête sur une demande d'autorisation** (lancer une commande, écrire hors de son dossier, supprimer) :
  elle ne s'affiche que dans l'app Desktop. Symptôme : `STATUS` figé. Le CdP prévient le porteur, qui l'accepte.
- **Une fenêtre devant l'application** (la conversation, une notification) gâche une capture : d'où le contrôle et la
  vérification du focus.
- **Un dossier de travail ouvert ailleurs que dans l'espace du projet** oblige à des autorisations d'accès à chaque
  étape : ouvrir la session locale directement sur `<racine>\<Projet>`.
- **Le shell de l'exécutant peut bloquer une suppression** quand il a le dossier visé comme répertoire courant.
- **Les chemins propres au PC** (dossier de travail, installation de l'application, taille d'écran) vont dans un
  `config.json` local ignoré par git, jamais en dur dans le code publié.
