Voici **DOC-007 — Performance & Scalability Guidelines (Version longue, 6–12 pages)**, le document de référence pour garantir la performance, la scalabilité, la faible latence et la capacité de montée en charge de **Sparkmetriq S2/S3/S4**.

Il suit les principes de :
**DDIA (Kleppmann) — High Performance Python — Google SRE — Distributed Systems best practices**,
et il est 100% adapté :

* à FastAPI,
* aux workers Celery,
* à RabbitMQ,
* à MongoDB,
* à Scheduler/Dispatcher,
* à l’architecture multi-nœuds Sparkmetriq.

Ce document est destiné à être placé dans :

```
docs/architecture/DOC-007_performance_scalability_guidelines.md
```

---

# 📘 **DOC-007 — Performance & Scalability Guidelines (Version longue)**

*Document Technique de Référence — Sparkmetriq Engineering / SRE++ / Scalability Architecture*

```markdown
---
title: DOC-007 — Performance & Scalability Guidelines
version: 1.0
status: Stable
category: Architecture / Performance / Scalability / SRE++
last_updated: 2025-01-31
---
```

---

# # **1. Objectif du document**

Ce document définit **les standards de performance et scalabilité** obligatoires pour Sparkmetriq :

* faible latence API,
* haute disponibilité,
* réduction du CPU & mémoire,
* optimisation réseau,
* montée en charge horizontale (workers, nodes, queues),
* performance MongoDB,
* performance RabbitMQ,
* performance Python (GIL, asyncio, threads, multiprocessing),
* performance connecteurs (API externes),
* prévention du backpressure & saturation.

Objectif :

> Sparkmetriq doit supporter des milliers de publications par minute, avec un temps de réponse stable, des queues fiables, et des workers résilients.

---

# # **2. Périmètre**

S’applique à :

* API FastAPI
* Scheduler
* Dispatcher
* Workers Celery
* Connecteurs
* MongoDB
* RabbitMQ
* Cache layer (Redis futur)
* Observability pour tuning

---

# # **3. Principes fondamentaux (DDIA / SRE++)**

## ✔ **3.1. Scale horizontally, not vertically**

Toute architecture Sparkmetriq doit préférer :

```
+10 workers Celery  → plutôt qu’un worker plus puissant
+3 nœuds API        → plutôt qu'un seul serveur plus gros
```

## ✔ **3.2. Stateless by design**

Permet :

* load balancing,
* rotation dynamique des workers,
* redémarrage sans perte d’état.

## ✔ **3.3. Backpressure awareness**

Chaque service doit :

* détecter saturation,
* ralentir proprement,
* éviter cascade failures.

## ✔ **3.4. Async everywhere**

Toute I/O (DB, HTTP, broker) doit être **non bloquante**.

## ✔ **3.5. Idempotence → prérequis performance**

Sans idempotence (DOC-005), aucun retry intelligent → saturation assurée.

---

# # **4. Performance API (FastAPI)**

## **4.1. Uvicorn + UVLoop obligatoire**

```bash
uvicorn api.main:app --workers 4 --loop uvloop --http httptools
```

Améliorations :

* +30% throughput
* -20% latence

---

## **4.2. Aucun appel bloquant dans les endpoints**

Interdit :

```python
time.sleep(3)
db.find_one()  # sync blocking
```

Correct :

```python
await asyncio.sleep(3)
await collection.find_one(...)
```

---

## **4.3. Taille des réponses maîtrisée**

* compresser JSON
* ne pas renvoyer données inutiles
* pagination obligatoire

---

## **4.4. FastAPI Middleware Tuning**

Utilisation d’un middleware léger :

* correlation_id
* observability
* rate limiting (futur)

Éviter middleware lourds côté request.

---

# # **5. Performance Scheduler / Dispatcher**

## **5.1. Scheduler est CPU-light**

Il doit :

* uniquement valider → normaliser → insérer un job
* ne jamais exécuter de logique métier lourde
* ne jamais publier lui-même

---

## **5.2. Dispatcher doit être I/O-optimized**

Le dispatcher :

* pousse les jobs en queue RabbitMQ,
* doit être **non bloquant**,
* doit être idempotent.

---

## **5.3. Prefetch & Acknowledgment control**

Pour RabbitMQ :

```
prefetch_count = 1
```

Cela évite qu’un worker reçoive plusieurs jobs qu’il ne peut traiter assez vite.

---

# # **6. Performance Celery Workers**

## **6.1. Nombre optimal de workers**

Règle :

```
workers = CPU cores × 2
threads = 1  (éviter pooling Python)
```

Exemple serveur 8 vCPU :

```
16 workers Celery
```

---

## **6.2. Timeout strict**

```
task_soft_time_limit = 20
task_time_limit = 30
```

