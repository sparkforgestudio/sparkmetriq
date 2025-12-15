# DOC-003 — API Schema & Response Contract

*Document Technique de Référence — Sparkmetriq API Architecture / SRE++*

```yaml
---
title: DOC-003 — API Schema & Response Contract
version: 1.0
status: Stable
category: Architecture / API / Serialization / SRE++
last_updated: 2025-01-28
---
```

---

## 1. Objectif du document

Ce document définit le **contrat d'API** unique et obligatoire pour Sparkmetriq.

Objectifs :
- garantir une API stable, cohérente, prédictible, documentée ;
- éviter les erreurs communes de FastAPI (response_model implicite, types internes exposés, enums non sérialisables, datetime incorrectes, etc.) ;
- assurer la compatibilité entre modules (S2, S3, S4) ;
- permettre des tests E2E reproductibles ;
- fournir une base solide pour les intégrations futures (webhooks, partenaires SaaS, agences).

Ce contrat s'applique à **toutes les routes**, internes comme publiques.

---

## 2. Règles non négociables

### 2.1. `response_model` obligatoire

**TOUTE route DOIT avoir un `response_model` explicite.**

#### ✔️ Correct

```python
from api.schemas.scheduler import SchedulePostResponse

@router.post(
    "/posts/schedule",
    response_model=SchedulePostResponse,  # ✅ Explicite
    status_code=status.HTTP_201_CREATED,
)
async def schedule_post(
    payload: UnifiedPostPayload,
    bridge: SaasentialCoreBridge = Depends(get_saasential_bridge),
) -> SchedulePostResponse:
    # ...
    return SchedulePostResponse(job_id=job_id, ...)
```

#### ❌ Incorrect

```python
# ❌ INTERDIT : Pas de response_model
@router.post("/posts/schedule")
async def schedule_post(payload):
    return {"job_id": "123"}  # ❌ Dict implicite
```

### 2.2. Schémas Pydantic v2

Tous les schémas DOIVENT utiliser Pydantic v2 :

```python
from pydantic import BaseModel, ConfigDict

class SchedulePostResponse(BaseModel):
    job_id: str
    org_id: str
    status: JobStatus
    scheduled_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,  # Ancien orm_mode
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
    )
```

### 2.3. Types datetime

Tous les `datetime` DOIVENT être timezone-aware (UTC) :

```python
from datetime import datetime, timezone

scheduled_at: datetime = datetime.now(timezone.utc)  # ✅
```

### 2.4. Enums sérialisables

Les enums DOIVENT être sérialisables en JSON :

```python
from enum import Enum

class JobStatus(str, Enum):  # ✅ Hérite de str
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
```

---

## 3. Checklist API Contract

Avant chaque PR :

- [ ] Toutes les routes ont un `response_model` explicite
- [ ] Tous les schémas utilisent Pydantic v2 (`model_config = ConfigDict(...)`)
- [ ] Tous les `datetime` sont timezone-aware (UTC)
- [ ] Tous les enums héritent de `str`
- [ ] Aucun type interne (ObjectId, etc.) exposé dans les réponses
- [ ] Documentation OpenAPI générée correctement

---

## 4. Exemples bon/mauvais

### ✅ Bon : Route complète

```python
@router.get(
    "/jobs/{job_id}",
    response_model=JobDetails,
    summary="Get job details",
    description="Retrieve detailed information about a scheduled job",
)
async def get_job_details(
    job_id: str,
    bridge: SaasentialCoreBridge = Depends(get_saasential_bridge),
) -> JobDetails:
    job = await bridge.get_job_by_id(job_id)
    return JobDetails(**job)
```

### ❌ Mauvais : Route sans contrat

```python
# ❌ INTERDIT
@router.get("/jobs/{job_id}")
async def get_job_details(job_id: str):
    job = await db["scheduled_tasks"].find_one({"_id": ObjectId(job_id)})
    return job  # ❌ Expose ObjectId, pas de response_model
```

---

## 5. Conclusion

**Toute route sans `response_model` = PR bloquée automatiquement.**
