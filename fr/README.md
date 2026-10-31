# Méthode CdP — package

*English version: [README](../README.md).*

Une méthode de développement avec Claude : un **chef de projet** (CdP, Opus) qui décide avec toi, cadre, lance le dev
en sous-agent et réceptionne ; un **dev**, dont le CdP choisit le modèle et le mode d'effort à chaque lot, qui construit
un lot à la fois ; toi, qui décides et valides à l'écran. Tout circule par GitHub.

**Commencer par [`NOYAU.md`](NOYAU.md)** : deux pages qui se suffisent pour un porteur seul avec un CdP, et la table des
extensions à ajouter quand un signe vécu le demande. Puis [`LISEZ_MOI.md`](LISEZ_MOI.md) ; un CdP, plusieurs modules
indépendants ou des modules liés avec un coordinateur : `LISEZ_MOI.md` §2 bis. Les termes sont au
[`GLOSSAIRE.md`](GLOSSAIRE.md) ; ce que la méthode suppose du produit Claude, au
[`DEPENDANCES_CLAUDE.md`](DEPENDANCES_CLAUDE.md). **La méthode a été éprouvée sur trois projets, dont un complexe**
(plusieurs CdP en parallèle sur plusieurs produits, un serveur de production).

| chemin | porte |
|---|---|
| `NOYAU.md` | à lire en premier : la méthode d'un CdP seul en deux pages, et la table des extensions |
| `GLOSSAIRE.md` | chaque terme de la méthode et le document où il vit |
| `DEPENDANCES_CLAUDE.md` | les fonctions du produit Claude dont la méthode dépend, ce qui casse si l'une change, le repli |
| `LISEZ_MOI.md` | le mode d'emploi, l'architecture en trois couches, les gestes pour démarrer un projet |
| `1_INSTRUCTIONS_PROJET.md` | le texte des instructions d'un projet claude.ai |
| `2_PROMPT_AMORCAGE_CDP.md` | le premier message de la première session de CdP |
| `3_GITHUB.md` | les dépôts, le circuit d'un lot par branche, les pièges des sessions |
| `modeles/` | méthode, prompt du dev, cadrage, commande du dev, exécutant local (le repli), vivants et leurs scripts (tableau, vérificateur, archivage et recherche des chantiers), squelettes de dépôts ; facultatif : l'exécutant serveur (`EXECUTANT_SERVEUR.md`, dont le pont d'échange de fichiers du dépôt d'ordres), dont l'implémentation de référence est publiée une seule fois, à la racine, en `templates/server-runner/` ; l'arbitre des vivants (`ARBITRE.md`, mode C : rôle, pourquoi, mise en place, lecture) et la table des domaines qu'il lit (`domaines.yaml`) |
| `skill/SKILL.md` | la skill personnelle `methode-cdp`, à personnaliser (§1 et §8) puis installer |

*Package v18 (skill v17) — historique dans `LISEZ_MOI.md` §7. Licence MIT.*
