Voici **DOC-020 — Media Inference & Preprocessing Limits**, version longue (12–18 pages), conçu pour établir **le contrat officiel de préparation média**, couvrant :

* pré-processing pour Sparkmetriq S2,
* pipeline IA pour S3 (génération multimodale),
* pipeline enrichi pour S4 (context-aware intent engine),
* limites de performance,
* contraintes de sécurité,
* architecture multi-tenant,
* pipeline GPU/CPU futur.

Ce document est crucial pour assurer la cohérence du pipeline multimédia présent (S2) et futur (S3/S4/MusAI Studio).

À intégrer dans :

```
docs/architecture/DOC-020_media_inference_preprocessing_limits.md
```

---

# 📘 **DOC-020 — Media Inference & Preprocessing Limits**

*Sparkmetriq S2/S3/S4 — Préparation Média, IA Multimodale, Sécurité, Pipeline Temps Réel*

```markdown
---
title: DOC-020 — Media Inference & Preprocessing Limits
version: 1.0
status: Stable
category: Architecture / Media / AI Inference / Preprocessing / Limits
last_updated: 2025-02-12
---
```

---

# # **1. Objectif du document**

Sparkmetriq dépend fortement de la **manipulation de médias** :

* images (S2 → IG, TikTok, Threads…),
* vidéos (S2 reels, TikTok),
* carrousels (multi-images),
* contenus premium (MusAI, OnlyFans),
* contenus IA générés (S3),
* contenus contextualisés dynamiquement (S4).

Ce document définit :

* les **règles de pré-processing média**,
* les **limites physiques et computationnelles**,
* le **pipeline d’inférence IA futur**,
* les **capacités des workers pré-traitement**,
* les **contraintes multi-tenant**,
* la sécurité et la conformité SRE++.

Aucune étape IA ne doit casser la stabilité de S2.
Aucune étape S3/S4 ne doit casser la cohérence tenant.

---

# # **2. Périmètre**

Couvre :

* ingestion média (DOC-010),
* préparation image/vidéo,
* normalisation,
* compression,
* resizing,
* extraction métadonnées (EXIF),
* validation plateforme,
* pré-processing IA pour S3/S4,
* contraintes GPU futures,
* modèles utilisés (upscaling, denoisers, frame-interpolation),
* pipeline sécurisé multi-tenant.

Ne couvre pas :

* génération IA complète (S3),
* génération textuelle S4.

---

# # **3. Architecture générale du pipeline Preprocessing & AI**

```mermaid
flowchart TD
A[Upload Media] --> B[ACL Media Validation (DOC-010)]
B --> C[Preprocessing Worker]
C --> D[Media Normalizer]
D --> E[Platform-Specific Transformer]
E --> F[AI Inference (optional S3/S4)]
F --> G[Optimized Media Output]
G --> H[CDN Storage]
```

---

# # **4. Principes fondamentaux**

## ✔ 4.1. Le pré-processing est **obligatoirement stateless**

Aucun état entre jobs.

## ✔ 4.2. Aucun worker S2 ne doit exécuter de modèle IA lourd

Les modèles IA lourds appartiennent à **S3**.

## ✔ 4.3. Le média source est **immuable**

On ne modifie jamais le fichier original.

## ✔ 4.4. Le média optimisé est un fichier distinct

Stockage :

```
/{org_id}/{media_id}/optimized/{variant}
```

## ✔ 4.5. Multi-tenant isolation stricte (DOC-009)

Aucun worker ne doit accéder à un média d’un autre tenant.

## ✔ 4.6. Le pré-processing doit être déterministe

Pour garantir l'idempotence (DOC-005).

---

# # **5. Capacités obligatoires du Preprocessing Worker**

Le worker doit pouvoir :

### 5.1. Lire le média via Storage Provider

pas de dépendance locale.

### 5.2. Déterminer la nature :

* image
* vidéo (<2 min max pour S2)

### 5.3. Vérifier les capacités plateforme :

Par ex. :

| Plateforme       | Format   | Ratio            | Taille max |
| ---------------- | -------- | ---------------- | ---------- |
| Instagram (feed) | JPEG/MP4 | 1:1, 4:5, 1.91:1 | 8 MB       |
| TikTok           | MP4      | vertical         | 50 MB      |
| Threads          | JPEG     | variable         | 8 MB       |

### 5.4. Appliquer transformations :

#### A — Images

* resize
* crop safe
* compression (WebP, JPEG-XL)
* orientation automatique
* conversion (PNG → JPEG)

#### B — Vidéos

