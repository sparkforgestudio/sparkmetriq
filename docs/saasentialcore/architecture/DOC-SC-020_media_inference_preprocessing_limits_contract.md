Parfait — j’intègre **DOC-SC-020** **sans aucune référence à S3/S4**, de manière **agnostique produit**, **agnostique startup**, et **LLM-first générique**, applicable à **toute startup** exploitant des modèles IA (vision, audio, texte, multimodal) sur SaasentialCore.

Ce document devient donc un **contrat transverse du socle**, au même niveau que Secrets, Workers ou Gateway.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-020_media_inference_preprocessing_limits_contract.md
```

---

# 📘 `DOC-SC-020_media_inference_preprocessing_limits_contract.md`

````markdown
---
title: DOC-SC-020 — Media Inference & Preprocessing Limits Contract
version: 1.0
status: Stable
category: SaasentialCore / AI / Media / Inference / Performance / Security
last_updated: 2025-02-18
---

# 1. Objectif du document

DOC-SC-020 définit le **contrat universel de préparation, validation et exécution des médias et données d’inférence IA** dans SaasentialCore.

Il s’applique à :
- toutes les startups utilisant des **LLM**,
- tous les produits manipulant des **médias** (image, vidéo, audio, texte),
- tous les workers d’inférence,
- tous les pipelines IA (classification, génération, scoring, analyse, enrichment).

Ce document garantit :
- stabilité runtime,
- protection des ressources,
- prévisibilité des coûts,
- sécurité des entrées IA,
- compatibilité multi-modèles,
- scalabilité industrielle.

---

# 2. Principes fondamentaux

## ✔ 2.1. Toute entrée IA est hostile par défaut  
Aucune donnée fournie à un modèle n’est considérée sûre.

## ✔ 2.2. Préprocessing obligatoire  
Aucune donnée brute n’est envoyée à un modèle sans validation préalable.

## ✔ 2.3. Resource bounded inference  
Toute exécution IA doit être **bornée** en :
- temps,
- mémoire,
- taille d’entrée,
- coût estimé.

## ✔ 2.4. Modèle-agnostique  
Le contrat s’applique **indépendamment du fournisseur** :
- OpenAI
- Anthropic
- Mistral
- DeepSeek
- LLaMA
- modèles open-weight on-prem
- modèles multimodaux custom

---

# 3. Typologie des entrées IA

| Type | Exemples |
|----|---------|
| Texte | prompt, conversation, transcript |
| Image | JPEG, PNG |
| Vidéo | MP4, MOV |
| Audio | WAV, MP3 |
| Multimodal | image + texte |
| Métadonnées | tags, scores, context |

Chaque type possède **des limites strictes**.

---

# 4. Pipeline canonique de préprocessing

```mermaid
flowchart LR
    Input --> Validation
    Validation --> Normalization
    Normalization --> Compression
    Compression --> SecurityScan
    SecurityScan --> Inference
    Inference --> PostProcessing
````

Aucune étape ne peut être sautée.

---

# 5. Validation des entrées (Hard Gate)

## 5.1. Validation structurelle

* format valide
* MIME correct
* encodage supporté
* schéma JSON valide (si texte structuré)

Entrée invalide → **rejet immédiat**.

---

## 5.2. Validation de taille (obligatoire)

### Texte

* max tokens (ex : 8k / 16k / configurable)
* max caractères
* profondeur JSON max

### Image

* dimensions max (ex : 4096x4096)
* poids max (ex : 10MB)

### Vidéo

* durée max (ex : 120s)
* résolution max
* bitrate max

### Audio

* durée max
* fréquence max

Dépassement → **rejet** ou **downscale contrôlé**.

---

# 6. Normalisation & Compression

## 6.1. Normalisation

* encodage UTF-8
* nettoyage caractères invalides
* stripping metadata dangereuses (EXIF, GPS)
* harmonisation formats

## 6.2. Compression contrôlée

Objectif :

* réduire coût inference
* réduire latence
* préserver signal utile

Exemples :

* resize image
* downsample audio
* trimming texte inutile

---

# 7. Sécurité & IA Safety

## 7.1. Prompt Injection Protection

Les entrées texte doivent être :

* séparées en **instructions système / utilisateur / contexte**
* nettoyées des patterns dangereux
* encapsulées (delimiters)

---

## 7.2. Contenu malveillant

Détection obligatoire :

* payloads trop répétitifs
* patterns DoS
* encodage malveillant
* contenu binaire déguisé

---

# 8. Modèle d’exécution Inference

## 8.1. Inference Context

Chaque exécution IA possède un contexte isolé :

```json
{
  "inference_id": "...",
  "startup_id": "...",
  "org_id": "...",
  "product_id": "...",
  "model_id": "...",
  "input_size": "...",
  "estimated_cost": "...",
  "timeout": "..."
}
```

---

## 8.2. Timeouts obligatoires

| Type  | Timeout      |
| ----- | ------------ |
| Texte | 30s          |
| Image | 45s          |
| Vidéo | 120s         |
| Batch | configurable |

Timeout dépassé → **abort**.

---

# 9. Resource Bounding

Chaque worker IA doit imposer :

* limite mémoire par inference
* limite CPU / GPU
* limite concurrente par tenant
* limite coût estimé

Violation → **FAIL FAST**.

---

# 10. Batch Inference Rules

Le batch est autorisé si :

* inputs homogènes,
* tenant identique,
* modèle identique,
* limite batch size respectée.

Batch cross-tenant → **interdit**.

---

# 11. Post-Processing

Après inference :

* validation sortie
* trimming sortie
* normalisation format
* filtrage contenu sensible
* scoring qualité

La sortie **n’est jamais retournée brute**.

---

# 12. Observabilité IA (obligatoire)

## Logs

```json
{
  "event": "ai.inference",
  "model_id": "llama-70b",
  "input_tokens": 4231,
  "output_tokens": 512,
  "latency_ms": 1840,
  "tenant": "...",
  "trace_id": "..."
}
```

Jamais :

* contenu brut
* prompts complets
* outputs complets

---

## Metrics

* `ai_inference_total`
* `ai_inference_latency_seconds`
* `ai_inference_timeout_total`
* `ai_tokens_in_total`
* `ai_tokens_out_total`
* `ai_cost_estimated`

---

# 13. Multi-Tenant Isolation

Règles strictes :

* aucune mutualisation d’état
* aucun cache partagé cross-tenant
* aucune mémoire persistante cross-inference
* aucun modèle personnalisé partagé sans contrat explicite

---

# 14. CI/CD Compliance Rules

### 🚫 Bloquant

* inference sans validation
* inference sans timeout
* inference sans resource limits
* input non nettoyé
* logs contenant prompt/output
* inference cross-tenant
* modèle non déclaré

### ⚠ Warning

* absence estimation coût
* absence métriques
* absence stress tests

---

# 15. Invariants non négociables

1. Aucune inference sans préprocessing.
2. Aucune inference sans limites.
3. Aucune inference cross-tenant.
4. Aucun contenu brut dans logs.
5. Toute entrée IA est traitée comme hostile.
6. Toute violation bloque la PR.

---

# 16. Conclusion

DOC-SC-020 est le **contrat de sécurité, performance et stabilité de toute IA** opérant sur SaasentialCore.

Il permet :

* intégration de n’importe quel LLM,
* contrôle des coûts,
* sécurité des entrées,
* stabilité des workers,
* passage à l’échelle multi-startup,
* industrialisation réelle de l’IA.

C’est un **pilier transversal**, indépendant de tout produit spécifique.

