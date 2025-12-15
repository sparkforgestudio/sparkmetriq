Voici **DOC-011 — Admin Panel Contract (Version longue, 8–14 pages)**, format Markdown technique, conçu pour structurer l’architecture du **panneau d’administration Sparkmetriq**, garantir l’isolation multi-tenant, standardiser les permissions, définir les contrats API/UI, encadrer le rôle du frontend Next.js, et établir les limites fonctionnelles strictes entre l’UI et l’API backend.

Prêt à être intégré dans :

```
docs/architecture/DOC-011_admin_panel_contract.md
```

---

# 📘 **DOC-011 — Admin Panel Contract (Version longue)**

*Document Technique de Référence — Sparkmetriq Suite / Admin Panel / RBAC / UI Architecture / Multi-Tenant Isolation*

```markdown
---
title: DOC-011 — Admin Panel Contract
version: 1.0
status: Stable
category: Architecture / Frontend / Permissions / Multi-Tenant / UI-Backend Contract
last_updated: 2025-02-04
---
```

---

# # **1. Objectif du document**

L’Admin Panel Sparkmetriq permet :

* la gestion des organisations (agences),
* la gestion des comptes sociaux,
* la visualisation du calendrier des publications (S2),
* la gestion des tâches programmées,
* la visualisation des logs et métriques,
* l’accès aux quotas,
* la configuration des connecteurs,
* la gestion des utilisateurs et des rôles,
* les opérations avancées (superadmin → multi-agences).

Ce document fixe **le contrat d’architecture** entre :

* le frontend Next.js (admin_panel),
* l’API FastAPI,
* SaasentialCore (future multi-startup DOC-YY),
* Sparkmetriq S2/S3/S4.

Objectifs :

* isoler les tenants (DOC-009),
* garantir la sécurité (DOC-008),
* structurer les permissions,
* éviter toute logique métier côté UI,
* garantir un UI cohérent, stable et maintenable.

---

# # **2. Périmètre**

S’applique à :

* tout le code dans `admin_panel/*`
* pages Next.js (app router)
* appels API depuis l’UI
* gestion authentification / sessions
* affichage des données multi-tenant
* composants UI critiques (calendrier, logs, scheduler UI)

Hors périmètre :

* frontend public marketing
* composants internes non liés au panel

---

# # **3. Principes fondamentaux**

## ✔ **3.1. L’Admin Panel ne contient aucune logique métier**

Le Panel :

* **affiche** les données
* **déclenche** des actions backend
* **ne calcule rien de critique**

100% de la logique métier doit résider dans :

* API
* Services Sparkmetriq
* Workers

---

## ✔ **3.2. UI-Backend Contract obligatoire**

Chaque page Next.js correspond à :

* un endpoint GET
* un endpoint POST/PUT/DELETE selon action

Si un endpoint n’existe pas → la page UI n’a pas le droit d’exister.

---

## ✔ **3.3. Multi-tenant isolation stricte**

L’Admin Panel de l’agence A :

* ne peut pas voir les données de l’agence B
* ne peut pas passer un org_id dans un paramètre
* ne peut jamais manipuler les tokens externes directement

---

## ✔ **3.4. RBAC enforce côté backend et côté frontend**

L’UI n’expose que les fonctionnalités compatibles avec le rôle :

| Rôle         | Capabilities                      |
| ------------ | --------------------------------- |
| superadmin   | multi-agences, diagnostics, audit |
| org_admin    | gestion org, quotas, accounts     |
| org_operator | publications, connecteurs         |
| org_viewer   | lecture seule                     |
| bot_service  | routes automations uniquement     |

---

## ✔ **3.5. Observability intégrée (DOC-006)**

Chaque interaction panel → API doit être traçable via :

```
request_id
user_id
org_id
role
ui_component
```

---

# # **4. Structure d’architecture UI (Next.js)**

Arborescence obligatoire :

```
admin_panel/
  app/
    dashboard/
    schedule/
    posts/
    connectors/
    quotas/
    logs/
    analytics/
    users/
  components/
    ui/
    forms/
    tables/
    charts/
  lib/
    api/
    auth/
    rbac/
  middleware/
```

### Interdits :

* composants business mixtes
* pages exposant directement les logs sensibles
* appels API en dur → doivent passer par une couche API interne

---

# # **5. Authentification & Sessions**

## **5.1. JWT Access Token + Refresh Token**

UI utilise :

* Access Token : durée 15 minutes
* Refresh Token : HttpOnly cookie, durée 7 jours

Les appels API incluent toujours le **Bearer Token**.

---

## **5.2. Middleware Next.js obligatoire**

Doit :

* vérifier la présence du token
* rafraîchir si nécessaire
* rediriger vers `/login` si échec
* attacher les rôles utilisateur

---

# # **6. API Boundaries (contrats stricts)**

L’Admin Panel ne doit jamais :

* appeler la DB,
* appeler un service interne,
* interpréter une erreur métier sans s’appuyer sur l’API.

### Exemple d’appel correct :

```ts
const res = await api.get("/s2/jobs?from=...&to=...");
```

### Exemple incorrect (interdit) :

