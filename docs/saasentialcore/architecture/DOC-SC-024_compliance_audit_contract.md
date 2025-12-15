Voici **DOC-SC-024 — Compliance & Audit Contract (Enterprise / SOC2 / ISO Mindset)**,
version **longue**, normative, **orientée clients enterprise, audits externes et investisseurs**, et strictement alignée avec **SC-001 → SC-023**, SRE++, sécurité, FinOps et gouvernance IA.

Ce document n’est **pas une certification** en soi :
c’est le **socle contractuel** qui permet **d’y accéder sans refonte**.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-024_compliance_audit_contract.md
```

---

# 📘 `DOC-SC-024_compliance_audit_contract.md`

````markdown
---
title: DOC-SC-024 — Compliance & Audit Contract
version: 1.0
status: Stable
category: SaasentialCore / Compliance / Audit / Enterprise Readiness
last_updated: 2025-02-18
---

# 1. Objectif du document

DOC-SC-024 définit le **contrat de conformité et d’audit** applicable à l’ensemble de SaasentialCore et des produits qui s’y appuient.

Il établit :
- les **principes de conformité structurelle**,
- les **exigences d’auditabilité technique**,
- les **contrôles internes obligatoires**,
- les **traces requises pour audits externes**,
- l’alignement avec les référentiels **SOC2 / ISO 27001 / ISO 27701 / Enterprise IT**,
- sans rigidité excessive ni bureaucratie inutile.

L’objectif est simple :

> *Être auditable à tout moment, sans stress, sans bricolage de dernière minute.*

---

# 2. Philosophie Compliance SaasentialCore

## ✔ 2.1. Compliance by Design  
La conformité n’est pas ajoutée après coup :  
elle est **codée dans l’architecture**.

## ✔ 2.2. Evidence > Promesses  
Toute règle doit produire :
- des preuves techniques,
- des logs,
- des métriques,
- des documents.

## ✔ 2.3. Least Privilege & Least Data  
Tout accès est minimal :
- en droits,
- en périmètre,
- en durée.

## ✔ 2.4. Audit sans contexte tribal  
Un auditeur externe doit comprendre le système **sans dépendre des développeurs**.

---

# 3. Périmètre de conformité

DOC-SC-024 couvre :

- Core SaasentialCore
- API & Gateway
- Scheduler / Dispatcher
- Workers
- Connecteurs externes
- IA / Inference
- Données (runtime, analytics)
- Admin Panel
- CI/CD
- Secrets & Configuration
- Monitoring & Logs

---

# 4. Axes de conformité couverts

| Axe | Référentiels |
|---|---|
| Sécurité | SOC2 Security / ISO 27001 |
| Disponibilité | SOC2 Availability |
| Confidentialité | SOC2 Confidentiality |
| Intégrité | SOC2 Processing Integrity |
| Vie privée | ISO 27701 / RGPD |
| Traçabilité | Enterprise IT / Audit |

---

# 5. Identity & Access Management (IAM)

## 5.1. Authentification

- Auth centralisée
- JWT signés, expirés, rotatifs
- MFA obligatoire pour rôles élevés
- Aucun compte partagé

Aligné DOC-SC-005 / DOC-SC-011.

---

## 5.2. Autorisation (RBAC strict)

- rôles définis
- permissions explicites
- refus par défaut
- audit des changements de rôle

---

# 6. Data Protection & Confidentialité

## 6.1. Classification des données

| Classe | Exemple |
|----|--------|
| Public | documentation |
| Interne | métriques agrégées |
| Sensible | tokens, secrets |
| Critique | clés privées, PII |

Chaque classe impose :
- chiffrement
- restrictions d’accès
- règles de rétention

---

## 6.2. Chiffrement

- at-rest : obligatoire
- in-transit : TLS obligatoire
- secrets : jamais en clair

---

# 7. Logging & Audit Trails

## 7.1. Événements auditables obligatoires

- login / logout
- échec auth
- changement de rôle
- accès secrets
- usage IA
- scheduling actions
- modifications configuration
- actions admin

---

## 7.2. Format d’audit standard

```json
{
  "event": "audit.role.changed",
  "actor_id": "...",
  "target_id": "...",
  "startup_id": "...",
  "org_id": "...",
  "old_role": "viewer",
  "new_role": "admin",
  "timestamp": "...",
  "trace_id": "..."
}
````

Logs :

* immuables
* horodatés
* centralisés
* non modifiables

---

# 8. Change Management

## 8.1. Changements critiques

Considérés critiques :

* secrets
* policies IA
* quotas
* budgets
* rôles
* rate limits
* modèles IA actifs

Chaque changement critique exige :

* justification
* trace
* auteur
* timestamp

---

## 8.2. CI/CD comme garde-fou

* lint compliance
* architecture checks
* policy enforcement
* merge bloqué si violation

---

# 9. Incident Management & Evidence

Aligné DOC-SC-017.

Chaque incident doit produire :

* description factuelle
* timeline
* impact
* actions correctives
* documents de preuve

---

# 10. Data Retention & Right to Erasure

## 10.1. Rétention

| Type          | Durée                |
| ------------- | -------------------- |
| Logs sécurité | 90–180 jours         |
| Audit logs    | 12–36 mois           |
| Analytics     | 12–36 mois           |
| Secrets       | durée de validité    |
| Backups       | politique documentée |

---

## 10.2. RGPD / Privacy

* suppression sur demande
* pseudonymisation par défaut
* aucune donnée inutile conservée
* traçabilité des suppressions

---

# 11. Vendor & Third-Party Risk

Chaque fournisseur externe (API, LLM, CDN, paiement) doit avoir :

* inventaire
* périmètre usage
* données exposées
* plan de sortie (exit strategy)

---

# 12. Evidence Pack (Audit Ready)

Le système doit pouvoir produire à tout moment :

* architecture docs (SC series)
* logs d’accès
* logs secrets
* policies IA
* preuves de rotation
* dashboards SRE
* rapports incidents
* journaux CI/CD

Sans développement spécifique.

---

# 13. Tests de conformité

Tests obligatoires :

* accès non autorisé
* fuite cross-tenant
* secret leakage
* absence logs critiques
* bypass gateway
* usage modèle non autorisé

---

# 14. CI/CD Compliance Rules

### 🚫 Bloquant

* absence audit logs
* absence RBAC strict
* secrets exposés
* accès non tracé
* modèle IA hors gouvernance
* pipeline sans contrôles

### ⚠ Warning

* absence documentation
* absence runbook
* absence tests compliance

---

# 15. Invariants non négociables

1. Toute action sensible est auditée.
2. Aucun accès sans trace.
3. Aucun secret sans contrôle.
4. Aucune IA sans gouvernance.
5. Aucune donnée sans politique.
6. Toute PR violant DOC-SC-024 est bloquée.

---

# 16. Conclusion

DOC-SC-024 place SaasentialCore au **niveau Enterprise-ready** :

* auditable à froid,
* conforme par construction,
* crédible face aux clients grands comptes,
* rassurant pour investisseurs,
* évolutif sans refonte compliance.

Ce document clôt la **série fondamentale DOC-SC-001 → DOC-SC-024**.

Il permet désormais :

* onboarding clients enterprise,
* préparation SOC2 / ISO,
* industrialisation multi-startup sereine.

```

---

## ✅ DOC-SC-024 est finalisé.
