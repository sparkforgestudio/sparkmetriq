Voici **DOC-SC-011 — Admin Panel Contract**, version longue, complète, cohérente avec toute la série SC (001 → 010), parfaitement alignée avec l’architecture SaasentialCore, le multi-startup, le multi-produit, et les exigences SRE++, sécurité, RBAC, et API boundaries.

Ce document formalise **toutes** les règles :

* structure du panel,
* permissions UI / RBAC,
* rôle du backend vs frontend,
* isolation tenant stricte,
* restrictions d’accès,
* règles CI/CD,
* audit & logs,
* standards d’UX produit.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-011_admin_panel_contract.md
```

---

# 📘 `DOC-SC-011_admin_panel_contract.md`

```markdown
---
title: DOC-SC-011 — Admin Panel Contract (Roles, UI Isolation, API Boundaries)
version: 1.0
status: Stable
category: SaasentialCore / Frontend / RBAC / Admin / Security
last_updated: 2025-02-16
---

# 1. Objectif du document

DOC-SC-011 définit le **contrat officiel du Admin Panel**, sa structure, ses permissions, ses frontières API, son intégration multi-startup/multi-produit, et son interaction avec SaasentialCore.

Ce document garantit que :

- le panel est sécurisé, multi-tenant, et multi-produit,
- l’UI suit des frontières strictes alignées avec API,
- la gestion des rôles est cohérente avec DOC-SC-005 (AuthN/AuthZ),
- l’isolation org/startup est respectée (DOC-SC-004),
- aucune logique backend ne se retrouve dans le frontend,
- l’observabilité du panel est complète (DOC-SC-009),
- le panel reste stable et modulaire pour Sparkmetriq, Sparkpusher et futurs produits.

---

# 2. Principes fondamentaux

## ✔ 2.1. L’Admin Panel n’est **pas** un backend  
Il ne doit contenir *aucune* logique métier — uniquement UI + appels API.

## ✔ 2.2. Zero-Trust sur le frontend  
Le panel **ne doit jamais faire confiance** aux données utilisateur :

- toutes permissions sont validées côté backend,
- aucune logique de sécurité dans le frontend,
- pas de filtrage tenant côté UI seul.

## ✔ 2.3. Multi-startup et multi-produit  
Le panel doit afficher :

- uniquement les startups auxquelles l’utilisateur a accès,
- uniquement les organisations associées,
- uniquement les produits autorisés (Sparkmetriq, Sparkpusher…),
- uniquement les données de l’org active.

## ✔ 2.4. Respect strict de la séparation Core / Produits  
Un produit ne peut pas injecter du code global dans le panel Core.

---

# 3. Architecture du Admin Panel

Arborescence :

```

frontend/admin_panel/
core/
layout/
auth/
components/
tenants/
routing/
api_client/
products/
sparkmetriq/
sparkpusher/
<future_products>/
pages/
dashboard/
settings/
org/
product_switcher/

```

---

# 4. Rôles & Permissions (UI)

L’Admin Panel doit s’adapter dynamiquement aux permissions définies dans DOC-SC-005.

## 4.1. Rôles principaux

| Rôle | Portée | Droits |
|------|---------|--------|
| `core.admin` | plateforme | accès global + management startups |
| `startup.owner` | startup | gestion des organisations |
| `org.admin` | org | gestion users + produits |
| `product.admin` | produit | gestion des features produit |
| `product.editor` | produit | usage avancé du produit |
| `product.viewer` | produit | lecture seule |

## 4.2. Le frontend doit être **permission-aware**

Exemples :

- cacher un bouton si permission manquante,
- désactiver les actions dangereuses si non autorisé,
- n’afficher **aucune** information cross-tenant.

---

# 5. Tenant Switching (obligatoire)

Le panel doit proposer :

```

Startup Selector → Organisation Selector → Produit Selector

```

Chaque action du panel doit être contextualisée sur :

- startup active  
- organisation active  
- produit actif  

Les requêtes API doivent transmettre :

```

X-Startup-ID
X-Org-ID
X-Product-ID
X-Trace-ID

```

Backend revalide tout (DOC-SC-005).

---

# 6. API Boundaries (contrat Core)

L’Admin Panel ne doit communiquer **que** avec les routes définies dans l'API FastAPI.  
Interdictions absolues :

- ❌ accès direct aux services Core ou produits,
- ❌ accès direct à Mongo ou Rabbit,
- ❌ bypass des règles AuthN/AuthZ backend,
- ❌ lecture des secrets par le panel.

### Règle d’or :

> Le frontend ne doit jamais faire quelque chose que le backend ne valide pas.

---

