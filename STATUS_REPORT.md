# V.O.T. Guardian – État du projet (28/10/2025)

## 1. Résumé exécutif
- Le socle technique (backend Flask, modules audio/ML/sécurité, UI Vue) est en place mais la chaîne d'analyse n'est pas branchée de bout en bout.
- L'API `/analyze` exécute uniquement un test E2B; aucune extraction audio, inférence ML, Tenebris ou persistance n'est déclenchée.
- Le frontend dépend du mode mock (`VITE_USE_MOCK=true`) pour fonctionner; l'intégration temps réel échoue faute de payload conforme.
- Monitoring, conformité (Tenebris, Datadog) et observabilité sont documentés mais pas opérationnels.
- Aucun jeu de tests automatisés ni pipeline CI/CD n'existe; les promesses de performance/production ne sont pas démontrées.

## 2. Vue d'ensemble technique
| Domaine | Couverture actuelle | Écart critique |
| --- | --- | --- |
| API backend | Flask + endpoints `/`, `/health`, `/analyze`, `/metrics`, mock `/api/v1/analyze`. | `/analyze` retourne des logs E2B sans analyse; aucune orchestration des modules importés. |
| Audio | `AudioProcessor` calcule VOT/jitter/shimmer/SNR si `librosa`/`soundfile` installés. | Jamais invoqué; dépendances absentes par défaut, valeurs aléatoires si erreur. |
| ML | `MLPredictor` définit un CNN-LSTM et gestion GPU. | Le modèle n'est pas chargé/exploité; `torch` manquant casse l'inférence; aucun entraînement ni modèle validé fourni. |
| Sécurité (Tenebris) | Contexte Tenebris avec audit hash, destruction fictive. | Non utilisé par l'API; aucune révocation réelle ni intégration Datadog. |
| E2B | Gestionnaire de pool et scripts de validation d'images. | Pool jamais initialisé; l'endpoint crée des sandboxes ad hoc, détruit après sonde. |
| Bases de données | Client `asyncpg`, scripts init & tests, docker-compose pour PostgreSQL/RethinkDB/MindsDB. | L'application n'ouvre pas de connexion; tables jamais utilisées; tests RethinkDB/MindsDB désactivés. |
| Monitoring | Client Datadog + enregistrement métriques. | Non câblé; dépendance optionnelle; agent Docker compose mais nécessite clés. |
| Frontend | UI moderne (upload, résultats, statut système) + Pinia + Tailwind. | Fait confiance à payload `call_id/prediction` inexistant; `SystemStatus` pointe vers ports fixes; router défaut non nettoyé. |
| Infra & DevOps | Dockerfiles (backend, MindsDB), docker-compose, scripts PowerShell. | Pas de pipeline build/deploy; docs mentionnent OpenShift/ArgoCD non fournis; Dockerfiles lourds, non testés. |

## 3. Travaux réalisés / bases disponibles
- Backend Flask structuré avec configuration centralisée (`Settings`) et modules spécialisés (audio, ML, Tenebris, E2B, Datadog, PostgreSQL).
- Scripts d'installation/tests pour PostgreSQL, RethinkDB, MindsDB; docker-compose complet pour environnement local.
- Templates E2B (min/mid/full) et scripts de validation pour s'assurer des dépendances torch/librosa.
- Frontend Vue 3 + Vite + Tailwind avec composants Upload/Results/Status, store Pinia, configuration thème.
- Documentation abondante (README, roadmap, guides scriptés) décrivant la vision, dépendances, et objectifs.

## 4. Backlog restant (par priorité)
### Priorité critique (P0)
- Implémenter la vraie pipeline `/analyze` : validation audio, extraction de features, appel ML, enregistrement Tenebris, persistance PostgreSQL, réponse conforme.
- Gérer correctement l'absence de `torch`/`librosa` (grâce à dépendances, fallback ou feature flags) pour éviter des exceptions runtime.
- Aligner le frontend sur le backend réel (adapter payloads, gérer erreurs, retirer dépendance au mock).
- Vérifier et sécuriser l'utilisation des clés E2B/Datadog (configuration, secrets, failover).