Empêche les tasks zombies.

---

## **6.3. Disable useless Celery features**

* disable result backend (use Mongo only for idempotence)
* no retry unless explicitly needed

---

## **6.4. Avoid heavy Python objects**

FastAPI/Celery doivent éviter :

* pandas
* numpy lourds
* pickles volumineux
* objets Python énormes

---

# # **7. MongoDB Performance Guidelines**

## **7.1. Indexation obligatoire**

| Collection    | Index                    |
| ------------- | ------------------------ |
| `jobs`        | `{org_id, scheduled_at}` |
| `quotas`      | `{org_id, date}`         |
| `idempotence` | `{idempotency_key}`      |

---

## **7.2. Projections**

Toujours utiliser :

```python
collection.find(..., {"_id": 0, "field": 1})
```

Améliore perf ×5.

---

## **7.3. Sharding (future)**

Préparer le design : clé de sharding = `org_id`.

---

## **7.4. Write concern**

For scheduler :

```
w=1  (rapide)
```

For idempotence:

```
w=majority  (sécurité)
```

---

# # **8. RabbitMQ Performance Guidelines**

## **8.1. Durable queues**

Toutes les queues critiques doivent être :

```
durable=True
delivery_mode=2
```

---

## **8.2. Keeps queue length < 10 000**

Au-delà → consumer saturation.

---

## **8.3. HA (High Availability policy)**

```
ha-mode = all
```

---

# # **9. Cache Layer (Redis) — futur S3/S4**

Use cases :

* API rate limiting
* caching des profils d’agences
* caching des configurations connecteurs
* éviter surcharge Mongo

---

# # **10. Backpressure Strategy**

Chaque composant doit détecter :

* queue RabbitMQ > threshold
* Mongo slow queries
* worker saturation
* external 429/5xx flood

Actions :

* ralentir scheduler
* augmenter delay retry
* couper connecteur temporairement
* signaler incident SLO (DOC-006)

---

# # **11. Memory Management (Python)**

## **11.1. Éviter les gros objets**

Chaque worker doit :

* libérer explicitement les buffers
* éviter les dicts immenses
* éviter deepcopy inutiles

---

## **11.2. Limiter les imports lourds**

Interdit dans un worker :

```python
import torch
import numpy
import pandas
```

---

## **11.3. GIL Awareness**

Le Python GIL empêche le full parallelism CPU.
Solutions :

* multiprocessing (pour tâches CPU rares)
* async (pour I/O 90% du temps → ton cas dans S2)

---

# # **12. Latency Budgets**

Budget de latence S2 :

| Composant                     | Max latency |
| ----------------------------- | ----------- |
| API receive → schedule        | 40 ms       |
| Scheduler → queue push        | 30 ms       |
| Worker start → connector call | 100 ms      |
| Connector response            | 200–700 ms  |
| Total pipeline                | < 1.2s      |

---

# # **13. Performance Tests Requirements**

## **13.1. Load testing API**

Simuler :

* 500 req/s
* 50 organisations simultanées
* payloads variés

Objectif :
latence P95 < **80 ms**.

---

## **13.2. Stress testing Workers**

Simuler :

* 5 000 jobs planifiés en rafale
* 200 workers
* idempotence testée

Résultat souhaité :
100% jobs exécutés sans doublons.

---

## **13.3. Spike testing**

Simuler :

* 10× charge normale
* récupération en < 60 sec

---

# # **14. CI/CD — Performance Compliance**

CI doit vérifier :

### 🚫 Bloquant :

* allocations mémoire sans libération dans workers
* absence d’indice Mongo
* code synchrone bloquant dans endpoints
* appels connecteurs dans un scheduler
* absence de timeouts
* data volumes excessive dans logs/API

### ⚠ Warning :

* absence tests de charge
* absence projections Mongo

---

# # **15. Checklist finale SRE++ Performance**

* [ ] endpoints 100% async
* [ ] Mongo avec indices corrects
* [ ] Workers dimensionnés correctement (CPU×2)
* [ ] idempotence garantie
* [ ] backoff+jitter implémentés
* [ ] aucune boucle Python bloquante
* [ ] aucun gros import dans workers
* [ ] queue RabbitMQ sous contrôle
* [ ] dashboards Grafana complets
* [ ] alerting configuré

---

# # **16. Conclusion**

DOC-007 fournit le **cadre formel** garantissant une plateforme Sparkmetriq :

* scalable,
* stable,
* rapide,
* résistante aux pannes,
* efficace en ressources,
* compatible croissance commerciale,
* adaptée aux charges massives.

C’est un document **obligatoire**, dont toute fonctionnalité doit respecter les règles avant d’être mergée.

> Sparkmetriq devient une plateforme “industrial grade” dès que DOC-007 est appliqué partout.

---
