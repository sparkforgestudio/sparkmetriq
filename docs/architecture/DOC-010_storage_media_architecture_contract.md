Voici **DOC-010 — Storage & Media Architecture Contract (Version longue, 8–14 pages)**, au format Markdown technique, conçu pour assurer une architecture robuste, isolée, performante et évolutive du stockage média de Sparkmetriq.

Prêt à être placé dans :

```
docs/architecture/DOC-010_storage_media_architecture_contract.md
```

Il inclut :

* Media Pipeline Sparkmetriq complet
* Anti-Corruption Layer (ACL) entre DB / CDN / API / Worker
* Sécurité & isolation multi-tenant
* Storage tiers (OVH, S3, Backblaze)
* CDN Edge optimisé
* Compression, hashing, signatures, métadonnées
* Règles SRE++ & CI/CD

---

# 📘 **DOC-010 — Storage & Media Architecture Contract (Version longue)**

*Document Technique de Référence — Sparkmetriq Storage / Media Pipeline / Anti-Corruption Layer (ACL)*

```markdown
---
title: DOC-010 — Storage & Media Architecture Contract
version: 1.0
status: Stable
category: Architecture / Storage / Media / SRE++
last_updated: 2025-02-03
---
```

---

# # **1. Objectif du document**

Sparkmetriq S2/S3/S4 manipule :

* images générées,
* vidéos,
* miniatures,
* médias compressés pour connecteurs (Instagram, TikTok…),
* médias pré-traités (AI generation, upscaling),
* archives,
* logs multimédia,
* médias uploadés via `/api/media/upload`.

Ce document définit le **contrat d’architecture media & storage**, incluant :

* pipeline complet du media,
* anti-corruption layer (ACL) pour éviter dépendance directe entre services,
* isolation multi-tenant (DOC-009),
* optimisation CDN/edge,
* compression & hashing,
* métadonnées structurées,
* règles SRE++ pour performance, sécurité et fiabilité.

Ce contrat est obligatoire pour toute fonctionnalité manipulant des médias.

---

# # **2. Périmètre**

S’applique à :

* `/api/media/upload`
* `/api/media/files/{id}`
* Worker Celery media operations
* Génération IA dans S3/S4
* Upload vers connecteurs
* Stockage (local, S3, OVH Object Storage)
* CDN (Cloudflare / OVH CDN)
* Pre-processing & validation
* Media metadata DB
* Multi-tenant isolation
* Anti-Corruption Layer

---

# # **3. Architecture générale — Media Pipeline Diagram**

```mermaid
flowchart LR
A[Client Upload] --> B[FastAPI Upload Endpoint]
B --> C[Anti-Corruption Layer - MediaService]
C --> D[Storage Provider (S3/OVH/Local)]
C --> E[MongoDB Metadata Store]
E --> F[CDN Edge Cache]
C --> G[Workers Celery - Preprocessing]
```

---

# # **4. Anti-Corruption Layer (ACL) — Obligatoire**

## Pourquoi ?

Pour éviter que les services :

* accèdent directement au storage,
* manipulent les formats bruts,
* créent des dépendances dures,
* exposent aux connecteurs des fichiers non sécurisés.

## Rôle de l’ACL MediaService :

* validation du fichier
* hashing & signature
* génération d’ID unique
* compression / conversion
* authentification tenant
* interaction abstraite avec storage provider
* mise à jour de la metadata DB
* règles d’expiration & lifecycle
* gestion CDN

**Tous les modules doivent passer par cette ACL.**

---

# # **5. Flux de téléchargement (upload)**

Étapes obligatoires :

### 5.1. Réception du fichier

* via `multipart/form-data`
* limite : 25 MB par fichier (configurable)
* scanning extension → MIMETYPE

### 5.2. Validation SRE++

* type autorisé (`image/jpeg`, `image/png`, `video/mp4`, etc.)
* taille max respectée
* checksum avant upload
* pas de virus scan (option futur)

### 5.3. Hashing

```
sha256(file) → file_hash
```

### 5.4. Création ID interne

Ex:

```
media_id = "m_" + uuid4()
```

### 5.5. Stockage via Provider (S3/OVH)

Chemin standardisé :

```
/{org_id}/{media_id}/{filename}
```

### 5.6. Création metadata DB

```json
{
  "_id": "m_123",
  "org_id": "org_77",
  "hash": "<sha256>",
  "size_bytes": 402300,
  "extension": "jpg",
  "mime_type": "image/jpeg",
  "storage_path": "...",
  "created_at": "...",
  "used_in": ["post_abc123"]
}
```

---

# # **6. Multi-tenant isolation (DOC-009 compliance)**

### 6.1. Un fichier appartient à un seul tenant

```
media.org_id
```

### 6.2. Le storage path inclut org_id

Interdit :

```
/uploads/global/
```

Correct :