### Priorité haute (P1)
- Initialiser et réutiliser un pool E2B (`E2BSandboxManager.start()`), gérer timeouts/quotas, instrumenter Tenebris.
- Activer la persistance réelle (async tasks pour `PostgreSQLClient.connect()`, stockage des analyses, audit trail).
- Câbler Datadog (ou alternative) pour métriques/événements réels; exposer `/metrics` compatible Prometheus.
- Couvrir la base de code par des tests unitaires/intégration (pipeline happy path, erreurs, sandbox indisponible).
- Documenter et fournir un modèle ML réel (fichier `.pth` validé, métadonnées, procédure de recalibrage).

### Priorité moyenne (P2)
- Nettoyer le frontend (supprimer routes de template, internationalisation, accessibilité, historique des analyses).
- Durcir sécurité : limites de taille fichier, authentification, journalisation sensible, plan de rotation des clés.
- Industrialiser DevOps : scripts make, pipelines CI, conteneurs back/frontend, publication images.
- Mettre en place de vrais tests d'intégration E2B + bases (peut être via mocks pour CI local).
- Créer documentation technique alignée avec l'état réel (diagrammes, runbooks, SLA).

### Priorité basse (P3)
- Étendre monitoring (Datadog dashboards, alerting), observabilité (traces, logs structurés).
- Préparer packaging production (OpenShift manifests réalistes, Helm charts, IaC réseau).
- Automatiser génération de rapports conformité (Tenebris, audit trail, retention).

## 5. Divergences documentation ⇔ implémentation
- README annonce une détection temps réel <500 ms, accuracy 98 %, purge Tenebris <100 ms : aucune mesure ni code ne le prouve.
- Endpoints documentés (`/analyze` retournant prediction/confidence) ne correspondent pas à la réponse JSON actuelle.
- Références à Red Hat/OpenShift/ArgoCD/GitOps sans manifests opérationnels (répertoires vides ou placeholders).
- Mention de tests pytest (unit/integration/security) alors qu'aucune suite n'est présente dans `src/tests`.
- Tenebris annonce audit Datadog et crypto mais ne fait qu'écrire en mémoire locale.

## 6. Tests & qualité
- Scripts manuels : `test_simple.py`, `test_setup.py`, `test_databases.py` (partiellement désactivés) vérifient présence fichiers/dépendances.
- Aucun test automatisé exécutant la pipeline ou le frontend; pas de couverture ni CI.
- Forte dépendance à l'environnement (API keys, bases externes) non mockées → définir stratégie de tests (mocks, sandboxes de test, feature flags).

## 7. Données & Machine Learning
- `models/vot-cnn-lstm-v2.1.pth` présent mais provenance/performance inconnues; chargement conditionné à un dict `model_state_dict`.
- Pas de pipeline d'entraînement ni de script d'évaluation; aucune gestion du drift malgré code placeholder.
- AudioProcessor dépend de libraries lourdes et renvoie des valeurs aléatoires en fallback → risque de faux positifs.
- Aucune gestion de dataset, licences audio, ni sauvegarde des features.

## 8. Infrastructure & déploiement
- Docker Compose bien renseigné mais non testé (images custom libellées, dépendance à `Dockerfile.mindsdb` privé).
- Dockerfile.dev installe énormément de dépendances, risque de build lent et non reproductible.
- Pas de manifeste Kubernetes/ArgoCD exploitable; `manifests/` contient des squelettes à compléter.
- Scripts PowerShell utiles pour Windows mais nécessitent validation/sécurisation (téléchargements non vérifiés).

## 9. Risques et points d'attention
- **Technique** : Crash runtime si `torch` absent, quotas E2B dépassés, taille binaire `librosa` > 1h builder.
- **Organisationnel** : Documentation marketing surévaluée vs état réel → risque pour parties prenantes.
- **Sécurité** : Pas d'authentification ni filtrage fichier; clés API potentiellement exposées.
- **Opérationnel** : Aucune stratégie de logs/alertes; aucun plan de reprise ni d'escalade incidents.

## 10. Recommandations (prochaines étapes 2 semaines)
1. Brancher un flux end-to-end minimal (`/analyze` → AudioProcessor → MLPredictor → réponse) et l'encadrer par des tests unitaires.
2. Stabiliser les dépendances critiques (geler versions PyPI, vérifier installation torch/librosa dans Docker/venv, charger le modèle `.pth`).
3. Faire converger frontend & backend (mêmes schémas JSON, gestion des erreurs, configuration API via `.env`).
4. Mettre en place une batterie de tests automatisés (pytest + GitHub Actions/CI local) pour éviter régressions.
5. Mettre à jour la documentation produit pour refléter l'état actuel et clarifier la feuille de route.
