# LA COMMANDE DU DEV — le lancement en sous-agent, et la ligne de repli

*Le CdP lance le dev lui-même (outil `Agent`, en arrière-plan), avec le modèle et le mode d'effort du cadrage. Le dev
part **sans le contexte du CdP** : cette commande est tout ce qu'il sait en plus du dépôt. Elle tient en quatre parts.
**Les conditions durables sont au prompt du dev** (`modeles/PROMPT_DEV.md`, §1, §2 et §6) : **la commande ne redit que ce
qui change d'un lot à l'autre** — le document à exécuter, le dossier de travail, les branches, les lignes de commit. Le dev
ne parle qu'au CdP : par ce qu'il pousse et par sa réponse finale.*

---

## A · La commande, en quatre parts

```
1 · QUI TU ES ET CE QUE TU FAIS
Tu es le dev du lot `v<X.Y>` de <Projet>. Tu travailles seul, sans interlocuteur : tu lis, tu exécutes, tu livres, tu rends compte.
Document à exécuter : lots/v<X.Y>/<CADRAGE.md | ADDENDUM_<n>.md>, sur la branche lot/v<X.Y> du dépôt <owner>/<Projet>-App <code public : <owner>/<Projet>-Lots ; le code part du commit <sha> du dépôt public <owner>/<Projet>-App, où tu pousses le code seul>, commit de départ <sha>.
Lis avant tout, dans cet ordre : PROMPT_DEV_<P>.md (racine de la branche), le cadrage, ses addenda <et tes rapports précédents : …>. Les seules images à ouvrir : <aucune | noms>.
Rapport attendu : lots/v<X.Y>/<RAPPORT_DEV.md | RAPPORT_DEV_<n>.md>.

2 · LES CONDITIONS PRATIQUES — elles priment sur le cadrage et le prompt
- Ton dossier de travail : /home/claude/dev_<lot>/ ; jamais <les chemins des copies du CdP>, qu'il occupe lui-même.
- Tu ne pousses que sur lot/v<X.Y> <code public : et sur lot/<lot> du dépôt public, où tu pousses le code seul>.
- Fin de chaque message de commit, ces lignes : <les lignes d'attribution imposées par la session du CdP, recopiées telles quelles>.
- <Les outils déjà présents : navigateur à tel chemin, ne pas le réinstaller ; version de l'interpréteur.>
<Les dépôts rattachés, les clones à part, les branches seules, aucun processus en arrière-plan : au prompt du dev, qui les porte. Un projet sans prompt du dev les redit ici.>

3 · LES ARRÊTS
Un point ambigu, impossible, ou qui contredit l'état réel du code : écris lots/v<X.Y>/ARRET_<n>.md, commite, pousse la branche, puis arrête-toi et dis-le dans ta réponse. Ne tranche pas. Une maquette demandée : MAQUETTE_<n>.md, et arrête-toi de même (prompt du dev, §3 étape 6).

4 · TA RÉPONSE FINALE, POUR LE CdP
- les hashs complets : commit de livraison, commit du rapport ;
- chaque critère avec OK ou ÉCART ;
- ce dont tu n'es pas sûr.
```

**Après un arrêt ou une maquette** : le CdP pousse l'addendum (ou, pour une maquette, regarde les images, les montre au
porteur et recueille son verdict) et relance **le même sous-agent par message** (`SendMessage`) s'il est encore joignable ;
sinon un neuf, dont la part 1 nomme aussi les arrêts et rapports précédents à lire. **Le verdict du porteur se transmet mot
pour mot**, sans le reformuler ; un changement demandé fait un nouveau tour, `MAQUETTE_<n+1>.md`.

**Pendant ce temps** : le CdP ne touche pas aux chemins que le dev occupe — son dossier de travail, et ceux que le banc
écrit en dur ; il est notifié à la fin, n'attend rien activement et ne prédit jamais le résultat d'un sous-agent en
cours.

---

## B · Le repli — la ligne que le porteur colle

*Quand le CdP ne peut pas lancer de sous-agent. Le CdP donne la ligne au mot près, avec au-dessus, en gras, le modèle,
l'effort et la session : le porteur ne lit pas forcément le cadrage. Le prompt du dev dit alors au dev de ne dire au porteur
qu'une phrase, quand il s'arrête ou livre.*

**Sonnet · Medium · conversation neuve dans le projet**

```
Tu es le dev de <Projet>. Rattache le dépôt <owner>/<Projet>-App (outil add_repo, accès push), clone la branche lot/v<X.Y>, lis PROMPT_DEV_<P>.md puis lots/v<X.Y>/CADRAGE.md, et exécute.
```

**Pour un addendum, dans la session de dev encore ouverte :**

```
L'addendum <n> est poussé sur lot/v<X.Y> : git pull --rebase, lis lots/v<X.Y>/ADDENDUM_<n>.md, et reprends à l'étape qu'il indique.
```

*Piège vu : une conversation de dev ouverte à la main peut échouer à rattacher un dépôt privé ; le sous-agent, lui,
hérite des dépôts de la session du CdP.*