* transcodage
* bitrate normalization
* génération thumbnail
* extraction durée

### 5.5. Vérifier contraintes SRE++ (DOC-017)

* pas de long running (>5s CPU)
* timeout strict
* memory cap

---

# # **6. Limites de Preprocessing (S2)**

Ces limites sont fixées pour éviter surcharge CPU/IO :

### Images :

* résolution max : **4096 x 4096 px**
* poids max upload : **25 MB**
* poids final optimisé : **≤ 8 MB**

### Vidéos :

* durée max : **60 secondes** (TikTok, IG Reels)
* poids max : **50 MB**
* résolution max : **1080p**
* bitrate max : **8 Mbps**

### Temps d’exécution :

* pré-processing image : **≤ 200ms**
* pré-processing vidéo : **≤ 1.5s**

---

# # **7. Variants & Renditions**

Le système génère plusieurs versions du média :

### 7.1. Original (immutable)

Pas d’altération.

### 7.2. Optimized

Version standard destinée aux publications classiques.

### 7.3. Platform-specific variants

Exemple Instagram Reels :

```
1080x1920
h264 baseline
a=44.1k
```

### 7.4. Low-resolution Preview

Utilisé dans Admin Panel.

---

# # **8. Préparation IA (Future S3/S4)**

Lorsque S3 sera déployé, la pipeline acceptera :

### 8.1. AI Fixes

* face retouching
* brightness corrections
* noise removal

### 8.2. AI Upscaling

Modèles :

* Real-ESRGAN
* Stable Diffusion upscalers
* Topaz-style architectures

### 8.3. AI Frame Interpolation (vidéo)

RIFE / FILM / DAIN.

### 8.4. AI Generation overlay

* logos
* stickers
* backgrounds

### 8.5. Embeddings multimodaux (S4)

Extraction :

* CLIP embeddings
* Face embeddings
* Context embeddings

---

# # **9. Contraintes IA S3/S4**

### 9.1. Interdiction d’exécuter IA lourde dans les workers S2

→ Risque de latence + surcharge CPU.

### 9.2. IA lourde doit s’exécuter sur un cluster dédié S3

→ GPU
→ pipeline séparée
→ file d’attente dédiée

### 9.3. Pré-processing IA doit rester **optionnel**

et jamais bloquer la publication.

### 9.4. IA doit être déterministe

→ éviter résultats divergents
→ important pour idempotence

---

# # **10. Multi-Tenant & Multi-Startup Isolation**

Chaque média doit être taggé par :

```
org_id
startup_id (DOC-YY futur)
```

Aucun worker IA ou préprocessing ne doit :

* charger un média hors tenant
* écrire dans un bucket étranger
* lire un secret non associé

---

# # **11. Stockage & CDN (alignement DOC-010)**

Les fichiers optimisés suivent :

```
/org/{org_id}/media/{media_id}/optimized/default.jpg
/org/{org_id}/media/{media_id}/optimized/tiktok.mp4
/org/{org_id}/media/{media_id}/optimized/instagram.jpg
```

URLs **signées** obligatoires.

---

# # **12. Tests obligatoires**

## Unitaires

* resize
* crop
* compression
* video transcoding

## Intégration

* upload → preprocess → storage
* preview generation
* multi-tenant isolation tests

## E2E

* publication IG/TikTok avec preprocessing activé
* playback correct
* stress-test 500 médias → stable

---

# # **13. CI/CD Compliance Rules**

### 🚫 Bloquant :

* worker S2 exécute IA lourde
* transcodage vidéo > 2s
* média modifié sans créer une nouvelle version
* lecture média cross-tenant
* absence de variant platform-required
* absence de timeout transcoding

### ⚠ Warning :

* preview non générée
* metadata EXIF non filtrée
* pas de thumbnail vidéo

---

# # **14. Checklist SRE++**

* [ ] pre-processing déterministe
* [ ] idempotence respectée
* [ ] multi-tenant enforced
* [ ] performance contrôlée
* [ ] IA lourde interdite en S2
* [ ] variants par plateforme générés
* [ ] logging structured
* [ ] CDN integration OK
* [ ] CI/CD compliant
* [ ] pipeline future-proof S3/S4

---

# # **15. Conclusion**

DOC-020 fixe les règles **définitives** pour la préparation média et la future pipeline IA multimodale Sparkmetriq.

Il garantit :

* optimisation,
* compatibilité plateformes,
* scalabilité,
* sécurité,
* conformité multi-tenant,
* préparation technique pour S3/S4.

> Toute PR violant DOC-020 doit être refusée automatiquement.

---
