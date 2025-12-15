# DOC-005 — Retry Policy & Idempotency

*Document Technique de Référence — Sparkmetriq Architecture / Reliability / SRE++*

```yaml
---
title: DOC-005 — Retry Policy & Idempotency
version: 1.0
status: Stable
category: Architecture / Reliability / Distributed Systems / SRE++
last_updated: 2025-01-29
---
```

---

## 1. Objectif du document

Ce document définit les **politiques de retry et l'idempotence** obligatoires dans Sparkmetriq.

Objectifs :
- éviter les **retry multiples ou infinis**,
- empêcher les **appels doublés** aux plateformes externes → double publication,
- garantir la **consommation unique** de quotas,
- assurer un comportement **déterministe** même en cas de pannes.

---

## 2. Règles non négociables

### 2.1. Retry Policy

#### Configuration standard

```python
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = [60, 300, 900]  # 1min, 5min, 15min
```

#### Comportement

1. **Tentative 1** : Immédiate
2. **Tentative 2** : Après 60s (backoff exponentiel)
3. **Tentative 3** : Après 300s
4. **Échec définitif** : Après 3 tentatives → statut `FAILED`

### 2.2. Idempotence

**TOUTE opération externe DOIT être idempotente.**

#### Exemple : Publication sur plateforme

```python
async def publish_to_platform(payload, platform):
    # ✅ Utiliser un idempotency_key
    idempotency_key = f"{payload.job_id}_{platform}"
    
    # Vérifier si déjà publié
    existing = await check_existing_publication(idempotency_key)
    if existing:
        return existing  # ✅ Retourner le résultat existant
    
    # Publication
    result = await platform_api.publish(payload, idempotency_key=idempotency_key)
    await store_publication(idempotency_key, result)
    return result
```

### 2.3. Quotas idempotents

Les opérations de quotas DOIVENT être idempotentes :

```python
# ✅ Utiliser des opérations atomiques MongoDB
await collection.update_one(
    {"org_id": org_id},
    {"$inc": {"usage.scheduled_posts": 1}},  # ✅ Atomique
)
```

---

## 3. Checklist Retry & Idempotency

- [ ] MAX_ATTEMPTS = 3 (configurable mais par défaut 3)
- [ ] Backoff exponentiel entre tentatives
- [ ] Statut `FAILED` après échec définitif
- [ ] `completed_at` défini pour SUCCESS et FAILED
- [ ] Idempotency keys pour toutes les opérations externes
- [ ] Vérification avant publication (éviter doublons)
- [ ] Opérations quotas atomiques (`$inc`, `$set`)

---

## 4. Exemples bon/mauvais

### ✅ Bon : Retry avec idempotence

```python
async def run_scheduled_job(job_id, executor_callback):
    job = await get_job_by_id(job_id)
    
    # ✅ Vérifier idempotence
    if job["status"] == "SUCCESS":
        return job["result"]  # Déjà exécuté
    
    # Exécution avec retry
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = await executor_callback(job)
            # ✅ Marquer comme SUCCESS (idempotent)
            await update_job(job_id, {"status": "SUCCESS", "result": result})
            return result
        except Exception as e:
            if attempt == MAX_ATTEMPTS:
                await update_job(job_id, {"status": "FAILED", "error": str(e)})
                raise
            await asyncio.sleep(BACKOFF_SECONDS[attempt - 1])
```

### ❌ Mauvais : Retry sans idempotence

```python
# ❌ INTERDIT : Pas de vérification, risque de double exécution
async def run_job(job_id):
    for attempt in range(10):  # ❌ Trop de tentatives
        result = await publish()  # ❌ Pas d'idempotency key
        return result
```

---

## 5. Conclusion

**Toute opération externe sans idempotence = risque de double publication.**
