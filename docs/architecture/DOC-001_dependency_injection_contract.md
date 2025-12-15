# DOC-001 — Dependency Injection Contract

*Document de Référence Technique — Sparkmetriq Architecture / SRE++*

```yaml
---
title: DOC-001 — Dependency Injection Contract
version: 1.0
status: Stable
category: Architecture / SRE++
last_updated: 2025-01-28
---
```

---

## 1. Objectif du document

Le présent document définit **le contrat d'injection de dépendances (DI)** obligatoire dans Sparkmetriq.

Objectifs :
- garantir une architecture **cohérente, testable, stable** ;
- éliminer les bugs liés aux fallbacks (`localhost:27017`, env globals, imports circulaires) ;
- homogénéiser l'accès aux services (Quotas, Scheduler, Dispatcher, Connecteurs, etc.) ;
- éviter les divergences **test/runtime** ;
- fournir une base solide pour les modules S2, S3 et S4 ;
- permettre une intégration propre dans la CI (Architecture Compliance).

Ce document est **normatif** :
➡️ Tout code violant les règles ci-dessous est **refusé en revue et bloqué en CI**.

---

## 2. Périmètre

Ce contrat s'applique à :
- API FastAPI (`api/routes/*`)
- Services métier (`products/*/services/*`)
- Repositories
- Celery worker tasks
- Scheduler / Dispatcher
- Connecteurs (TikTok, Instagram, Threads, etc.)
- Tests unitaires & E2E

Hors périmètre :
- infrastructure pure (MongoDB, RabbitMQ, Redis)
- frontend Next.js (admin panel)

---

## 3. Principes fondamentaux

### 3.1. Single Source of Truth (DB + Settings + Services)

Sparkmetriq doit garantir :

| Élément  | Source unique          | Usage                             |
| -------- | ---------------------- | --------------------------------- |
| DB       | `get_core_db()`        | Tous les services et repositories |
| Settings | `get_settings()`       | Configuration runtime             |
| Services | `SaasentialCoreBridge` | Accès via routes & workers        |

Interdictions :
- ❌ créer `MongoClient()` dans un service
- ❌ lire `os.environ` dans un service
- ❌ instancier `QuotasService()` directement
- ❌ coder une URL DB en dur

### 3.2. Inversion de contrôle

La route NE construit JAMAIS les services.
Elle reçoit un **bridge** qui donne accès à tous les services construits proprement.

### 3.3. Isolation et testabilité

Aucune dépendance globale non contrôlée :
- ❌ pas de singletons indésirables
- ❌ pas de variables globales modulaires
- ❌ pas d'instances cachées
- ✔️ tout doit être injectable

---

## 4. Architecture DI — Diagramme explicatif

```
Route → Depends(get_saasential_bridge) → SaasentialCoreBridge(db) → Services → Repositories → DB
```

---

## 5. Règles non négociables

### 5.1. Routes FastAPI

#### ✔️ Obligatoire

```python
from fastapi import Depends
from api.deps import get_saasential_bridge
from api.services.core.saasential_bridge import SaasentialCoreBridge

@router.post("/s2/posts/schedule", response_model=ScheduleResult)
async def schedule_post(
    payload: UnifiedPostPayload,
    bridge: SaasentialCoreBridge = Depends(get_saasential_bridge),
):
    quotas_service = bridge.get_quotas_service()
    return await quotas_service.check_quotas_before_scheduling(payload)
```

#### ❌ Interdit

```python
# Mauvais : DI contournée, DB non injectée, tests impossibles
def schedule_post(payload):
    quotas = QuotasService()  # ❌ Instanciation directe
    return quotas.schedule(payload)
```

### 5.2. Services