```ts
const result = await fetch("http://localhost:27017/jobs"); // ❌
```

---

# # **7. Pages critiques et leurs obligations contractuelles**

## ✔ **7.1. Calendar View (S2)**

Affiche :

* posts programmés
* posts exécutés
* erreurs
* statut des quotas

Le calendrier ne calcule rien → c’est l’API qui :

* agrège
* filtre par org
* applique le fuseau horaire
* donne le statut final

UI doit uniquement afficher.

---

## ✔ **7.2. Workforce & Scheduler View**

Affiche :

* jobs en file
* statut workers
* retry rate
* erreurs récentes

Dépend du module observability (DOC-006).

---

## ✔ **7.3. Connectors Management**

Affiche :

* le statut des comptes sociaux
* expiration tokens
* erreurs récentes
* possibilité de reconnecter via OAuth

Interdictions :

* UI ne doit JAMAIS afficher le token OAuth
* UI ne doit jamais manipuler un token brut
* UI ne doit jamais lire la DB ― uniquement API

---

## ✔ **7.4. Quotas View**

Données affichées :

* quota réservé
* quota consommé
* quota restant
* historique

L’UI ne doit pas :

* calculer elle-même les quotas
* interpréter les états du job (DOC-004)
* modifier les quotas

---

## ✔ **7.5. Logs View**

Doit utiliser **le pipeline d’observabilité** :

```
/api/logs?org_id=auto&level=error
```

Interdit :

* accès direct aux logs système
* affichage des tokens/secrets

---

## ✔ **7.6. Users & Roles**

UI peut :

* créer un utilisateur
* lui attribuer un rôle
* le désactiver

Mais l’UI ne doit jamais :

* définir un rôle superadmin (réservé backend uniquement)
* permettre à un user d’une agence de voir la liste des autres agences

---

# # **8. Sécurité UI (DOC-008 Compliance)**

Règles :

* cookies HttpOnly
* aucune donnée sensible dans localStorage
* pas de tokens OAuth dans UI
* strict CSP headers
* sanitisation inputs
* `escapeHTML()` obligatoire dans composants internes
* rate limiting sur endpoints sensibles

Superadmin UI doit être **protégée par IP filtering**.

---

# # **9. Multi-Tenant UI Isolation**

### Obligatoire :

* un utilisateur ne voit QUE les données de son `org_id`
* aucun champ UI ne doit permettre de passer `org_id` manuellement
* chaque requête API joint automatiquement `org_id` depuis le JWT

### Interdit :

* dropdown list d’agences visibles pour org_operator
* affichage des quotas globaux multi-agences

### Superadmin uniquement :

* page /multi-org-dashboard
* /system/metrics
* /system/jobs

---

# # **10. Performance UI (DOC-007 alignment)**

* lazy loading
* infinite scroll
* batching des appels API
* cache SWR / react-query
* pagination obligatoire
* éviter le rendu de +500 objets simultanés

---

# # **11. Anti-Patterns UI (interdits)**

### ❌ 1. Logique métier dans l’UI

### ❌ 2. org_id passé dans les payloads client

### ❌ 3. afficher des tokens externes

### ❌ 4. appeler des endpoints internes non documentés

### ❌ 5. mettre du try/catch silencieux

### ❌ 6. cacher des erreurs backend

### ❌ 7. générer une charge excessive (polling intensif)

---

# # **12. Tests obligatoires**

## **12.1. Unit tests**

* components
* RBAC front
* validations UI
* redirections auth

## **12.2. Integration tests**

* appels API simulés
* isolation tenant testée
* permissions testées

## **12.3. E2E tests (Playwright)**

* workflows d’une agence
* tests connecteurs
* tests scheduler
* tests superadmin

---

# # **13. CI/CD — Admin Panel Compliance**

### 🚫 Bloquant :

* role non vérifié
* accès UI à des routes non conformes
* org_id présent dans un payload
* affichage d’un secret/token
* contournement RBAC
* composant UI accédant directement à storage ou DB
* absence de tests E2E pour pages critiques

### ⚠ Warning :

* API non typée dans lib/api
* absence de middleware auth
* composants non isolés

---

# # **14. Checklist finale SRE++ Admin Panel**

* [ ] aucune logique métier dans l’UI
* [ ] RBAC complet appliqué
* [ ] org_id jamais passé depuis le client
* [ ] isolation tenant respectée
* [ ] page superadmin sécurisée
* [ ] aucune donnée sensible affichée
* [ ] composants UI typés strictement
* [ ] appels API centralisés
* [ ] logs UI → backend avec request_id
* [ ] tests E2E complets
* [ ] monitoring UI (latence / erreurs)

---

# # **15. Conclusion**

DOC-011 établit l’architecture **officielle** du panneau d’administration Sparkmetriq.

Il garantit :

* une UI sécurisée,
* isolée par tenant,
* performante,
* conforme aux contraintes SRE++,
* découplée proprement du backend,
* adaptée aux modules S2 / S3 / S4,
* et compatible avec la multi-startup architecture (DOC-YY).

> Toute violation de DOC-011 bloque la PR.

--
