Voici **DOC-SC-017 — S2 Failure Modes & Reliability Playbook**,
version **longue**, opérationnelle, et **orientée production réelle**, alignée SRE++, DDIA, *Release It!*, et totalement cohérente avec SC-001 → SC-016.

Ce document est **le playbook de survie de Sparkmetriq S2** :
il décrit **quoi casse**, **pourquoi**, **comment détecter**, **comment réagir**, **comment éviter la récidive**.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-017_s2_failure_modes_reliability_playbook.md
```

---

# 📘 `DOC-SC-017_s2_failure_modes_reliability_playbook.md`

```markdown
---
title: DOC-SC-017 — S2 Failure Modes & Reliability Playbook
version: 1.0
status: Stable
category: SaasentialCore / Sparkmetriq S2 / Reliability / SRE
last_updated: 2025-02-18
---

# 1. Objectif du document

DOC-SC-017 définit le **playbook officiel de fiabilité** de Sparkmetriq S2.

Il formalise :
- les **modes de panne connus et anticipés**,
- les **signaux faibles et forts** de dégradation,
- les **stratégies de mitigation immédiates**,
- les **mécanismes de protection structurelle**,
- les **procédures de recovery**,
- les **invariants SRE++ non négociables**.

Ce document est destiné :
- aux développeurs backend,
- aux DevOps / SRE,
- aux exploitants production,
- aux audits post-incident.

---

# 2. Philosophie SRE appliquée à S2

## 2.1. Tout cassera, mais pas n’importe comment

Sparkmetriq S2 est conçu pour :
- **échouer localement**,
- **isoler la panne**,
- **se rétablir automatiquement**,
- **ne jamais corrompre les données**,
- **ne jamais violer l’isolation tenant**.

## 2.2. Hiérarchie des objectifs

1. **Intégrité des données**
2. **Isolation multi-tenant**
3. **Prévisibilité**
4. **Disponibilité**
5. **Performance**

---

# 3. Taxonomie des pannes S2

## 3.1. Catégories principales

| Catégorie | Description |
|---------|-------------|
| Infra | DB, Broker, réseau |
| Scheduler | Ordonnancement, backlog |
| Dispatcher | Saturation, starvation |
| Worker | Crash, timeout, OOM |
| Connector | API externe |
| Quotas | Incohérence, fuite |
| Payload | Schéma invalide |
| Analytics | Lag, perte d’événements |
| Config | Secrets, env |
| Sécurité | Auth, rate-limit |

---

# 4. Failure Modes détaillés

## 4.1. MongoDB indisponible

### Symptômes
- erreurs DB timeout
- scheduler bloqué
- quotas non réservés

### Détection
- `mongo_connection_errors_total`
- healthcheck DB FAIL

### Mitigation immédiate
- passage en **read-only degraded mode**
- arrêt scheduling nouveaux jobs
- workers terminent jobs en cours

### Recovery
- redémarrage replica
- resync scheduler depuis DB
- reprise progressive

### Prévention
- replica set
- timeouts stricts
- circuit breaker DB

---

## 4.2. RabbitMQ saturé ou down

### Symptômes
- jobs bloqués en QUEUED
- dispatcher inactif

### Détection
- queue depth > seuil
- ack latency élevée

### Mitigation
- backpressure scheduler
- réduction concurrency workers

### Recovery
- redémarrage broker
- replay jobs non ack

### Prévention
- queues par tenant
- TTL sur messages
- monitoring fin

---

## 4.3. Scheduler backlog massif

### Symptômes
- latence publication élevée
- dérive horaire des posts

### Détection
- `scheduler_delay_seconds`
- backlog_size > N

### Mitigation
- throttling low-priority jobs
- pause scheduling windowed

### Recovery
- purge jobs obsolètes
- replanification intelligente

### Prévention
- time-wheel
- quotas stricts
- fairness tenant

---

## 4.4. Worker crash (OOM / segfault)

### Symptômes
- jobs bloqués EXECUTING
- heartbeat manquant

### Détection
- absence heartbeat
- `worker_crashes_total`

