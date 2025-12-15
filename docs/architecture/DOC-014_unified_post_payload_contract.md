Voici **DOC-014 — UnifiedPostPayload & Cross-Platform Schema Contract (S2 Data Model Deep Spec)**
Version longue (10–18 pages), format Markdown, intégrable dans :

```
docs/architecture/DOC-014_unified_post_payload_contract.md
```

Ce document formalise *le cœur structurel* de Sparkmetriq S2 :
le **payload universel** permettant de publier sur toutes les plateformes (Instagram, TikTok, Threads, Snapchat, Reddit, X/Twitter, Facebook, OnlyFans…).

Il garantit :

* cohérence cross-platform,
* validation stricte,
* compatibilité scheduler/dispatcher/workers,
* isolation multi-tenant,
* compatibilité média (DOC-010),
* sécurité (DOC-008),
* observabilité (DOC-006),
* futures extensions S3/S4 (génération IA multimédia).

---

# 📘 **DOC-014 — UnifiedPostPayload & Cross-Platform Schema Contract**

*Document Technique — Sparkmetriq S2 / Data Model & Schema Layer / SRE++*

```markdown
---
title: DOC-014 — UnifiedPostPayload & Cross-Platform Schema Contract
version: 1.0
status: Stable
category: Architecture / Data Model / S2 Schema
last_updated: 2025-02-07
---
```

---

# # **1. Objectif du document**

Sparkmetriq S2 doit publier des contenus sur **toutes les plateformes sociales** via un unique pipeline :

📌 *Planning → Scheduling → Dispatching → Worker → Connector → Platform*

Pour y parvenir, il est indispensable de définir un **schéma universel**, unique, stable et extensible :
**UnifiedPostPayload (UPP)**.

Objectifs :

* unifier toutes les structures API internes
* réduire la complexité du scheduler
* standardiser les connecteurs
* éviter la duplication plateforme × plateforme
* introduire une couche d’abstraction durable
* garantir la validation stricte & SRE++
* permettre les futures extensions multimédia S3/S4
* maintenir backward-compatibility

Ce document définit **le contrat officiel du UnifiedPostPayload** et de tous les sous-schémas associés.

---

# # **2. Périmètre**

S’applique à :

* Scheduler → `/s2/posts/schedule`
* Dispatcher
* Worker S2
* Connecteurs
* `/api/media/upload`
* `products/sparkmetriq/schemas`
* Admin Panel
* Observability logs
* Idempotence (DOC-005)
* Quotas (DOC-004)

Hors périmètre :

* messages privés / DMs (S3)
* contenu IA généré contextuellement (S4)

---

# # **3. Principes fondamentaux (SRE++ / Data Model)**

## ✔ 3.1. Un schéma unique pour toutes les plateformes

L’UPP contient les **attributs communs**, plus une section `platform_options` pour la personnalisation.

## ✔ 3.2. InputModel ≠ InternalModel ≠ ResponseModel

Conformité DOC-003.

## ✔ 3.3. Les champs obligatoires ne dépendent jamais d’une plateforme

Même TikTok ou Instagram utilisent la même colonne vertébrale.

## ✔ 3.4. Le payload doit être entièrement validé dans l’API (pas dans scheduler)

→ le scheduler fait confiance au payload validé.

## ✔ 3.5. Chaque payload doit être idempotent (DOC-005)

→ hash du contenu + timestamp.

## ✔ 3.6. Multi-tenant enforced (DOC-009)

→ `org_id` jamais fourni par le client, uniquement par JWT.

---

# # **4. UnifiedPostPayload — Spécification principale**

Voici le schéma **officiel** :

```python
class UnifiedPostPayload(BaseModel):
    platform: Literal["instagram", "tiktok", "threads", "facebook", "twitter", "reddit", "snapchat", "onlyfans"]
    account_id: str  # ID interne du compte social lié à org_id
    scheduled_at: datetime  # UTC ISO 8601
    caption: Optional[str]
    media: List[MediaItem]  # DOC-010 compliance
    platform_options: Optional[PlatformOptions]
    idempotency_key: Optional[str]  # auto-généré si absent
    metadata: Optional[Dict[str, Any]]  # AI context, tracking
```

---

# # **5. Sous-schéma : MediaItem (DOC-010 integration)**

Chaque média appartient à un seul tenant → **multi-tenant isolation enforced**.

```python
class MediaItem(BaseModel):
    media_id: str  # issu de /api/media/upload
    type: Literal["image", "video"]
    alt_text: Optional[str]
    position: Optional[int]  # ordre (carrousels)
```

Règles :
✔ media_id doit exister
✔ org_id du média == org_id du JWT
✔ type déterminé par ACL Media
✔ thumbnails et vidéo-transcoding via workers (DOC-010)

---

# # **6. Sous-schéma : PlatformOptions (spécifique plateforme)**

Le modèle complet :

```python
class PlatformOptions(BaseModel):
    instagram: Optional[InstagramOptions]
    tiktok: Optional[TikTokOptions]
    threads: Optional[ThreadsOptions]
    reddit: Optional[RedditOptions]
    twitter: Optional[TwitterOptions]
    snapchat: Optional[SnapchatOptions]
    onlyfans: Optional[OnlyFansOptions]
```

---

# # **7. Détails par plateforme**

---

## **7.1. InstagramOptions**

```python
class InstagramOptions(BaseModel):
    is_reel: bool = False
    location_id: Optional[str]
    tags: Optional[List[str]]
    product_tags: Optional[List[ProductTag]]
```

