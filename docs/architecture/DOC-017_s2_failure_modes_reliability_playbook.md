Voici **DOC-017 — S2 Failure Modes & Reliability Playbook**, version longue (15–22 pages), le document SRE le plus stratégique pour Sparkmetriq S2.
Il définit :

* les *types de pannes* possibles,
* les *mécanismes de récupération (fault recovery)*,
* les *SLI/SLO associés*,
* les *runbooks opérationnels*,
* les *contraintes d’architecture liées à la fiabilité*,
* les *tests de résilience obligatoires*,
* le *chaos engineering minimum viable*,
* et les *procédures d'incident*.

À placer dans :

```
docs/architecture/DOC-017_s2_failure_modes_reliability_playbook.md
```

---

# 📘 **DOC-017 — S2 Failure Modes & Reliability Playbook**

*Document SRE++ — Sparkmetriq S2 / Fiabilité / Résilience / Gestion des Pannes*

```markdown
---
title: DOC-017 — S2 Failure Modes & Reliability Playbook
version: 1.0
status: Stable
category: SRE / Reliability / Incident Response / Distributed Systems
last_updated: 2025-02-10
---
```

---

# # **1. Objectif du document**

Sparkmetriq S2 est un système **temps-réel différé** :
il doit publier du contenu à la seconde près, pour des milliers d’agences, sur des plateformes externes imprédictibles.

Ce document définit :

* les pannes possibles (catalogue officiel),
* les mécanismes de récupération attendus (RTOS + distribué),
* les bonnes pratiques SRE (inspirées Google SRE, DDIA),
* les runbooks pour les équipes,
* les tests de résilience obligatoires,
* la politique de disponibilité.

Ce document est **normatif** et s’appuie sur :

* DOC-013 (Scheduler/Dispatcher Deep Spec)
* DOC-015 (Worker Execution Model)
* DOC-012 (Connectors Contract)
* DOC-016 (Analytics & Reporting)
* DOC-004/DOC-005 (Quotas & Idempotence)

---

# # **2. Catalogue officiel des modes de panne**

Les pannes sont classées en 4 familles :

```
A. Internal Failures
B. External Failures (plateformes sociales)
C. Infrastructure Failures (Mongo, RabbitMQ, network)
D. Human / Operational Failures
```

---

# # **3. A — INTERNAL FAILURES**

## A1 — Scheduler Failure

### Symptômes :

* jobs restent en `READY`
* batchs non produits
* pas de logs scheduler

### Causes :

* bug logique
* deadlock
* surcharge CPU

### Recovery attendu :

✔ redémarrage automatique (systemd)
✔ reprise instantanée via state machine
✔ scheduler idempotent
✔ jobs READY replanifiés
✔ jamais de perte de job

---

## A2 — Dispatcher Failure

### Symptômes :

* backlog READY monte
* RabbitMQ reste vide
* aucun job ne part

### Recovery attendu :

✔ dispatcher restart → reprise automatique
✔ idempotence empêche double push
✔ détection directe via métriques

---

## A3 — Worker Crash

### Symptômes :

* message non acké → retourne en queue
* logs interrompus
* latence augmente

### Recovery attendu :

✔ worker restart
✔ message reprocessing (RabbitMQ)
✔ idempotence → pas de double effet
✔ quotas non impactés

---

## A4 — Idempotence Registry Corruption

### Symptômes :

* double publication plateforme
* worker rejoue un job déjà effectué

### Recovery attendu :

✔ correction automatique via pattern "last write wins"
✔ fallback sur hash contenu
✔ audit logs

---

## A5 — Quotas incohérents

### Symptômes :

* quotas jamais libérés
* quotas consommés deux fois
* jobs BLOCKED

### Recovery attendu :

✔ resynchronisation during scheduler_run
✔ état RELEASED recalculé via events
✔ idempotence du comptage

---

# # **4. B — EXTERNAL FAILURES (Plateformes sociales)**

## B1 — Instagram/TikTok/Threads Rate Limits

### Symptômes :

* 429
* réduction brutale du débit
* worker retries

### Recovery attendu :

✔ backoff exponentiel (DOC-012)
✔ bucket tenant-level
✔ metrics `connector_rate_limit_hits_total`

---

## B2 — API Downtime

### Symptômes :

* 5xx répétés
* timeouts

### Recovery :

✔ retry limité
✔ fail fast après 3 tentatives
✔ requeue automatique
✔ quotas non consommés

---

## B3 — Token Expiration

### Symptômes :

* OAuth error code 190 (Meta)
* TikTok invalid tokens

### Recovery :

✔ fail immediate
✔ quotas → RELEASED
✔ push notification admin panel
✔ aucun retry

---

# # **5. C — INFRASTRUCTURE FAILURES**

---

## C1 — MongoDB Down

### Symptômes :

* scheduler incapable d’écrire
* worker incapable de valider état final

### Recovery :

✔ retry 30s window
✔ fallback to safe mode
✔ 0 data loss garanti pour jobs en cours
✔ events stockés temporairement in-memory
✔ redémarrage automatique

---

## C2 — RabbitMQ Down

### Symptômes :

* aucun dispatch possible
* workers idle

### Recovery :

✔ circuit breaker actif
✔ dispatcher en pause
✔ scheduler continue de préparer les batches
✔ redémarrage → reprise instantanée

---

## C3 — Network Partition (partial split-brain)

### Symptômes :

