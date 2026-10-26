# LA COMMANDE DU DEV — le lancement en sous-agent, et la ligne de repli

*Le CdP lance le dev lui-même (outil `Agent`, en arrière-plan), avec le modèle et le mode d'effort du cadrage. Le dev
part **sans le contexte du CdP** : cette commande est tout ce qu'il sait en plus du dépôt. Elle tient en quatre parts.*

---

## A · La commande, en quatre parts

```
1 · QUI TU ES ET CE QUE TU FAIS
Tu es le dev du lot `v<X.Y>` de <Projet>. Tu travailles seul, sans interlocuteur : tu lis, tu exécutes, tu livres, tu rends compte.
Document à exécuter : lots/v<X.Y>/<CADRAGE.md | ADDENDUM_<n>.md>, sur la branche lot/v<X.Y> du dépôt <owner>/<Projet>-App <code public : <owner>/<Projet>-Lots ; le code part du commit <sha> du dépôt public <owner>/<Projet>-App, où tu pousses le code seul>, commit de départ <sha>.
Lis avant tout, dans cet ordre : PROMPT_DEV_<P>.md (racine de la branche), le cadrage, ses addenda <et tes rapports précédents : …>. Les seules images à ouvrir : <aucune | noms>.
Rapport attendu : lots/v<X.Y>/<RAPPORT_DEV.md | RAPPORT_DEV_<n>.md>.

2 · LES CONDITIONS PRATIQUES — elles priment sur le cadrage et le prompt
- Les dépôts sont déjà rattachés à cette session : n'appelle ni add_repo ni register_repo_root.
- Tes clones vont dans /home/claude/dev_<lot>/, jamais dans les copies du CdP. Délai de commande généreux pour les clones.
- Tu ne pousses que sur lot/v<X.Y> : jamais sur main, jamais de tag, jamais --force ; en avance rapide, après un fetch.
- <Les lignes de fin des messages de commit imposées par la session, s'il y en a.>
- <Les outils déjà présents : navigateur à tel chemin, ne pas le réinstaller ; version de l'interpréteur.>

3 · LES ARRÊTS
Un point ambigu, impossible, ou qui contredit l'état réel du code : écris lots/v<X.Y>/ARRET_<n>.md, commite, pousse la branche, puis arrête-toi et dis-le dans ta réponse. Ne tranche pas.

4 · TA RÉPONSE FINALE, POUR LE CdP
- les hashs complets : commit de livraison, commit du rapport ;
- chaque critère avec OK ou ÉCART ;
- ce dont tu n'es pas sûr.
```

**Après un arrêt** : le CdP pousse l'addendum et relance — le même sous-agent s'il est encore joignable (message de
suite), sinon un neuf, dont la commande nomme aussi les rapports et arrêts précédents à lire.

**Ce qui reste au CdP pendant ce temps** : rien à attendre activement ; il est notifié à la fin. Il ne prédit jamais le
résultat d'un sous-agent en cours.

---

## B · Le repli — la ligne que le porteur colle

*Quand le CdP ne peut pas lancer de sous-agent. Le CdP donne la ligne au mot près, avec au-dessus, en gras, le modèle,
l'effort et la session : le porteur ne lit pas forcément le cadrage.*

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
