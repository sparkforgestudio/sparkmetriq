Parfait.
Voici maintenant **DOC-SC-008 — Testing & Workspace Strategy Contract**, un document essentiel qui unifie l’approche de test dans tout le monorepo SaasentialCore + Produits.
Il définit **quoi tester**, **où**, **comment**, **avec quelle structure**, et surtout **comment garantir la non-régression multi-startup / multi-produit**.

Ce document corrige et dépasse largement l’approche standard, pour la transformer en **SRE++ Testing Strategy**, adaptée à un runtime composé de :

* API FastAPI
* Scheduler / Dispatcher
* Workers Celery
* Connecteurs externes
* Multi-tenant
* Multi-produits
* Multi-startups

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-008_testing_workspace_strategy_contract.md
```

---

# 📘 `DOC-SC-008_testing_workspace_strategy_contract.md`

```markdown
---
title: DOC-SC-008 — Testing & Workspace Strategy Contract
version: 1.0
status: Stable
category: SaasentialCore / Testing / Workspace / Quality Assurance
last_updated: 2025-02-15
---

# 1. Objectif du document

DOC-SC-008 définit la **stratégie de test unifiée** du monorepo SaasentialCore :

- types de tests à produire et leurs responsabilités,
- organisation stricte du workspace `tests/`,
- règles de séparation Core / Produits,
- stratégie de mocking et DI (aligné DOC-SC-003),
- protocoles E2E pour S2/S3/S4,
- intégration dans CI/CD,
- couverture obligatoire pour releases Core et Produits.

Il vise à garantir :

- la stabilité architecturale,  
- la non-régression fonctionnelle,  
- l’isolation multi-tenant et multi-produit  
- le niveau de qualité conforme aux standards SRE++.

---

# 2. Principes fondamentaux

## ✔ 2.1. Tout changement doit être accompagné de tests  
Toute PR doit contenir :

- tests unitaires pour le changement,
- tests d’intégration si API ou services,
- tests E2E si le flux système est impacté.

## ✔ 2.2. La CI représente la vérité  
Un merge ne peut être effectué si :

- le coverage < seuil,
- les tests d’architecture échouent,
- les tests E2E échouent.

## ✔ 2.3. Les tests doivent refléter l’architecture  
Puisque SaasentialCore impose une architecture stricte, les tests doivent :

- valider les invariants Core (DOC-SC-001),
- valider les contrats multi-startup (DOC-SC-004),
- valider les mécanismes de sécurité (DOC-SC-005),
- valider les événements (DOC-SC-006),
- valider la compatibilité versionnée (DOC-SC-007).

## ✔ 2.4. Aucun test ne doit dépendre d’un état partagé  
Les tests sont **stateless**, ou isolés via fixtures.

## ✔ 2.5. Les tests produits ne doivent jamais modifier Core  
Aligné sur DOC-SC-001 & DOC-SC-002.

---

# 3. Organisation officielle du dossier `tests/`

Structure requise :

```

tests/
unit/
saasentialcore/
products/
integration/
core/
products/
api/
e2e/
s2/
s3/
s4/
architecture/
smoke/

```

---

# 4. Tests unitaires (unit/)

### Rôle :
Tester **une fonction**, **une classe**, **un composant isolé**.

### Interdictions :
- aucun accès réel à Mongo / RabbitMQ,
- aucun appel réseau,
- aucun événement cross-produit.

### Obligations :
- mocking DI container,
- injection controlée,
- fixtures reproductibles.

### Exemples :
- validateurs Pydantic,
- services Core stateless,
- helpers cryptographiques,
- utils tenant isolation.

---

# 5. Tests d’intégration (integration/)

### Rôle :
Tester un module avec ses dépendances internes.

### Scope :
- une API interne + une DB réelle (ou in-memory),
- un produit + DI + Core,
- un product registry.

### Interdit :
- exécuter la stack complète (cela appartient aux E2E).

### Obligatoire :
- démarrer une base Mongo de test,
- exécuter DI réelle via container (DOC-SC-003),
- utiliser fixtures tenant complètes (DOC-SC-004).

### Exemples :
- test SchedulerService → Mongo (sans Rabbit),
- test ProductRegistry → manifest + load dynamic.

---

# 6. Tests API

### Rôle :
Tester les routes FastAPI versionnées.

### Obligations :
- utiliser `TestClient`,
- injection de DI Core via overrides,
- simulation JWT (DOC-SC-005),
- isolation tenant obligatoire.