* certains workers isolés
* impossibilité d’atteindre connecteurs

### Recovery :

✔ worker isolation automatique
✔ requeue jobs vers workers disponibles
✔ partition healing automatique

---

# # **6. D — HUMAN / OPERATIONAL FAILURES**

## D1 — Mauvaise configuration API

✔ detection dans CI
✔ UI validation
✔ logs d’erreur explicites

## D2 — Mauvaise configuration worker

✔ validation au démarrage
✔ erreurs bloquantes

## D3 — Suppression involontaire de contenu

✔ soft delete
✔ restore via admin panel

---

# # **7. S2 Reliability Model (SRE++)**

### SLI (Service Level Indicators)

| SLI                  | Description                   |
| -------------------- | ----------------------------- |
| publish_success_rate | pourcentage de jobs complétés |
| end_to_end_latency   | temps total job → plateforme  |
| retry_rate           | proportion de retries         |
| error_rate           | erreurs par plateforme        |
| scheduler_latency    | délai READY → ENQUEUED        |
| worker_latency       | durée worker                  |

---

### SLO (Service Level Objectives)

| SLO                        | Cible              |
| -------------------------- | ------------------ |
| Publish Success ≥ 98%      | S2 production      |
| Worker Latency P95 < 8s    | opti               |
| Scheduler Latency < 3s     | scaling horizontal |
| Retry Rate < 5%            | normal             |
| Platform Error Budget < 2% | externe            |

---

# # **8. Failure Detection Mechanisms**

Sparkmetriq doit détecter automatiquement :

* anomalies de latence
* absence de logs
* absence d’événements scheduler
* absence d’ACK RabbitMQ
* augmentation des retries
* erreurs 429/500 excessives
* worker stuck > 10s
* quota anomalies
* flux analytics biaisé

---

# # **9. Recovery Procedures (Playbook)**

## 9.1. Worker freeze

→ Kill worker process
→ message retourné à queue
→ restart process
→ idempotence → safe

---

## 9.2. Dispatcher stuck

→ restart dispatcher service
→ vérifier metrics
→ pas de requeue

---

## 9.3. Scheduler blackout

→ restart scheduler
→ effectuer "state reconciliation"

---

## 9.4. RabbitMQ crashed

→ restart
→ dispatcher synchronise
→ workers drain jobs

---

## 9.5. MongoDB inconsistent

→ failover to secondary
→ replay des events depuis logs
→ réparer via audit

---

## 9.6. Platform rate limits

→ réduire périodicité scheduler
→ worker impose hard throttle
→ limiter backpressure

---

# # **10. Chaos Engineering (Minimum Contract)**

Tests hebdomadaires obligatoires :

* crash scheduler
* crash worker
* crash dispatcher
* kill MongoDB for 20s
* kill RabbitMQ for 10s
* connexion externe retardée de 2s
* 50% erreurs 500 simulées connecteurs

Le système doit :

* ne rien perdre
* ne pas doubler les publications
* rattraper automatiquement

---

# # **11. Tests obligatoires (CI & E2E)**

## Unitaire

* simulate worker crash
* simulate invalid token
* simulate scheduler state drift

## Intégration

* simulate RabbitMQ outage
* simulate MongoDB partial failure
* simulate HTTP throttling

## E2E

* 500 jobs en rafale sous défaillance externe
* 100 jobs sous latence réseau x10
* 200 jobs sous intermittence RabbitMQ

---

# # **12. CI/CD Reliability Compliance**

### 🚫 Bloquant

* absence de tests failure modes
* absence de retry spec
* absence de state reconciliation
* worker sans watchdog
* scheduler sans auto-recovery
* double publication possible
* log non structuré → impossible à tracer

### ⚠ warning

* observabilité incomplète
* absence de chaos tests

---

# # **13. Tableau final des modes de panne & stratégies**

| Failure          | Impact             | Expected Strategy        | Guarantees                 |
| ---------------- | ------------------ | ------------------------ | -------------------------- |
| Scheduler crash  | retards            | restart + reconciliation | no job lost                |
| Dispatcher crash | aucune publication | restart                  | no double enqueue          |
| Worker crash     | job ré-enqueue     | restart                  | idempotence ensures safety |
| Connecteur 500   | retry              | backoff                  | no duplicate publish       |
| Rate limits      | >latence           | throttle                 | no quota corruption        |
| Mongo down       | backlog            | retry                    | no data loss               |
| RabbitMQ down    | no dispatch        | circuit breaker          | no overwrite               |

---

# # **14. Checklist finale SRE++**

* [ ] système résilient aux pannes internes
* [ ] système résilient aux pannes externes
* [ ] mécanismes auto-recovery présents
* [ ] aucun risque de double publication
* [ ] aucun risque de perte de job
* [ ] idempotence au cœur de l’architecture
* [ ] observabilité complète
* [ ] dashboards opérationnels OK
* [ ] chaos tests automatisés
* [ ] CI/CD bloque toute régression de fiabilité

---

# # **15. Conclusion**

DOC-017 est l’élément ultime du pilier SRE++ de Sparkmetriq S2.
Il garantit une **fiabilité de niveau industriel**, adaptée :

* au scale multi-agences,
* aux défaillances externes imprévisibles,
* aux pannes internes,
* aux exigences de qualité d’une application SaaS critique.

> **Toute PR qui diminue la fiabilité ou viole DOC-017 doit être bloquée immédiatement.**

---
