Sparkmetriq System Reference Document v1
1. Objectif du document
Ce document fournit une référence unifiée et complète de la stack Sparkmetriq. Il remplace les fichiers d’exemple précédemment dispersés dans le projet et offre une version consolidée de leur logique, de leurs responsabilités et de leurs interactions. Il sert de base pour maintenir, déployer et étendre l’infrastructure sur une architecture multi-nœud.
________________________________________
2. Architecture générale Sparkmetriq
Sparkmetriq repose sur une architecture distribuée optimisée pour la haute disponibilité, la séparation des responsabilités et l’évolutivité.
2.1. Rôles des nœuds (configuration OVH)
•	Node 1 (ADVANCE-2) : Base de données & message broker
o	MongoDB (ReplicaSet + WiredTiger tuning)
o	RabbitMQ (AMQP + Management UI)
•	Node 2 (RISE-S-2) : API & Frontend
o	API FastAPI (backend Python)
o	Caddy (reverse proxy, automatic TLS, HTTP/2)
•	Node 3 (RISE-S-2) : Workers & Scheduler
o	Celery workers (tâches lourdes)
o	Scheduler Celery Beat
o	Pipelines de traitement intensif
2.2. Principes clés
•	Isolation des services critiques
•	Tagging strict des images (pas de latest)
•	Sécurité renforcée (env vars obligatoires, zero trust interne)
•	Communication interne via réseau Docker
•	Ports critiques vérifiés pré-déploiement
________________________________________
3. Stack Docker
L’application est orchestrée via docker-compose.yml sur chaque nœud avec services spécifiques.
3.1. Versioning des images
Les versions sont définies dans versions.env pour garantir les déploiements reproductibles.
•	MongoDB : 7.0.25
•	RabbitMQ : 3.13.4-management
•	Caddy : 2.8.4
•	API / workers: images Docker taggées manuellement
Cela garantit cohérence, rollback et auditabilité.
________________________________________
4. Gestion des variables d’environnement
Les fichiers .env.example et .env définissent toutes les variables nécessaires.
4.1. Principales catégories
•	Domaines et URLs
•	Credentials MongoDB et RabbitMQ
•	Paramètres de réplication Mongo
•	Credentials applicatifs
•	Tags Docker
•	Options de tuning (cache WiredTiger, pool DB, etc.)
4.2. Templating MongoDB
Le fichier d’initialisation 01-users.js est automatiquement généré via un script pour injecter :
•	APP_DB_USER
•	APP_DB_PASS
•	APP_DB_NAME
Cela assure un provisioning cohérent et non manuel.
________________________________________
5. Scripts système et DevOps
5.1. Script preflight.sh** (Production Preflight Checks)**
Permet de valider l’environnement avant tout déploiement.
Vérifications effectuées :
•	Présence des binaires essentiels (docker, docker compose)
•	Présence des fichiers critiques (docker-compose.yml, .env, versions.env, Caddyfile)
•	Chargement et vérification des variables essentielles
•	Check des ports critiques : 80 et 443
5.2. Script smoke.sh** (Smoke Test HTTP)**
Test rapide après déploiement :
•	Vérifie le code HTTP 200 sur /health
•	Teste via HTTPS
Indispensable pour GitHub Actions et pour les déploiements automatiques.
5.3. Makefile
Standardisation des commandes :
•	make up / down / restart
•	make preflight
•	make smoke
•	make logs
•	make build-api / build-worker
Permet aux développeurs d’interagir avec le projet sans mémoriser les commandes.
________________________________________
6. Reverse Proxy : Caddy
Caddy est utilisé comme proxy moderne pour l’API et le frontend.
6.1. Rôles
•	Terminaison TLS automatique via Let’s Encrypt
•	HTTP/2 et HTTP/3 QUIC
•	Reverse proxy vers le backend
6.2. Structure générale
•	Redirection HTTP → HTTPS
•	Configuration par domaine
•	Gestion des headers de sécurité
Il remplace avantageusement Nginx dans un contexte multi-nœud grâce à sa simplicité et son automation native.
________________________________________
7. Workflow de déploiement
7.1. Étapes standards
1.	Commit → Git push
2.	GitHub Actions build images (API, workers)
3.	Tagging automatique
4.	Preflight sur chaque nœud
5.	Pull des images
6.	Docker compose up -d
7.	Smoke tests
8.	Notification (Telegram / Slack)
7.2. Atomicité du déploiement
Les nœuds peuvent être mis à jour indépendamment :
•	Node 3 (workers) d’abord
•	Node 2 (API)
•	Node 1 (DB) uniquement pour migrations planifiées
________________________________________
8. Monitoring & Observabilité
Sparkmetriq repose sur une stratégie d’observabilité intégrée.
8.1. Logs
•	Logs structurés JSON
•	Tags : service, node, correlation_id
•	Routage vers une messagerie Telegram pour erreurs critiques
8.2. Metrics
•	RabbitMQ : taux de queue, messages non ack
•	MongoDB : connexions, réplication, slow queries
•	API : taux d’erreur, latence
8.3. Dashboards
Prometheus + Grafana (option standardisée mais non obligatoire).
________________________________________
9. Scheduler & Workers
9.1. Scheduler
Responsable des tâches planifiées :
•	publication de contenus
•	tâches périodiques
•	gestion pipelines
9.2. Workers Celery
Fonctionnement :
•	Concurrency ajustée selon CPU
•	Routing des tâches selon type
•	Dead-letter routing pour erreurs graves
9.3. Backend MongoDB
Stocke :
•	Résultats de tâches
•	Statuts
•	Logs utiles
________________________________________
10. Exigences techniques
•	Python 3.11+
•	Docker 24+
•	Docker Compose V2+
•	Caddy 2.8+
•	MongoDB 6+
•	RabbitMQ 3.13+
________________________________________
11. Bonnes pratiques Sparkmetriq
11.1. Sécurité
•	Pas de credentials en dur
•	.env ignoré dans Git
•	Permissions strictes sur Node 1
•	Rotation périodique des mots de passe DB
11.2. Performance
•	Indexation MongoDB obligatoire
•	TTL sur collections de logs
•	Préférer les opérations bulk
11.3. Maintenance
•	tests smoke après chaque release
•	backups automatisés Mongo
•	supervision RabbitMQ
________________________________________
12. Roadmap technique (résumé)
•	Intégration monitoring avancé
•	Architecture full multi-nœud
•	Standardisation des connecteurs API
•	Mise en place scheduler distribué
•	Optimisation workers CPU-bound + IO-bound
________________________________________
13. Conclusion
Ce document fournit la base de référence consolidée pour tous les déploiements et maintenances Sparkmetriq. Il remplace les fichiers techniques dispersés et sert désormais comme point d’entrée unique pour comprendre et exploiter la stack.
Product Foundations v1.0 — Sparkmetriq
1. Raison d’être Produit (Guidée par INSPIRED de Marty Cagan)
Sparkmetriq n’est pas une simple application SaaS : c’est une suite orchestrée destinée à automatiser, augmenter et scaler les opérations des agences de créateurs et influenceurs. Selon les principes de product/market fit, la valeur d’un produit technologique réside dans la capacité à résoudre un problème critique, clairement ressenti par une audience prête à payer. Pour Sparkmetriq, ces problèmes sont :
•	la fragmentation des workflows (publication, chat, IA, analytics),
•	la saturation opérationnelle (10–100 comptes à gérer),
•	le manque d’outils unifiés pour orchestrer contenus, conversations et tunnels.
Les fondations Produit positionnent Sparkmetriq comme une suite modulaire, chaque module étant autonome mais renforçant la valeur globale lorsqu’ils sont combinés.
________________________________________
2. Principes Structurants du Produit
2.1. Modélisation orientée “Problème → Flux → Résultat”
Chaque module doit répondre à un flux métier clair :
•	Publish → planification → orchestration → diffusion,
•	Engage → conversations → intent → génération → réponse → analytics,
•	Operate → supervision → décisions → automatisation,
•	Intelligence → analyse → enrichissement → recommandations.
2.2. Continuous Discovery & Delivery
•	cycles courts de prototypage (API mock, live-data prototypes),
•	feature flags sur tous les modules,
•	tests de valeur et d’utilisabilité sur agences pilotes.
2.3. Multi-tenant natif & extensibilité
•	isolation par org_id,
•	connecteurs “plug-and-play”,
•	services découplés publiés via événements.
________________________________________
3. Architecture Produit : les 4 piliers fonctionnels
Pilier 1 — Publish (Automatisation Contenus)
•	orchestrateur central (dispatcher),
•	scheduler haute fiabilité (verrouillage, retry, idempotence),
•	connecteurs multi-plateformes,
•	A/B testing créatif,
•	calendar temps réel.
Objectif Produit :
Réduire de 70% le temps opérationnel lié à la publication multi-comptes.
Pilier 2 — Engage (Chat + IA + LLM Twin)
•	Intent Engine hybride,
•	Chat omnicanal,
•	RAG Unified,
•	LLM Twin personnalisé.
Objectif Produit :
Fournir une IA stable, pilotable, conforme à la personnalité de chaque muse.
Pilier 3 — Operate (Management d’agence)
•	roles, permissions, multi-agency,
•	dashboards opérations,
•	supervision des tâches critiques,
•	alertes + logs enrichis.
Objectif Produit :
Transformer Sparkmetriq en cockpit d’agence permettant de gérer 10 à 100 modèles.
Pilier 4 — Intelligence (BI + Pricing + Reco)
•	BI Insights,
•	recommandations de pricing,
•	scoring dynamique,
•	prévisions de conversion.
Objectif Produit :
Rendre chaque muse systématiquement performante grâce à l’IA.
________________________________________
4. Foundation Technique (Observabilité, Résilience, Scalabilité)
•	logs structurés,
•	traces corrélées,
•	idempotence de bout en bout,
•	retries maîtrisés,
•	services stateless.
________________________________________
5. Vision Long Terme : Sparkmetriq Suite
•	automatisation totale des tunnels,
•	optimisation continue via feedback,
•	simulation IA des audiences,
•	jumeaux conversationnels avancés.
________________________________________
6. Synthèse (Executive Summary)
Sparkmetriq = suite modulaire + architecture distribuée + IA-first + observabilité + extensibilité.
________________________________________
Engineering Contracts v1.0 — Documents “Non Négociables”
Objectif : réduire les erreurs de type “runtime config / localhost fallback / routes non montées / response models implicites / quotas incohérents / retries empilés”. Ces contrats sont considérés comme normatifs.
DOC-001 — Dependency Injection Contract
Règles non négociables
1.	Single Source of Truth DB : un unique provider DB (ex. api/databases/* ou saasentialcore/databases/*) est autorisé.
2.	Aucun service core ne peut être instancié sans DI : interdiction de QuotasService() / SchedulerService() / FooService() “à la main” dans les routes.
3.	Bridge obligatoire : les routes consomment un bridge (SaasentialCoreBridge) construit via DI.
4.	Aucun fallback implicite (ex. localhost:27017) : tout config runtime doit venir de settings/env et être injecté.
Matrice : composant → dépendances → injection
•	Routes FastAPI → Depends(get_saasential_bridge)
•	Services métier → reçoivent DB/clients via constructeur uniquement depuis le bridge
•	Celery tasks → get_runtime_container() / init_worker_container(settings)
Exemples
✅ Bon
@router.post(...)
def schedule_post(payload: UnifiedPostPayload, bridge=Depends(get_saasential_bridge)):
    return bridge.quotas.schedule(payload)
❌ Mauvais
def schedule_post(payload: UnifiedPostPayload):
    quotas = QuotasService()  # pas de DB injectée
    return quotas.schedule(payload)
Checklist de validation
________________________________________
DOC-002 — Shim Pattern Standard (api/ → products/*)
Rôle d’un shim
•	Compatibilité et redirection uniquement
•	Zéro logique métier
•	Contrat stable et plan de suppression
Règles d’implémentation
1.	Imports lazy (import tardif dans la fonction) pour éviter ModuleNotFoundError.
2.	Fallback explicite : si le module cible n’est pas présent, renvoyer une erreur claire.
3.	Headers de dépréciation : X-API-Deprecated, X-API-Sunset, Link doc.
4.	Checklist route list : validation via app.routes + openapi.json.
Template shim
@router.get("/legacy/path", include_in_schema=False)
def legacy_entry(request: Request):
    try:
        from products.sparkmetriq.api.routes.new import handler
    except Exception as e:
        raise HTTPException(500, detail=f"Shim target unavailable: {e}")

    response = handler(request)
    response.headers["X-API-Deprecated"] = "true"
    response.headers["X-API-Sunset"] = "2026-03-01"
    return response
________________________________________
DOC-003 — API Schema & Response Contract
Règles non négociables
1.	No implicit response model : chaque route définit response_model=....
2.	No service-layer types in API responses : les réponses utilisent des schémas api/schemas/*.
3.	Enums exposés = Enum(str, Enum).
4.	Error envelope standard : format unique des erreurs.
Error Envelope
{
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "...",
    "details": {"org_id": "..."},
    "correlation_id": "..."
  }
}
________________________________________
DOC-004 — Quotas State Machine
Questions contractuelles
•	incrément à la planification ?
•	incrément à l’exécution ?
•	rollback en cas d’échec ?
•	publish immédiat ?
Proposition d’état (exemple)
•	RESERVED (quota réservé à la planification)
•	CONSUMED (quota consommé à l’exécution)
•	RELEASED (réservation annulée)
Invariants
•	scheduled_posts >= 0
•	reset périodique
•	idempotence par job_key
________________________________________
DOC-005 — Retry Policy & Idempotency
Principe central
Un seul niveau de retry par catégorie d’échec, sinon amplification des pannes.
Table “qui retry quoi”
•	Connecteur (429/5xx) → retry local borné (backoff + jitter)
•	Scheduler → retry orchestration (erreurs transitoires)
•	Celery → retry infra (worker crash / timeouts)
Idempotency key
•	job_id + platform + account_id + content_hash
•	dédup côté dispatch
________________________________________
Appendix — Prompt Cursor (Pack DOC-001 → DOC-005)
Prompt (à copier-coller dans Cursor)
Contexte : Tu es un Staff Engineer FastAPI/Python. Le repo Sparkmetriq a des problèmes de DI runtime (DB/bridge/config), shims api→products, response models implicites, quotas contractuels, et retries empilés. Je veux produire 5 documents normatifs + appliquer les modifications minimales dans le code pour que les tests E2E n’utilisent jamais localhost:27017 par défaut.
Livrables :
1.	Crée docs/architecture/DOC-001_dependency_injection_contract.md
2.	Crée docs/architecture/DOC-002_shim_pattern_standard.md
3.	Crée docs/architecture/DOC-003_api_schema_response_contract.md
4.	Crée docs/architecture/DOC-004_quotas_state_machine.md
5.	Crée docs/architecture/DOC-005_retry_policy_idempotency.md
Contraintes :
•	Les docs doivent contenir : règles non négociables, matrice composant→dépendances→injection, exemples bon/mauvais, checklists.
•	Le code doit respecter :
o	routes : utilisent Depends(get_saasential_bridge)
o	bridge construit avec DB injectée
o	aucun service core instancié sans DB injectée
o	aucun fallback implicite localhost
•	Ajoute un petit guide “E2E test overrides” : comment override get_core_db / get_saasential_bridge dans pytest.
Tâches code minimales :
•	Localise les instanciations directes (QuotasService(), SchedulerService(), etc.) dans api/routes/* et remplace par DI.
•	Ajoute/centralise get_core_db() et get_saasential_bridge() dans api/deps.py (ou équivalent), sans circular imports.
•	Assure que les settings DB sont chargés via un seul module api/settings.py.
Sortie attendue :
•	Donne le contenu complet des 5 docs.
•	Donne un diff minimal (ou patch) des fichiers Python modifiés, avec chemins exacts.
•	Donne une checklist finale de validation (pytest, openapi, import check).