### Mitigation
- job marqué FAILED
- retry si possible

### Recovery
- redémarrage worker
- replay job idempotent

### Prévention
- memory limits
- single-job isolation
- payload size caps

---

## 4.5. Connector API rate-limited (429)

### Symptômes
- spikes FAILED
- retries en chaîne

### Détection
- `connector_429_total`
- error_rate plateforme

### Mitigation
- pause plateforme
- backoff global
- réduction concurrency

### Recovery
- reprise progressive
- drain retry queue

### Prévention
- rate-limit awareness
- adaptive throttling
- platform quotas internes

---

## 4.6. Connector auth invalid (401/403)

### Symptômes
- échecs permanents
- jobs DEAD

### Détection
- error_code auth
- `auth_failures_total`

### Mitigation
- stopper jobs plateforme
- notifier org

### Recovery
- refresh token
- validation secrets

### Prévention
- rotation proactive
- tests token réguliers

---

## 4.7. Quota inconsistency

### Symptômes
- quota négatif
- posts bloqués

### Détection
- invariant violation
- `quota_negative_total`

### Mitigation
- freeze org
- audit quota log

### Recovery
- compensation event
- recalcul depuis events

### Prévention
- state machine stricte (DOC-004)
- idempotence

---

## 4.8. Payload invalide

### Symptômes
- job DEAD immédiat

### Détection
- validation error
- `payload_validation_failed_total`

### Mitigation
- rejet immédiat
- feedback API clair

### Prévention
- validation upfront
- schema versioning (DOC-SC-014)

---

## 4.9. Event loss (Analytics)

### Symptômes
- dashboards incohérents

### Détection
- lag ingestion
- missing sequence

### Mitigation
- replay RawEventStore

### Prévention
- append-only
- at-least-once delivery

---

## 4.10. Secrets manquants / invalides

### Symptômes
- worker FAIL early

### Détection
- secret_access_error

### Mitigation
- stop jobs org
- alert admin

### Prévention
- manifest validation
- preflight checks

---

# 5. Failure Containment Rules (non négociables)

1. Une panne **ne doit jamais** traverser les frontières tenant.
2. Une panne **ne doit jamais** bloquer tout S2.
3. Une panne **ne doit jamais** corrompre l’état.
4. Une panne **doit toujours** être observable.

---

# 6. Graceful Degradation Modes

| Mode | Description |
|----|-------------|
| READ_ONLY | arrêt scheduling |
| PLATFORM_PAUSED | pause plateforme |
| TENANT_FROZEN | gel org |
| ANALYTICS_LAG | runtime prioritaire |

---

# 7. Alerting Strategy

## Alertes critiques (page immédiat)
- DB down
- Rabbit down
- Worker crash storm
- Quota corruption

## Alertes majeures
- backlog > seuil
- retries explosion

## Alertes mineures
- latency P95 dégradée

---

# 8. Runbooks obligatoires

Chaque failure mode doit avoir :
- description
- commandes diagnostic
- actions immédiates
- rollback
- validation post-fix

---

# 9. Postmortem Contract

Après incident :
- timeline factuelle
- root cause
- blast radius
- corrective actions
- doc update obligatoire

---

# 10. Tests de fiabilité

Tests obligatoires :
- chaos testing worker
- broker restart
- DB failover
- rate-limit simulation
- secret rotation test

---

# 11. CI/CD Reliability Gates

### 🚫 Bloquant
- code non idempotent
- absence timeouts
- absence circuit breaker
- absence metrics
- modification state machine sans doc

---

# 12. Invariants non négociables

1. Aucun incident silencieux.
2. Aucun retry infini.
3. Aucun cross-tenant impact.
4. Toute panne est observable.
5. Toute panne améliore le système.

---

# 13. Conclusion

DOC-SC-017 est le **manuel de résilience opérationnelle** de Sparkmetriq S2.

Il transforme :
- l’échec en événement maîtrisé,
- la panne en signal exploitable,
- l’incident en amélioration structurelle.

C’est un pilier SRE++ du socle SaasentialCore.

```

