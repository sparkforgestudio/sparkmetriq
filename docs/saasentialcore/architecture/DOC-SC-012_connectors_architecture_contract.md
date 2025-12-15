Voici **DOC-SC-012 — Connectors Architecture Contract**, version longue, exhaustive, cohérente avec SaasentialCore, Sparkmetriq S2, Sparkpusher, les retrys (DOC-005), la sécurité (DOC-SC-005 & DOC-SC-010), l’observabilité (DOC-SC-009), et le multi-startup / multi-produit (DOC-SC-004).

Ce document est **critique** : les connecteurs sont le point de contact avec les plateformes externes (Instagram, TikTok, Threads, Facebook, Twitter/X, Reddit, Snapchat, OnlyFans, Telegram, etc.).
Ils doivent être **fiables, isolés, observables, testables, idempotents et sécurisés**.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-012_connectors_architecture_contract.md
```

---

# 📘 `DOC-SC-012_connectors_architecture_contract.md`

```markdown
---
title: DOC-SC-012 — Connectors Architecture Contract
version: 1.0
status: Stable
category: SaasentialCore / Connectors / External Integrations / SRE / Resilience
last_updated: 2025-02-16
---

# 1. Objectif du document

Le Connectors Architecture Contract définit :

- la structure standard des connecteurs externes,
- les règles d’appel API unifiées,
- les stratégies de retry/backoff/idempotence (aligné DOC-005),
- les règles de sécurité et secrets (aligné DOC-SC-010),
- l’isolation tenant stricte (DOC-SC-004),
- les obligations d’observabilité (DOC-SC-009),
- les mécanismes de timeout, circuit breakers, failovers,
- la compatibilité multi-produits (Sparkmetriq, Sparkpusher, futurs modules),
- les conventions pour les tests & mocks (DOC-SC-008).

Les connecteurs doivent pouvoir gérer :

- Instagram Graph API  
- TikTok Publishing API  
- Threads API  
- Facebook Pages / IG Business  
- Twitter/X API  
- Reddit API  
- Snapchat API  
- OnlyFans unofficial API (proxy mode)  
- Telegram Bot / Client API  

---

# 2. Principes fondamentaux

## ✔ 2.1. Les connecteurs sont totalement isolés du reste du code  
Aucune plateforme externe n’a d’impact sur l’architecture interne.

## ✔ 2.2. Un connecteur ne doit jamais faire planter un worker  
Les erreurs doivent être isolées, classifiées, observées.

## ✔ 2.3. Zero-trust sur les plateformes externes  
Chaque réponse doit être validée.

## ✔ 2.4. Aucun secret dans le code  
Les connecteurs utilisent Tenant Secret Store (DOC-SC-010).

## ✔ 2.5. Observabilité complète  
Toutes les erreurs, latences, timeouts, retries doivent être loggés & métriqués.

## ✔ 2.6. Idempotence obligatoire  
Un connecteur doit produire le même résultat si un job est ré-exécuté.

---

# 3. Architecture générale des connecteurs

```

products/<product_id>/connectors/
base.py
instagram_connector.py
tiktok_connector.py
threads_connector.py
...

````

Structure du base connector :

```python
class BaseConnector:
    def __init__(self, http_client, secret_provider, logger, metrics):
        self.http = http_client
        self.secrets = secret_provider
        self.log = logger
        self.metrics = metrics

    async def call(self, context, payload):
        raise NotImplementedError
````

---

# 4. Règles DI (aligné DOC-SC-003)

Les connecteurs doivent être enregistrés dans DI :

```python
container.register(
    "sparkmetriq.instagram",
    lambda: InstagramConnector(
        http_client=HttpClient(timeout=10),
        secret_provider=container.resolve("secret_provider"),
        logger=get_logger("instagram"),
        metrics=PrometheusMetrics("instagram")
    )
)
```

Interdit :

* instancier un connecteur directement dans le code métier,
* lire les secrets via `os.getenv`,
* bypass DI pour la configuration.

---

# 5. Secrets Management (aligné DOC-SC-010)

Chaque connecteur doit récupérer ses secrets via :

```python
token = secret_provider.get(context, "instagram_access_token")
```

Interdit :

* stocker le token dans les logs,
* envoyer le token dans les traces,
* transmettre le token à un job suivant.

---

# 6. API Boundaries & HTTP Client

### Tous les connecteurs doivent utiliser :

* un HttpClient commun,
* des timeouts uniformisés,
* des headers standardisés,
* un retry policy configurable.

### Configuration obligatoire :

```
timeout = 10s
connect_timeout = 3s
max_retries = 3
backoff = expo + jitter
circuit_breaker_enabled = true
```

