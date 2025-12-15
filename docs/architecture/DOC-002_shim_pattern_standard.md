# DOC-002 — Shim Pattern Standard

*Document de Référence Technique — Sparkmetriq Architecture / API Compatibility / Migration*

```yaml
---
title: DOC-002 — Shim Pattern Standard
version: 1.0
status: Stable
category: Architecture / API Compatibility / Migration
last_updated: 2025-01-28
---
```

---

## 1. Objectif du document

Les *shims* sont un mécanisme essentiel de Sparkmetriq pour :
- assurer la **compatibilité ascendante** pendant une migration interne,
- permettre le **refactoring incrémental** sans interruption service,
- éviter les breaking changes dans l'API publique,
- permettre la transition de `api/...` vers `products/module/...`.

Ce document définit le **standard unique obligatoire** pour implémenter, maintenir et déprécier des shims au sein de Sparkmetriq.

Objectifs clés :
- éviter l'accumulation de dette technique,
- fournir un cadre homogène aux équipes backend,
- éviter que les shims deviennent une "seconde API",
- assurer une migration propre et mesurable vers l'architecture produit.

---

## 2. Périmètre

S'applique à :
- Routes FastAPI (`api/routes/*` → `products/*/api/routes/*`)
- Services (`api/services/*` → `products/*/services/*`)
- Repositories (`api/repositories/*` → `products/*/repositories/*`)
- Schémas Pydantic (compatibilité ascendante)

Hors périmètre :
- Tests (peuvent importer directement depuis `products/*`)
- Infrastructure (MongoDB, RabbitMQ, Redis)

---

## 3. Règles non négociables

### 3.1. Structure d'un shim

Un shim DOIT :
1. **Importer depuis la destination** (`products/*`)
2. **Ré-exporter** (pas de duplication de logique)
3. **Documenter** la migration prévue
4. **Déprécier** progressivement

#### ✔️ Exemple correct

```python
# api/routes/scheduler.py (SHIM)
"""
Shim de routing pour le scheduler Sparkmetriq/Sparkpusher.

Rôle :
- Exposer les routes S2 (Sparkpusher) sous /api/scheduler/*
- Préparer le futur pour des routes Sparkmetriq spécifiques au scheduler.

Architecture :
- products.sparkpusher.api.routes.scheduler : routes S2 officielles (Content Studio)
- products.sparkmetriq.api.routes.scheduler : routes Sparkmetriq (placeholder pour l'instant)
- Ce shim monte les deux routers avec les bons préfixes
- api/main.py ajoute le préfixe /api → chemin final /api/scheduler/*
"""

from fastapi import APIRouter
from products.sparkpusher.api.routes.scheduler import router as sparkpusher_scheduler_router
from products.sparkmetriq.api.routes.scheduler import router as sparkmetriq_scheduler_router

router = APIRouter()

# S2 (Sparkpusher) – routes officielles de scheduler utilisées en prod
router.include_router(
    sparkpusher_scheduler_router,
    prefix="/scheduler",
    tags=["scheduler-s2"],
)

# Sparkmetriq – pour l'instant seulement un stub propre
router.include_router(
    sparkmetriq_scheduler_router,
    prefix="/scheduler/sparkmetriq",
    tags=["scheduler-sparkmetriq"],
)
```

#### ❌ Exemple incorrect

```python
# ❌ INTERDIT : Duplication de logique
def schedule_post(payload):
    # Logique dupliquée au lieu de déléguer
    quotas = QuotasService()  # ❌ Instanciation directe
    # ... logique métier ...
```

### 3.2. Délégation pure

Un shim NE DOIT JAMAIS :
- contenir de logique métier,
- instancier des services directement,
- accéder à la DB directement,
- redéfinir des schémas Pydantic.

### 3.3. Documentation obligatoire

Chaque shim DOIT contenir :
- un docstring expliquant son rôle,
- la destination finale (`products/*/...`),
- la date prévue de dépréciation (si applicable).

---

## 4. Matrice Shim → Destination

| Shim actuel                    | Destination finale                    | Statut      |
| ------------------------------ | ------------------------------------- | ----------- |
| `api/routes/scheduler.py`      | `products/sparkpusher/api/routes/...` | ✅ Migré     |
| `api/services/scheduler/*`     | `products/*/services/scheduler/*`     | 🔄 En cours |
| `api/services/quotas_service`  | `products/sparkpusher/services/...`   | ✅ Migré     |

---

## 5. Checklist de conformité shim

Avant chaque PR contenant un shim :

- [ ] Le shim importe depuis `products/*` (pas de duplication)
- [ ] Le shim délègue via `include_router` ou ré-export
- [ ] Aucune logique métier dans le shim
- [ ] Docstring explique le rôle et la destination
- [ ] Tests passent via le shim ET directement via `products/*`
- [ ] Aucun service instancié directement dans le shim

---

## 6. Dépréciation progressive

### Phase 1 : Migration
- Le shim existe et délègue
- Les clients utilisent l'ancien chemin (`api/routes/...`)
- Tests vérifient les deux chemins

### Phase 2 : Dépréciation
- Ajouter un header `X-API-Deprecated: true`
- Logger un warning
- Documenter la nouvelle route

### Phase 3 : Suppression
- Après N versions, supprimer le shim
- Mettre à jour la documentation

---

## 7. Exemples bon/mauvais

### ✅ Bon : Shim de route

```python
# api/routes/scheduler.py
from products.sparkpusher.api.routes.scheduler import router as s2_router

router = APIRouter()
router.include_router(s2_router, prefix="/scheduler")
```

### ❌ Mauvais : Shim avec logique

```python
# ❌ INTERDIT
@router.post("/schedule")
def schedule(payload):
    # Logique métier dupliquée
    service = QuotasService()  # ❌
    return service.check(payload)
```

---

## 8. Conclusion

Les shims sont un outil de migration, pas une architecture permanente.

**Tout shim doit avoir une date de dépréciation prévue.**
