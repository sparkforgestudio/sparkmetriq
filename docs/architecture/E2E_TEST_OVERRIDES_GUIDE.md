# Guide E2E Test Overrides

*Guide pratique pour override les dépendances dans les tests E2E*

```yaml
---
title: E2E Test Overrides Guide
version: 1.0
status: Stable
category: Testing / E2E
last_updated: 2025-01-28
---
```

---

## Objectif

Ce guide explique comment override `get_core_db` et `get_saasential_bridge` dans les tests E2E pour garantir qu'**aucun test n'utilise jamais `localhost:27017` par défaut**.

---

## Pattern obligatoire

### 1. Fixture de test DB

Dans `tests/conftest.py` ou dans chaque fichier de test :

```python
import pytest
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorDatabase
from api.deps import get_core_db, get_saasential_bridge
from api.services.core.saasential_bridge import SaasentialCoreBridge

@pytest.fixture
async def test_db() -> AsyncIOMotorDatabase:
    """
    Base de données de test (fake ou MongoDB test).
    
    Option 1 : Fake DB (recommandé pour tests rapides)
    """
    from saasentialcore.tests.utils_fake_db import create_fake_db
    return create_fake_db()
    
    # Option 2 : MongoDB réel (pour tests d'intégration)
    # from api.databases.databases import init_clients
    # init_clients()  # Utilise TEST_DB_URI depuis .env
    # from api.databases.databases import get_core_db as _get_core_db
    # return _get_core_db()

@pytest.fixture
def override_dependencies(app: FastAPI, test_db: AsyncIOMotorDatabase):
    """
    Override des dépendances FastAPI pour les tests.
    
    Cette fixture garantit que :
    - get_core_db() retourne test_db
    - get_saasential_bridge() utilise test_db
    """
    # Override get_core_db
    app.dependency_overrides[get_core_db] = lambda: test_db
    
    # Override get_saasential_bridge
    def get_test_bridge() -> SaasentialCoreBridge:
        return SaasentialCoreBridge(db=test_db)
    
    app.dependency_overrides[get_saasential_bridge] = get_test_bridge
    
    yield
    
    # Nettoyage
    app.dependency_overrides.clear()
```

### 2. Utilisation dans un test

```python
async def test_s2_e2e_schedule(
    app: FastAPI,
    async_client: AsyncClient,
    override_dependencies,  # ✅ Utiliser la fixture
    test_db: AsyncIOMotorDatabase,
):
    """
    Test E2E qui utilise la DB de test injectée.
    
    Les routes utiliseront automatiquement test_db via les overrides.
    """
    payload = UnifiedPostPayload(...)
    
    # Les routes utiliseront automatiquement test_db
    response = await async_client.post(
        "/api/scheduler/posts/schedule",
        json=payload.model_dump(mode="json"),
    )
    
    assert response.status_code == 200
    
    # Vérifier en base (test_db)
    job = await test_db["scheduled_tasks"].find_one({"job_id": job_id})
    assert job is not None
```

### 3. Pattern inline (si pas de fixture)

```python
async def test_specific_case(
    app: FastAPI,
    async_client: AsyncClient,
    test_db: AsyncIOMotorDatabase,
):
    from api.deps import get_core_db, get_saasential_bridge
    from api.services.core.saasential_bridge import SaasentialCoreBridge
    
    # Override inline
    app.dependency_overrides[get_core_db] = lambda: test_db
    app.dependency_overrides[get_saasential_bridge] = lambda: SaasentialCoreBridge(db=test_db)
    
    try:
        # Test
        response = await async_client.post("/api/...", json=payload)
        assert response.status_code == 200
    finally:
        # Nettoyage
        app.dependency_overrides.clear()
```

---

## Vérifications automatiques

### Test de non-régression

```python
def test_no_localhost_fallback():
    """Vérifie qu'aucun fallback vers localhost n'est utilisé."""
    import inspect
    from api.deps import get_core_db
    
    # Vérifier que get_core_db() ne contient pas localhost:27017
    source = inspect.getsource(get_core_db)
    assert "localhost:27017" not in source, "get_core_db() contient un fallback localhost"
```

---

## Checklist E2E

Avant chaque test E2E :

- [ ] Fixture `test_db` définie (fake ou MongoDB test)
- [ ] Fixture `override_dependencies` utilisée
- [ ] `app.dependency_overrides[get_core_db]` défini
- [ ] `app.dependency_overrides[get_saasential_bridge]` défini
- [ ] Nettoyage dans `finally` ou `yield` de fixture
- [ ] Aucun appel direct à `get_core_db()` sans override

---

## Conclusion

**Tout test E2E doit override `get_core_db` et `get_saasential_bridge` pour éviter les connexions à `localhost:27017`.**