Règles :

* reels → vidéos uniquement
* product_tags doivent être validés
* tags max = 20

---

## **7.2. TikTokOptions**

```python
class TikTokOptions(BaseModel):
    sound_id: Optional[str]
    visibility: Literal["public", "private", "friends"] = "public"
    allow_comments: bool = True
    allow_stitch: bool = False
    allow_duet: bool = False
```

Règles :

* vidéos obligatoires
* options non utilisées par TikTok ignorées silencieusement

---

## **7.3. ThreadsOptions**

```python
class ThreadsOptions(BaseModel):
    reply_settings: Literal["everyone", "profiles_you_follow"] = "everyone"
```

---

## **7.4. TwitterOptions**

```python
class TwitterOptions(BaseModel):
    sensitive: bool = False
    reply_limit: Literal["everyone", "followers", "mentioned"] = "everyone"
```

---

## **7.5. RedditOptions**

```python
class RedditOptions(BaseModel):
    subreddit: str
    flair_id: Optional[str]
    nsfw: bool = False
```

---

## **7.6. OnlyFansOptions**

```python
class OnlyFansOptions(BaseModel):
    price: Optional[float]  # PPV
    expire_at: Optional[datetime]
    is_ppv: bool = False
```

---

# # **8. Génération & Validation de l’idempotency_key (DOC-005)**

L’idempotence est obligatoire.

Si le client ne fournit pas `idempotency_key`, Sparkmetriq génère :

```
idempotency_key = sha256(
    org_id +
    account_id +
    platform +
    scheduled_at +
    media_hash +
    caption_trimmed
)
```

---

# # **9. Champs obligatoires vs optionnels**

| Champ            | Obligatoire ? | Notes                          |
| ---------------- | ------------- | ------------------------------ |
| platform         | ✔             | valeurs strictes               |
| account_id       | ✔             | validé par org_id              |
| scheduled_at     | ✔             | UTC                            |
| media            | conditionnel  | Instagram/TikTok = obligatoire |
| caption          | optionnel     | plateformes textuelles         |
| platform_options | optionnel     | schémas extensibles            |
| metadata         | optionnel     | utile S3/S4                    |
| idempotency_key  | auto          | obligatoire au final           |

---

# # **10. Règles transverses (toutes plateformes)**

### ✔ 10.1. scheduled_at doit être dans le futur

juste marge de sécurité : 5 secondes.

---

### ✔ 10.2. caption normalisée

* trim
* no HTML
* taille max par plateforme appliquée automatiquement

---

### ✔ 10.3. media validation

* résolution max (varie selon plateforme)
* ratio
* poids max
* format accepté

ACL Media (DOC-010) réalise cette validation.

---

### ✔ 10.4. multi-tenant enforcement

Un worker doit refuser si :

```
job.org_id != media.org_id
```

---

# # **11. Versionnement du schéma et compatibilité**

Le schéma UPP est versionné :

```
v1 : 2025 (stable)
v2 : +carrousels avancés, +live support, +tags améliorés
v3 : +stories, +ads boost
```

Backward compatibility :
toute évolution doit être additive.

---

# # **12. Observabilité (DOC-006 compliance)**

Le scheduler et les workers doivent logguer :

```json
{
  "event": "unified_post_payload",
  "org_id": "...",
  "platform": "instagram",
  "media_count": 3,
  "has_options": true,
  "idempotency_key": "..."
}
```

---

# # **13. Invariants (non négociables)**

1. **Aucun job S2 n’existe sans UPP valide**
2. **Tous les média doivent être conformes ACL Media**
3. **UPP ne contient jamais org_id (venant client)**
4. **UPP doit permettre un publish sur plusieurs plateformes sans duplication de code**
5. **IDEMPOTENCY_KEY est obligatoire** (DOC-005)
6. **UPP ne doit jamais exposer les tokens fournisseurs**

---

# # **14. Tests obligatoires**

## 14.1. Unit tests

* validation multi-plateforme
* validation cross-platform options
* caption processing
* idempotence generation

## 14.2. Integration tests

* UPP → scheduler
* UPP → dispatcher
* UPP → connector translation

## 14.3. E2E tests

* post unique avec carrousel
* cross-platform publish → succès
* double submit → une seule publication

---

# # **15. CI/CD Compliance**

### 🚫 Blocages :

* champ manquant dans UPP
* org_id provenant du client
* media invalides
* options non conformes
* absence idempotency_key
* worker utilisant payload brut sans validation

### ⚠ Warnings :

* options plateforme inutilisées
* caption trop longue

---

# # **16. Checklist finale SRE++ UnifiedPostPayload**

* [ ] UPP complet, validé par Pydantic
* [ ] options plateformes respectées
* [ ] idempotency_key généré
* [ ] media ACL compliant
* [ ] aucun cross-tenant
* [ ] scheduler & dispatcher intégrés
* [ ] worker compatible
* [ ] observabilité complète
* [ ] tests E2E OK
* [ ] CI/CD validé

---

# # **17. Conclusion**

DOC-014 formalise **le schéma universel le plus critique de Sparkmetriq S2**.
Il garantit :

* stabilité du système,
* facilité d’intégration multi-plateforme,
* cohérence data end-to-end,
* sécurité,
* idempotence,
* lisibilité pour toute l’équipe,
* compatibilité avec le growth du produit.

> **Aucun job ne doit être accepté par Sparkmetriq sans conformité totale à DOC-014.**

---
