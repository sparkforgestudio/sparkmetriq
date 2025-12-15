Parfait.
**Option C (Hybride : auto-discovery + manifest produit)** est la meilleure pour un monorepo multi-startup moderne : flexible, robuste, compatible CI/CD, et parfaitement scalable.

Voici maintenant la **version longue, propre et complète** de :

# ✅ **DOC-SC-002 — Multi-Startup & Product Registration Contract**

*(architecture multi-produit, gestion automatique + manifest, règles CI, SRE, activation/désactivation)*

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-002_multi_startup_product_registration_contract.md
```

---

# 📘 `DOC-SC-002_multi_startup_product_registration_contract.md`

```markdown
---
title: DOC-SC-002 — Multi-Startup & Product Registration Contract
version: 1.0
status: Stable
category: SaasentialCore / Multi-Startup / Product Registration
last_updated: 2025-02-13
---

# 1. Objectif du document

DOC-SC-002 définit le **contrat officiel** permettant à SaasentialCore :

- d’identifier les produits présents dans le workspace (`products/*`),
- de charger uniquement ceux qui sont valides,
- d'assurer une intégration cohérente dans l’API unifiée,
- d’isoler les produits au runtime (multi-startup),
- de garantir la compatibilité CI/CD, SRE et sécurité,
- de conserver un mécanisme d’activation/désactivation propre.

Ce document fait suite à DOC-SC-001 (Architecture Workspace Contract).

---

# 2. Architecture générale

SaasentialCore doit être capable de :

1. **scanner dynamiquement** tous les dossiers dans `products/`
2. vérifier qu’un produit contient un **manifest officiel**
3. valider ce manifest (signature, structure, version)
4. importer dynamiquement le produit
5. exposer un registre interne (`ProductRegistry`)
6. permettre à l’API de monter les routes du produit
7. permettre aux tests de conditionner l'exécution selon les produits activés

---

# 3. Structure obligatoire d’un produit

Tout produit doit respecter la structure minimale suivante :

```

products/<product_id>/
**init**.py
product_manifest.json
domain/
services/
schemas/
api/

````

Le fichier **product_manifest.json** est obligatoire.

---

# 4. Le manifest produit (obligatoire)

Exemple complet :

```json
{
  "product_id": "sparkmetriq",
  "name": "Sparkmetriq Platform",
  "version": "2.0",
  "enabled": true,
  "entrypoint": "products.sparkmetriq",
  "routes_module": "products.sparkmetriq.api.routes",
  "capabilities": {
    "scheduling": true,
    "workers": true,
    "connectors": true,
    "frontends": ["admin_panel"]
  },
  "dependencies": {
    "python": ">=3.10",
    "saasentialcore": ">=1.0"
  }
}
````

### Règles obligatoires :

* `product_id` = identifiant unique
* `enabled` = permet l’activation/désactivation sans supprimer le code
* `entrypoint` = module Python principal
* `routes_module` = module à monter dans l’API
* `version` = version explicite du produit
* `capabilities` = description fonctionnelle
* `dependencies` = contraintes minimales

### Interdictions :

* pas de secret dans le manifest
* pas de config runtime (DOC-019)
* pas de référence directe à un autre produit

---

# 5. Auto-discovery hybride (Option C)

SaasentialCore exécute un **Product Discovery Pass** :

## 5.1. Étape 1 — Scan des dossiers

```
products/
    sparkmetriq/
    sparkpusher/
    malformedproduct/   ← ignoré s'il n’a pas de manifest valide
```

## 5.2. Étape 2 — Validation du manifest

Pour chaque dossier :

* présence du fichier `product_manifest.json`
* JSON valide
* champs obligatoires présents
* version compatible
* module importable (`importlib`)

## 5.3. Étape 3 — Enregistrement dans le ProductRegistry

```python
registry.add(ProductMetadata(...))
```

## 5.4. Étape 4 — Activation conditionnelle

Si `enabled = false` → le produit n’est pas exposé.

---

# 6. Le Product Registry (cœur du système)

Le registre doit être implémenté dans :