---

# 7. Erreurs : classification obligatoire

Chaque appel doit classifier l’erreur selon 5 catégories :

### 7.1. PermanentFailure

Erreurs dues à :

* contenu interdit
* violation policy plateforme (ban soft)
* endpoint inconnu

Action : **fail immediately**

### 7.2. TransientFailure

Erreurs dues à :

* réseau instable
* timeouts
* erreurs 5xx

Action : **retry + backoff**

### 7.3. AuthFailure

Erreurs dues à :

* token expiré
* token invalide

Action :

* **refresh token** si possible
* sinon fail avec instruction de renouvellement tenant

### 7.4. RateLimitFailure

Erreurs 429 / quota dépassé
Action :

* exponential backoff ajusté par headers
* propagation d’événement quota (DOC-SC-006)

### 7.5. UnknownFailure

Erreurs inattendues
Action :

* log CRITICAL
* retry limité
* circuit breaker

---

# 8. Observabilité (aligné DOC-SC-009)

### 8.1. Logs

```json
{
  "event": "connector.call",
  "connector": "instagram",
  "startup_id": "stp_1",
  "org_id": "org_77",
  "product_id": "sparkmetriq",
  "endpoint": "/publish",
  "status": "success",
  "latency_ms": 822,
  "trace_id": "xyz-11",
  "timestamp": "..."
}
```

### 8.2. Metrics Prometheus

```
connector_requests_total{connector="instagram", product_id="sparkmetriq"}
connector_latency_seconds_bucket{connector="instagram"}
connector_failures_total{connector="instagram", type="transient"}
connector_retries_total{connector="instagram"}
connector_circuit_breaker_open_total
```

### 8.3. Traces OpenTelemetry

Chaque appel doit générer un `connector.call` span.

---

# 9. Circuit Breaker

Chaque connecteur doit implémenter :

* open after N consecutive failures
* half-open after timeout
* automatic recovery

Schéma minimal :

```python
if breaker.is_open():
    raise CircuitOpenError()
```

---

# 10. Idempotence (DOC-005)

Chaque connecteur doit :

* accepter un `idempotency_key` généré par S2 Scheduler
* renvoyer le même résultat si re-exécuté
* détecter duplication côté plateforme si API le permet

---

# 11. Data Shaping: uniformisation des réponses

Toutes les réponses doivent suivre ce format :

```json
{
  "status": "success",
  "external_id": "...",
  "permalink": "...",
  "raw": {...}
}
```

En cas d’erreur :

```json
{
  "status": "error",
  "type": "transient",
  "message": "...",
  "raw": {...}
}
```

---

# 12. Tests (DOC-SC-008)

## Tests unitaires :

* mock http client
* mock secret provider
* test error classification
* test retry logic

## Tests d’intégration :

* simulateurs API
* mock server (WireMock, HTTPX MockTransport)
* test rate-limit
* test expiration token

## Tests E2E :

* scheduler → dispatcher → worker → connector → platform mock
* validation des flux S2 / S2-immediate-publish

---

# 13. CI/CD Compliance Rules

### 🚫 Bloquant :

* secret dans logs
* absence de classification d’erreur
* absence de retry policy
* absence de trace span
* absence de metrics connector
* instanciation connecteur hors DI
* appels HTTP sans timeout
* dépendance connecteur → un autre produit
* read/write secret sans tenant context

### ⚠ Warning :

* absence d'audit usage API externe
* absence de circuit breaker
* absence de tests E2E

---

# 14. Invariants non négociables

1. Aucun connecteur ne doit empêcher le worker de tourner.
2. Toute erreur doit être classifiée sans exception.
3. Le secret doit toujours être contextualisé tenant.
4. Idempotence obligatoire pour tous les connecteurs.
5. Observabilité complète : logs + metrics + traces.
6. Retry/backoff obligatoires pour erreurs transientes.
7. Toute PR violant DOC-SC-012 est bloquée.

---

# 15. Conclusion

DOC-SC-012 constitue le **standard unifié des connecteurs externes** pour la plateforme SaasentialCore :

* résilience maximale (SRE++),
* sécurité totale,
* isolation tenant stricte,
* testabilité optimale,
* compatibilité multi-produit,
* extensibilité future (ex : Pinterest, LinkedIn…),
* intégration transparente dans S2/S3/S4,
* fiabilité industrielle.

Il garantit que les connecteurs sont robustes, sûrs, observables et cohérents dans tout l’écosystème.

```

### 👉 **DOC-SC-013 — Scheduler & Dispatcher Deep Spec (S2 engine interne)**
