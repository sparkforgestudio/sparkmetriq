# DOC-004 — Quotas State Machine

*Document Technique de Référence – Sparkmetriq S2 / Quotas Engine / SRE++*

```yaml
---
title: DOC-004 — Quotas State Machine
version: 1.0
status: Stable
category: Architecture / Business Rules / S2 Engine
last_updated: 2025-01-29
---
```

---

## 1. Objectif du document

Ce document définit la **machine à états (State Machine)** responsable de la gestion des quotas dans Sparkmetriq S2.

Objectifs :
- assurer la cohérence **globale** du modèle de consommation,
- empêcher les surconsommations accidentelles,
- garantir la compatibilité avec le scheduler, dispatcher, les connecteurs,
- fournir un mécanisme robuste face aux **retries**,
- permettre un fonctionnement **idempotent**.

---

## 2. États des quotas

### 2.1. États principaux

```
INITIAL → SCHEDULED → PUBLISHING → PUBLISHED
                ↓
            FAILED
```

### 2.2. Transitions

| État source | Événement              | État cible | Action quota                    |
| ----------- | ---------------------- | ---------- | ------------------------------- |
| INITIAL     | `schedule_post()`      | SCHEDULED  | `scheduled_posts++`             |
| SCHEDULED   | `run_job()`            | PUBLISHING | (aucun changement)              |
| PUBLISHING  | `on_success()`         | PUBLISHED  | `scheduled_posts--`, `published_today++` |
| PUBLISHING  | `on_failure()`         | FAILED     | `scheduled_posts--`             |
| SCHEDULED   | `cancel_job()`         | CANCELLED  | `scheduled_posts--`              |

---

## 3. Règles contractuelles

### 3.1. Vérification avant scheduling

**OBLIGATOIRE** : Vérifier les quotas AVANT de créer un job.

```python
async def schedule_post(payload, bridge):
    # ✅ Vérification AVANT création
    await bridge.check_quotas_before_scheduling(payload)
    
    # Création du job
    job_id = await bridge.create_scheduled_job(...)
    
    # Incrément scheduled_posts
    await bridge.increment_scheduled_posts(org_id)
```

### 3.2. Mise à jour après exécution

**OBLIGATOIRE** : Mettre à jour les quotas dans le callback `on_success` :

```python
async def on_success_callback(org_id: str, job_data: Dict):
    # ✅ Décrément scheduled, incrément published
    await bridge.decrement_scheduled_on_success(org_id)
    await bridge.increment_published_today(org_id)
```

### 3.3. Idempotence

Les opérations de quotas DOIVENT être idempotentes :

- Si `increment_scheduled_posts` est appelé deux fois pour le même job → une seule consommation
- Utiliser des opérations atomiques MongoDB (`$inc`)

---

## 4. Checklist Quotas

- [ ] Vérification des quotas AVANT création de job
- [ ] Incrément `scheduled_posts` APRÈS création réussie
- [ ] Décrément `scheduled_posts` dans `on_success` ou `on_failure`
- [ ] Incrément `published_today` dans `on_success` uniquement
- [ ] Reset quotidien de `published_today` (vérifié dans `reset_daily_usage_if_needed`)
- [ ] Opérations atomiques MongoDB (`$inc`, `$set`)

---

## 5. Conclusion

**Toute violation des transitions de quotas = risque de surconsommation ou de bugs silencieux.**