### Exemples :
- POST /schedule → 200,
- POST /schedule → permission_denied,
- GET /jobs → tenant filtering correct.

---

# 7. Tests E2E (end-to-end)

Les tests E2E sont **le cœur des tests SaasentialCore**.

Ils valident :

- API → Scheduler → Dispatcher → Worker → Connecteurs
- isolation tenant complète  
- retry / backoff (DOC-005)  
- propagation d’événements (DOC-SC-006)  
- update des quotas (DOC-004)  
- idempotence  
- logging structuré  

### Structure recommandée :

```

tests/e2e/s2/test_scheduling_flow.py
tests/e2e/s2/test_failure_modes.py
tests/e2e/s2/test_connectors_endpoints.py

````

### Obligatoire :
- exécuter stack docker-compose de test,
- exécuter les workers,
- utiliser un Rabbit test,
- utiliser une DB test,
- simuler les connecteurs externes.

### Interdit :
- utiliser les vrais endpoints externes (Facebook/TikTok/etc.).

---

# 8. Tests architecture (architecture/)

Très important dans un monorepo.

Ces tests valident :

- les dépendances autorisées (DOC-SC-001),
- absence d’instanciation directe sans DI (DOC-SC-003),
- conformité des manifests produits (DOC-SC-002),
- stabilité du TenantContext (DOC-SC-004),
- absence de tokens secrets dans le code (DOC-019),
- versioning conforme (DOC-SC-007).

### Exemple :

#### 8.1. Détection du code interdit :

```python
def test_no_direct_mongo_import():
    forbidden = ["MongoClient(", "pymongo.MongoClient"]
    for file in scan_python_files("products"):
        assert not contains_any(file, forbidden)
````

#### 8.2. Détection des produits mal configurés :

```python
def test_product_manifest_valid():
    for manifest in load_manifests():
        validate_schema(manifest)
```

---

# 9. Tests Smoke (smoke/)

Ils valident que :

* l’API démarre,
* les routes principales répondent,
* les services DI se résolvent,
* le scheduler démarre,
* les workers sont connectés au broker.

Durée < 5 secondes.

---

# 10. Test Data Strategy

### Règles :

* aucun test ne doit polluer la DB réelle,
* usage obligatoire d’une base `test_XXXX`,
* fixtures déclarées dans :

```
tests/fixtures/
```

---

# 11. Mock Strategy (aligné DI — DOC-SC-003)

Ce qui doit être mocké systématiquement :

* connecteurs externes (TikTok, Instagram, Threads),
* API tierces,
* appels réseau HTTP,
* librairies non déterministes (dates, randomness).

### Jamais mocker :

* logiques métiers Core,
* logiques services produits,
* interactions avec DB test.

---

# 12. Coverage requirements

Minimum :

* Core : **85%**
* Produits : **80%**
* E2E coverage : **100% des flux critiques**
* Architecture tests : **obligatoire**

---

# 13. CI/CD Integration

Pipeline recommandé :

```
1. Lint & Format
2. Architecture tests
3. Unit tests
4. Integration tests
5. API tests
6. E2E tests (docker-compose)
7. Security scans
8. Coverage enforcement
9. Build & Publish
```

Une PR ne merge pas si :

* un test échoue,
* coverage insuffisant,
* architecture test violé,
* breaking non déclaré (DOC-SC-007).

---

# 14. Tooling

* Pytest (obligatoire)
* pytest-asyncio
* pytest-xdist (parallélisation)
* httpx (API test)
* mongomock ou MongoDB TestContainer
* Docker Compose pour E2E

---

# 15. Invariants non négociables

1. Tout changement doit être testé à l’endroit approprié.
2. Aucun test ne doit casser l’isolation tenant.
3. E2E doit refléter la stack réelle de production.
4. Les tests architecture sont obligatoires.
5. Les tests doivent garantir l’absence de régression versionnée.
6. La CI doit bloquer toute violation de DOC-SC-008.

---

# 16. Conclusion

DOC-SC-008 donne au monorepo SaasentialCore :

* un cadre de tests clair, cohérent, industriel,
* une séparation parfaite des niveaux de test,
* une intégration profonde avec l’architecture DI / Events / Tenant,
* une stratégie SRE-ready pour S2/S3/S4,
* une assurance qualité capable d’accompagner la croissance du projet.

C’est un pilier de stabilité et de scalabilité pour la suite.

```

### 👉 **DOC-SC-009 — Observability & SRE Contract (Core)**