```
saasentialcore/products/registry.py
```

Exemple minimal :

```python
class ProductMetadata(BaseModel):
    product_id: str
    name: str
    version: str
    enabled: bool
    entrypoint: str
    routes_module: Optional[str]
    capabilities: Dict[str, Any]

class ProductRegistry:
    def __init__(self):
        self.products: Dict[str, ProductMetadata] = {}

    def register(self, metadata: ProductMetadata):
        self.products[metadata.product_id] = metadata

    def enabled_products(self):
        return [p for p in self.products.values() if p.enabled]
```

---

# 7. Intégration avec l’API unifiée

L’API (dans `api/main.py`) doit :

1. charger SaasentialCore
2. récupérer la liste des produits activés
3. importer dynamiquement leurs routes
4. les monter sous un préfixe standardisé :

```
/p/<product_id>/...
```

Exemple :

```python
for product in registry.enabled_products():
    module = import_module(product.routes_module)
    app.include_router(module.router, prefix=f"/p/{product.product_id}")
```

---

# 8. Multi-Startup & Multi-Tenant Isolation

Chaque produit doit fonctionner :

* indépendamment des autres produits,
* avec son propre espace de données (via org_id, tenant_id),
* sans jamais lire ou modifier les données d’un autre produit.

Aligné sur :

* DOC-SC-004 (Multi-Tenant & Data Isolation),
* DOC-009 (Isolation Sparkmetriq S2),
* DOC-019 (Secrets Management).

---

# 9. Versioning & Compatibility

Le manifest produit sert aussi de **contrat de version**.

### Règles :

* aucune version incompatible ne doit être chargée
* SaasentialCore doit vérifier `dependencies.saasentialcore`
* un produit éclaté (breaking changes) → version majeure incrementée
* l’API refuse de monter un produit incompatible
* CI bloque les incompatibilités

---

# 10. Sécurité & SRE (obligatoire)

## 10.1. Logs

Chaque étape d’enregistrement produit doit produire :

* `product.discovered`
* `product.manifest.invalid`
* `product.manifest.loaded`
* `product.enabled`
* `product.disabled`
* `product.routes.mounted`

## 10.2. Métriques Prometheus

SaasentialCore expose :

```
products_total
products_enabled_total
product_load_time_seconds
product_routes_mounted_total
```

## 10.3. Alerting

Alarme si :

* manifest invalide
* produit impossible à charger
* conflit product_id
* version incompatible

---

# 11. CI/CD Contract

Un job CI `product_compliance.yml` doit vérifier :

### 🚫 Bloquant :

* absence de `product_manifest.json`
* manifest invalide
* dépendance produit → produit
* produit désactivé mais monté par API
* version non alignée
* violation de DOC-SC-001

### ⚠ Warning :

* capabilities incomplètes
* version produit manquante
* absence de tests produit
* absence de dashboard produit (si applicable)

---

# 12. Onboarding : créer un nouveau produit

Pour créer un produit valide :

1. Créer dossier sous `products/<nom>/`
2. Ajouter `product_manifest.json`
3. Implémenter domain/services/schemas
4. Ajouter un module `api/routes.py`
5. Tester l’import
6. Lancer `product_discovery` en local
7. Exécuter les tests
8. Commit + PR

---

# 13. Invariants non négociables

1. Un produit **sans manifest** n’existe pas.
2. Un produit **désactivé** doit être totalement invisible.
3. Aucun produit ne dépend d’un autre produit.
4. SaasentialCore reste indépendant et agnostique.
5. L’API ne charge que les produits validés.
6. Un produit mal formé ne doit jamais casser le run global.

---

# 14. Conclusion

DOC-SC-002 fixe les règles fondamentales du **multi-startup SaasentialCore** :

* détection automatique élégante
* contrôle strict via manifest
* activation désactivation fiable
* zero-coupling entre produits
* intégration API unifiée
* compatibilité CI/CD & SRE

**Toute PR violant DOC-SC-002 doit être bloquée.**

````
# DOC-SC-002_multi_startup_product_registration_contract.md
