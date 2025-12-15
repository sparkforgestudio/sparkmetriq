Voici **DOC-SC-014 — UnifiedPostPayload & Cross-Platform Schema Contract**, version **longue**, exhaustive, formelle, cohérente avec S2, SaasentialCore, et toute la série SC (001 → 013).

Ce document définit **le data model standardisé** permettant à Sparkmetriq S2 de supporter toutes les plateformes (Instagram, TikTok, Threads, Snapchat, X/Twitter, Reddit, Facebook, OnlyFans, Telegram...).
Il garantit une **normalisation totale**, une **compatibilité multi-produit**, une **vérification stricte**, et une **évolution contrôlée** via SemVer (DOC-SC-007).

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-014_unified_post_payload_cross_platform_schema_contract.md
```

---

# 📘 `DOC-SC-014_unified_post_payload_cross_platform_schema_contract.md`

````markdown
---
title: DOC-SC-014 — UnifiedPostPayload & Cross-Platform Schema Contract
version: 1.0
status: Stable
category: SaasentialCore / Sparkmetriq S2 / Data Model / API Contract
last_updated: 2025-02-17
---

# 1. Objectif du document

DOC-SC-014 définit :

- le **modèle de données unifié** pour la publication multi-plateformes,
- les invariants obligatoires du UnifiedPostPayload,
- les sous-schemas spécifiques par plateforme,
- les règles de validation,
- les règles versioning (DOC-SC-007),
- la compatibilité avec Scheduler, Dispatcher, Workers, Connectors,
- l’isolation tenant (DOC-SC-004),
- l’intégration API (DOC-003),
- les événements (DOC-SC-006),
- l’observabilité (DOC-SC-009).

Ce schéma est le **contrat technique** garantissant que tous les connecteurs fonctionnent de manière cohérente.

---

# 2. Principes fondamentaux

## ✔ 2.1. Unifié, mais extensible  
Le schéma doit être commun, mais chaque plateforme peut définir ses champs spécifiques.

## ✔ 2.2. Immutable Input Contract  
Une fois reçu par l’API, un UnifiedPostPayload :

- ne peut plus être modifié,
- est versionné,
- sert de base pour toutes les étapes du pipeline S2.

## ✔ 2.3. Backward-compatible  
Toute évolution doit suivre SemVer (DOC-SC-007) :  
- ajout de champs = MINOR  
- modification ou suppression = MAJOR  

## ✔ 2.4. Plateforme-agnostique  
Le cœur du schéma ne doit dépendre d’aucune plateforme.

## ✔ 2.5. Tenant-aware  
Le payload doit transporter les identifiants tenant (startup, org) ou être enrichi par DI.

---

# 3. Spécification complète du UnifiedPostPayload (UPP)

## 3.1. Structure principale

```json
{
  "post_id": "uuid",
  "product_id": "sparkmetriq",
  "startup_id": "stp_1",
  "org_id": "org_22",
  "platforms": ["instagram", "tiktok"],
  "schedule": {
    "type": "exact",
    "timestamp": "2025-02-17T13:00:00Z"
  },
  "media": [
    {
      "type": "image",
      "url": "https://cdn.sparkmetriq.com/media/x.jpg",
      "alt_text": "optional"
    }
  ],
  "caption": {
    "text": "Your quest for perfection ends here!",
    "hashtags": ["#ai", "#model", "#sparkmetriq"],
    "mentions": ["@melissa4musai"]
  },
  "settings": {
    "instagram": { ... },
    "tiktok": { ... },
    "threads": { ... }
  },
  "metadata": {
    "payload_version": "1.0",
    "trace_id": "xyz-111",
    "created_at": "2025-02-17T11:02:00Z"
  }
}
````

---

# 4. Champs obligatoires

| Champ                      | Description                             |
| -------------------------- | --------------------------------------- |
| `post_id`                  | Identifiant unique du contenu           |
| `product_id`               | Produit consommateur (ex : sparkmetriq) |
| `startup_id`               | Tenant startup                          |
| `org_id`                   | Tenant org                              |
| `platforms`                | Liste plateformes ciblées               |
| `schedule`                 | Informations de planification           |
| `media`                    | Liste des médias                        |
| `caption.text`             | Caption principale                      |
| `metadata.payload_version` | Version du schéma                       |

**Interdit de publier un post sans :**

* post_id,
* tenant,
* media,
* plateforme,
* version du schéma.

---

# 5. Schéma de planification

Supporte trois modes :

```json
{
  "type": "exact",        // exécution à timestamp exact
  "timestamp": "2025-02-17T13:00:00Z"
}
```

```json
{
  "type": "immediate"     // publication immédiate
}
```

```json
{
  "type": "window",       // fenêtre de publication
  "start": "...",
  "end": "..."
}
```

Règles :

* scheduler doit rejeter tout payload contenant une fenêtre illogique,
* immediate passe directement à l’étape RESERVED (DOC-SC-013).

---

# 6. Spécification des médias

## 6.1. Champs communs