- Ils reçoivent leurs dépendances via leur **constructeur** (et rien d'autre).
- Aucun accès direct à `os.environ`.
- Aucun client DB construit localement.

Exemple :

```python
class QuotasService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["org_quotas"]
```

Interdit :

```python
# Anti-pattern
client = MongoClient("mongodb://localhost:27017")  # ❌ Hardcodé
```

### 5.3. Bridge (SaasentialCoreBridge)

Rôle :
- instancier DB + repositories + services,
- centraliser toutes les dépendances,
- être injecté dans les routes et les worker tasks.

Le bridge est construit avec une DB injectée :

```python
def get_saasential_bridge(
    db: AsyncIOMotorDatabase = Depends(get_core_db),
) -> SaasentialCoreBridge:
    return SaasentialCoreBridge(db=db)
```

### 5.4. Workers Celery & Scheduler

Ils doivent utiliser :

```python
from api.deps import get_saasential_bridge
from api.databases.databases import get_core_db

db = get_core_db()
bridge = get_saasential_bridge(db=db)
service = bridge.get_scheduler_service()
```

Interdit :

```python
SchedulerService()  # ❌ Anti-pattern
```

---

## 6. Matrice Composant → Dépendances → Injection

| Composant          | Dépendances requises        | Injection                          |
| ------------------ | --------------------------- | ----------------------------------- |
| Route FastAPI      | `SaasentialCoreBridge`      | `Depends(get_saasential_bridge)`    |
| `SaasentialCoreBridge` | `AsyncIOMotorDatabase`  | `Depends(get_core_db)`              |
| `QuotasService`    | `AsyncIOMotorDatabase`      | Via bridge (lazy init)              |
| `SchedulerService` | `AsyncIOMotorDatabase`      | Via bridge (lazy init)              |
| Repository         | `AsyncIOMotorDatabase`      | Via service parent                  |

---

## 7. Anti-Patterns DI (interdits)

### 🔥 Anti-pattern n°1 : instanciation directe de service

Ex. dans un endpoint ou un connecteur.

```python
# ❌ INTERDIT
def my_route():
    service = QuotasService()  # Pas de DB injectée
```

Conséquence : contourne la DI → décohérence test/runtime.

### 🔥 Anti-pattern n°2 : fallback implicite

Exemples :

```python
MongoClient("mongodb://localhost:27017")      # ❌ interdit
RabbitMQ("amqp://guest:guest@localhost")      # ❌ interdit
```

Risque : la prod n'utilise pas le même chemin de code que les tests.

### 🔥 Anti-pattern n°3 : lecture directe des environnements dans un service

```python
# ❌ INTERDIT
import os
api_key = os.environ["API_KEY"]
```

Doit passer par `settings` :

```python
# ✅ CORRECT
from api.core.settings import get_settings
settings = get_settings()
api_key = settings.some_api_key
```

### 🔥 Anti-pattern n°4 : import circulaire dû à une mauvaise DI

Ce DOC vise aussi à les éliminer en centralisant les dépendances dans `api.deps`.

---

## 8. Checklist DI (à respecter avant chaque PR)

- [ ] Aucun service instancié directement dans `api/routes/*`
- [ ] Routes utilisent `Depends(get_saasential_bridge)` depuis `api.deps`
- [ ] Aucun `MongoClient()` dans le code métier
- [ ] Aucun `os.environ` dans des services
- [ ] Bridge construit toutes les dépendances
- [ ] Tests E2E override `get_core_db` et `get_saasential_bridge`
- [ ] Aucun fallback (`localhost:27017`, etc.)
- [ ] Workers utilisent `get_saasential_bridge(db=...)`

---

## 9. Tests (unitaires & E2E)

### 9.1 Tests unitaires

- injection fake DB
- injection fake repository
- services testés isolément

### 9.2 Tests E2E — Guide d'override

**Objectif** : Garantir que les tests E2E n'utilisent jamais `localhost:27017` par défaut.

#### Pattern obligatoire dans `tests/conftest.py` ou dans chaque test :

```python
from fastapi import FastAPI
from api.deps import get_core_db, get_saasential_bridge
from api.services.core.saasential_bridge import SaasentialCoreBridge
from motor.motor_asyncio import AsyncIOMotorDatabase

@pytest.fixture
async def test_db():
    """Base de données de test (fake ou MongoDB test)."""
    # Option 1 : Fake DB (recommandé pour tests rapides)
    from saasentialcore.tests.utils_fake_db import create_fake_db
    return create_fake_db()
    
    # Option 2 : MongoDB réel (pour tests d'intégration)
    # from api.databases.databases import init_clients
    # init_clients()  # Utilise TEST_DB_URI depuis .env
    # return get_core_db()

@pytest.fixture
def override_dependencies(app: FastAPI, test_db: AsyncIOMotorDatabase):
    """Override des dépendances FastAPI pour les tests."""
    # Override get_core_db
    app.dependency_overrides[get_core_db] = lambda: test_db
    
    # Override get_saasential_bridge
    def get_test_bridge() -> SaasentialCoreBridge:
        return SaasentialCoreBridge(db=test_db)
    
    app.dependency_overrides[get_saasential_bridge] = get_test_bridge
    
    yield
    
    # Nettoyage
    app.dependency_overrides.clear()

# Utilisation dans un test
async def test_s2_e2e_schedule(
    app: FastAPI,
    async_client: AsyncClient,
    override_dependencies,  # Utiliser la fixture
):
    # Les routes utiliseront automatiquement test_db via les overrides
    response = await async_client.post("/api/scheduler/posts/schedule", json=payload)
    assert response.status_code == 200
```

#### Vérifications automatiques dans les tests :

```python
def test_no_localhost_fallback():
    """Vérifie qu'aucun fallback vers localhost n'est utilisé."""
    import re
    import inspect
    
    # Vérifier que get_core_db() ne contient pas localhost:27017
    source = inspect.getsource(get_core_db)
    assert "localhost:27017" not in source, "get_core_db() contient un fallback localhost"
    
    # Vérifier que SaasentialCoreBridge.__init__ ne crée pas de DB par défaut
    bridge_source = inspect.getsource(SaasentialCoreBridge.__init__)
    assert "MongoClient" not in bridge_source or "localhost" not in bridge_source
```

---

## 10. CI/CD — Architecture Compliance (Blocage PR)

La CI doit détecter :

### Blocages immédiats :

- `QuotasService(` dans les routes
- `SchedulerService(` dans les routes
- `MongoClient(` dans le code métier
- `localhost:27017` hardcodé
- `os.environ` dans services
- Route sans `Depends(get_saasential_bridge)`

### Warnings :

- route sans `response_model`
- enum incorrecte
- shim non conforme

### Script de validation (à intégrer en CI) :

```bash
#!/bin/bash
# scripts/validate_di_compliance.sh

echo "🔍 Validation DI Compliance..."

# Vérifier les instanciations directes dans les routes
if grep -r "QuotasService(" api/routes/ products/*/api/routes/; then
    echo "❌ ERREUR: QuotasService() instancié directement dans les routes"
    exit 1
fi

if grep -r "SchedulerService(" api/routes/ products/*/api/routes/; then
    echo "❌ ERREUR: SchedulerService() instancié directement dans les routes"
    exit 1
fi

# Vérifier les fallbacks localhost
if grep -r "localhost:27017" api/ products/ saasentialcore/ --exclude-dir=.venv; then
    echo "❌ ERREUR: localhost:27017 hardcodé"
    exit 1
fi

# Vérifier que les routes utilisent Depends
if ! grep -r "Depends(get_saasential_bridge)" api/routes/ products/*/api/routes/; then
    echo "⚠️  WARNING: Certaines routes n'utilisent pas Depends(get_saasential_bridge)"
fi

echo "✅ DI Compliance OK"
```

---

## 11. Risques en cas de violation

| Violation                       | Impact                                      |
| ------------------------------- | ------------------------------------------- |
| Service instancié sans DI       | Bugs silencieux + tests trompeurs           |
| Fallback locaux                 | Différence runtime/test + pannes invisibles |
| Accès direct DB                 | Impossibilité de mocker + dette technique  |
| Mauvaise construction container | Workers non déterministes                   |

---

## 12. Glossaire interne

- **Bridge** : Agrégateur des services & dépendances (`SaasentialCoreBridge`).
- **DI** : Dependency Injection.
- **SRE++** : Standard avancé de fiabilité & architecture.
- **Idempotence** : Résultat identique même sous retry.

---

## 13. Conclusion

DOC-001 est la fondation de toute l'architecture Sparkmetriq.

**Toute violation = PR bloquée automatiquement.**

---

## 14. Références

- DOC-002 : Shim Pattern Standard
- DOC-003 : API Schema & Response Contract
- DOC-004 : Quotas State Machine
- DOC-005 : Retry Policy & Idempotency