```
/tenant_uploads/{org_id}/file
```

### 6.3. Les workers doivent vérifier org_id

Aucun accès cross-tenant autorisé.

### 6.4. Le CDN ne doit jamais exposer le chemin complet

Préférer :

```
/cdn/{media_id}
```

---

# # **7. Storage Provider Standard (abstraction)**

Sparkmetriq doit supporter :

* OVH Object Storage
* AWS S3
* Local filesystem (dev only)
* Cloudflare R2 (futur)

L’ACL MediaService encapsule le provider :

```python
class StorageProvider(Protocol):
    async def upload(self, path: str, file: bytes) -> str: ...
    async def download(self, path: str) -> bytes: ...
    async def delete(self, path: str) -> None: ...
```

---

# # **8. CDN Standard (Edge Delivery)**

## 8.1. URLs signées (Signed URLs)

Durée de validité : **15 minutes**

Empêche :

* hotlinking
* accès non autorisé
* scraping massif

---

## 8.2. Compression edge

Formats recommandés :

* **JPEG-XL** (convert optionnel workers)
* **WebP** (fallback)
* MP4 H.264 baseline (90% compatibilité)

---

## 8.3. Cache-Control

```
Cache-Control: public, max-age=86400
```

---

## 8.4. Purge automatique

Lorsqu’un fichier est supprimé → purge CDN.

---

# # **9. Workers Media Processing**

Actions possibles :

* compression
* resizing
* thumbnail generation
* conversion format
* video transcoding (ffmpeg wrapper)
* safe-cropping (S3/S4)
* AI content injection (S3/S4)

### Règles :

* workers doivent être **stateless**
* tous les outputs doivent passer par ACL
* aucun worker ne peut écrire dans storage directement

---

# # **10. Storage Lifecycle Policy**

Niveaux :

### 10.1. Active media

Pour les fichiers utilisés dans des publications récentes.

### 10.2. Warm storage (30+ jours)

Compression supplémentaire possible.

### 10.3. Archive storage (90+ jours)

Coût faible (OVH Cold Storage ou Glacier-like futur).

### 10.4. Deletion policy (6–12 mois)

Selon abonnement client.

---

# # **11. Sécurité Storage**

### ✔ encryption-at-rest obligatoire

Volumes OVH chiffrés.

### ✔ encryption per tenant (option enterprise)

Clés distinctes.

### ✔ aucun token storage ne doit être exposé

Pas dans logs, pas dans frontend.

### ✔ signed URLs uniquement

Les URL publiques sont interdites.

---

# # **12. CDN Anti-Abuse Measures**

* limite de débit par IP
* signature obligatoire
* watermarking optionnel
* réponse 404 pour media d’un autre tenant
* logs tenant-scopés (DOC-006)

---

# # **13. Contrat API pour `/api/media/*`**

## 13.1. Upload endpoint

**Réponse doit contenir :**

```json
{
  "media_id": "m_123",
  "cdn_url": "https://cdn.sparkmetriq.com/m_123?sig=...",
  "mime_type": "image/jpeg",
  "width": 1024,
  "height": 768
}
```

### Jamais :

* stocker le fichier dans MongoDB
* renvoyer du base64 (sauf cas spécifiques)

---

# # **14. Tests obligatoires**

## 14.1. Unit tests

* validation MIME
* hashing
* path isolation
* abstraction storage provider

## 14.2. Integration tests

* upload + get + delete
* CDN signed URL
* isolation tenant

## 14.3. E2E Tests

* upload → planification → publication (Instagram/TikTok)
* worker preprocessing chain
* failure rollback (networks, storage unavailable)

---

# # **15. CI/CD — Compliance Rules**

### 🚫 Bloquant

* accès direct au filesystem en production
* URL non signées
* media sans org_id
* metadata incomplète
* worker écrivant directement dans storage
* expose real storage path dans API
* pas de hashing sha256

### ⚠ Warning

* fichiers trop gros non compressés
* absence thumbnail
* absence tests de charge storage

---

# # **16. Checklist finale SRE++ Media**

* [ ] ACL MediaService utilisé partout
* [ ] stockage abstrait via provider
* [ ] signed URLs obligatoires
* [ ] org_id dans storage path
* [ ] workers stateless
* [ ] pas de filesystem direct
* [ ] validation MIME stricte
* [ ] hashing SHA256
* [ ] metadata Mongo propre
* [ ] CDN edge activé
* [ ] tests multi-tenant OK
* [ ] CI/CD compliant

---

# # **17. Conclusion**

DOC-010 définit le cadre officiel et obligatoire pour :

* la gestion complète des médias,
* la robustesse du système,
* l'isolation tenant,
* l’intégration SaaS professionnelle,
* la conformité SRE++,
* la performance CDN,
* la préparation de S3/S4 (IA multimédia avancée).

> Toute violation de DOC-010 bloque la PR.

---