```json
{
  "type": "image" | "video",
  "url": "<public-media-storage-url>",
  "alt_text": "optional",
  "width": 1080,
  "height": 1350,
  "duration": 15   // video only
}
```

### Interdictions :

* ❌ media inline base64
* ❌ media privés non accessibles par worker
* ❌ media non prétraités (voir DOC-SC-020)

---

# 7. Caption & Branding

```json
{
  "text": "Your quest for perfection ends here!",
  "hashtags": ["#sparkmetriq"],
  "mentions": ["@melissa4musai"]
}
```

Règles :

* hashtags max 30 (Instagram limitation)
* mentions doivent être valides selon plateforme
* text max 2 200 chars (Instagram)

---

# 8. Sections spécifiques par plateforme (Platform Extensions)

## 8.1. Instagram

```json
"instagram": {
  "disable_comments": false,
  "location": "Dubai",
  "tags": ["fashion", "ai"],
  "is_reel": false
}
```

## 8.2. TikTok

```json
"tiktok": {
  "sound": "original",
  "allow_duet": true,
  "allow_stitch": true
}
```

## 8.3. Threads

```json
"threads": {
  "reply_control": "everyone"
}
```

## 8.4. X/Twitter

```json
"twitter": {
  "thread_mode": false,
  "alt_text_enabled": true
}
```

## 8.5. Reddit

```json
"reddit": {
  "subreddit": "AIGirls",
  "nsfw": true
}
```

## 8.6. OnlyFans

```json
"onlyfans": {
  "locked": false,
  "price": 5.99
}
```

**Important :**

Chaque plateforme peut évoluer sans casser le schéma global (MINOR).

---

# 9. Validation Rules (Hard Rules)

## 9.1. Payload global

* `media` non vide
* `platforms` non vide
* `caption.text` non vide
* `schedule.type` valide
* URL media valide
* version du schéma valide

## 9.2. Par plateforme

Chaque connecteur valide ses contraintes :

Ex TikTok :

```
duration <= 180s
aspect ratio valid
```

Ex Instagram :

```
width >= 320
height >= 320
```

Ex OnlyFans :

```
price > 0 si locked == true
```

---

# 10. Intégration Scheduler (DOC-SC-013)

Le scheduler :

* valide le timestamp,
* réserve quota,
* enrichit payload avec trace_id,
* génère un job par plateforme,
* émet `s2.post.scheduled`.

---

# 11. Intégration Dispatcher

Le dispatcher :

* prend chaque job plateforme,
* applique les règles de fairness,
* push vers worker approprié,
* émet `s2.post.dispatched`.

---

# 12. Worker Execution Rules

Le worker :

* récupère le media depuis URL,
* applique transformations (DOC-SC-020),
* construit payload connector,
* appelle l’API plateforme,
* émet :

  * `s2.post.published` (success)
  * `s2.post.failed` (error)

---

# 13. Versioning du UnifiedPostPayload (DOC-SC-007)

La version du schéma doit être incluse :

```json
"payload_version": "1.0"
```

## 13.1. MAJOR

* changement incompatible du schéma principal
* suppression de champ
* changement structurel planification

## 13.2. MINOR

* ajout de champs optionnels
* ajout de plateformes
* ajout metadata

## 13.3. PATCH

* correction de bugs de validation
* documentation

---

# 14. Observabilité (DOC-SC-009)

Le payload doit inclure :

* trace_id
* tenant metadata
* product_id

### Logging obligatoire :

* lors réception API
* lors scheduling
* lors dispatch
* lors publication
* lors erreur

### Metrics :

* `s2_posts_scheduled_total`
* `s2_posts_published_total`
* `s2_payload_validation_failed_total`

---

# 15. CI/CD Compliance Rules

### 🚫 Bloquant

* schéma non versionné
* champs sensibles du tenant dans payload
* media inline base64
* plateforme inconnue sans manifest
* job créé sans validation payload
* backward incompatibilité non déclarée
* modification silent du schéma principal

### ⚠ Warning

* absence de tests pour nouvelle plateforme
* extension plateforme non documentée
* absence d’événements analytics

---

# 16. Invariants non négociables

1. Aucun post ne passe dans S2 sans validation UPP complète.
2. Chaque plateforme doit avoir sa section dédiée optionnelle.
3. Le schéma principal est immutable dans une même version MAJOR.
4. Toutes les évolutions doivent suivre SemVer strict.
5. Aucun secret ne doit apparaître dans le payload.
6. Toute PR violant DOC-SC-014 est bloquée.

---

# 17. Conclusion

DOC-SC-014 constitue la **spécification centrale** du modèle de données Sparkmetriq S2 :

* un schéma unique, extensible, robuste,
* compatible multi-plateformes, multi-produits, multi-startups,
* conforme aux exigences SRE++, sécurité, DI, événements, retries, worker pool, analytics.

C’est l’un des documents les plus critiques du système.


### 👉 **DOC-SC-015 — Worker Lifecycle & Execution Model (RTOS-inspired Contract)**  
