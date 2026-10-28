# Changelog — exécutant serveur (implémentation de référence)

## 0.1.1 — implémentation de référence

Première version publiée avec le package méthode, éprouvée en production sur un projet réel. Le déployeur lit chaque
minute les ordres du dépôt privé d'ordres et n'exécute qu'une liste blanche d'actions : état, adoption du commit servi,
déploiement et retour de l'application (sur un « go »), déploiement et retour des suites, reprise d'une file arrêtée, et
des opérations de fichiers enfermées dans des zones (lister, empreinte, créer, télécharger, copier, déplacer,
décompresser, basculer, corbeille). La base ne se perd jamais : projet et volumes vérifiés avant tout geste, sauvegarde
relue avant chaque déploiement, comptes des tables d'histoire avant et après, aucun retour automatique après une
migration, aucune restauration par le déployeur. Un installateur unique pose le programme, ses minuteurs, ses clés et le
compte de transfert, sans toucher au pare-feu. Les chemins protégés par défaut sont `.env` et `backups/`.