# 7. Intégration multi-produit

Chaque produit peut fournir son module UI dans :

```

frontend/admin_panel/products/<product_id>/

```

Chaque module contient :

- pages spécifiques,
- composants UI,
- tests UI frontaux.

### Exemples :

```

/products/sparkmetriq/s2_calendar
/products/sparkmetriq/s2_jobs
/products/sparkpusher/inbox
/products/sparkpusher/templates

````

Le panneau principal détecte les produits disponibles via :

1. JWT (`products` claim)  
2. Manifest produit (DOC-SC-002)  
3. Permissions de l’utilisateur  

---

# 8. Observabilité du panel (aligné DOC-SC-009)

Le panel doit générer :

- journaux UI (`ui_event`, `ui_error`),
- métriques d’interactions (latence, erreurs API),
- traces distribué côté frontend → backend.

## 8.1. Logging UI structuré

Exemples :

```json
{
  "event": "ui.click",
  "element": "schedule_button",
  "product_id": "sparkmetriq",
  "startup_id": "stp_1",
  "org_id": "org_22",
  "trace_id": "xyz-111",
  "timestamp": "..."
}
````

## 8.2. Metrics UI côté frontend

* `ui_errors_total`
* `ui_api_latency_ms`
* `ui_load_time_ms`
* `ui_product_switches_total`
* `ui_session_duration`

---

# 9. Contraintes de Sécurité

### Obligatoires :

* JWT uniquement en cookie HttpOnly + rotation (DOC-SC-005)
* aucun secret ne transite dans le frontend
* hashing anonymisé des userIds dans logs frontend
* CSP strict (Content Security Policy)
* interdire inline scripts
* sandbox des iframes des produits
* pas de stockage local de tenant data sensitive

### Interdits :

* utiliser `localStorage` pour des données sensibles
* exposer des IDs internes non nécessaires
* utiliser un token API produit côté frontend

---

# 10. Gestion des Organisations & Utilisateurs

Pages obligatoires :

* liste des organisations
* création d’une org
* liste des utilisateurs d’une org
* gestion des rôles par utilisateur
* audit log UI

### backend requis :

* filtrage strict par tenant
* contrôles d’autorisation multi-niveaux

---

# 11. Gestion produit (Sparkmetriq, Sparkpusher…)

Chaque produit doit fournir :

* pages pour ses propres settings
* pages pour ses propres analytics
* pages pour ses propres workflows

### Exemple Sparkmetriq S2 :

* calendrier multi-plateformes
* gestion des jobs
* gestion des quotas
* logs dispatch / scheduler
* analytics publications

---

# 12. Performance & UX (SRE++)

### Standards :

* temps de chargement panel < 1.2s
* latence API P95 < 300ms
* préchargement modules produits
* pagination côté backend
* WebSockets pour temps réel (logs, scheduler, workers)

### Interdits :

* boucles intensives UI,
* polling trop fréquent (< 1s) hors WS,
* chargement massif des données d’un tenant.

---

# 13. Tests frontend (aligné DOC-SC-008)

Le panel doit posséder :

### Unit tests

* composants UI isolés

### Integration tests

* navigation, routing, auth guard

### End-to-end tests (Playwright)

* login
* changement tenant
* accès produit
* actions principales (schedule, publish…)

### Contract tests

* validation des schémas API

---

# 14. CI/CD Compliance Rules

### 🚫 Bloquant :

* page affichant un produit sans permission
* fuite d’identifiants tenant côté frontend
* connexion backend hors API officielle
* inline script dans UI
* absence de tests
* absence d’audit log UI
* navigation vers tenant non autorisé
* utilisation de secrets côté panel

### ⚠ Warning :

* absence de telemetry UI
* absence de fallback erreurs
* absence de tests E2E panel
* absence de pages settings produit

---

# 15. Invariants non négociables

1. Le frontend ne contient aucune logique métier.
2. Aucun secret ne doit transiter dans le panel.
3. Le panel doit toujours respecter les permissions backend.
4. TenantContext doit être appliqué à chaque requête API.
5. Chaque module produit doit être isolé.
6. Le panel doit être observable (logs, metrics, traces).
7. Toute PR violant DOC-SC-011 est bloquée.

---

# 16. Conclusion

DOC-SC-011 fournit le cadre contractuel complet du Admin Panel :

* sécurité intégrale (zero-trust),
* isolation tenant et produit,
* cohérence RBAC,
* observabilité complète,
* extensibilité contrôlée pour futurs produits,
* alignement total avec architecture Core, DI, Events, Secret Management.

Il constitue le standard officiel pour la construction et l’évolution du panel admin.

```
