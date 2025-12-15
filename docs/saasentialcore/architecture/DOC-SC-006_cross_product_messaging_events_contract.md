Parfait.
Voici maintenant l’un des documents centraux du socle SaasentialCore, indispensable à la cohérence multi-startup et multi-produit :

# ✅ **DOC-SC-006 — Cross-Product Messaging & Events Contract**

Version longue, propre, cohérente avec les DOC-SC précédents, pensée pour un système **event-driven** industriel, compatible S2/S3/S4, Sparkpusher, et tout futur produit.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-006_cross_product_messaging_events_contract.md
```

---

# 📘 `DOC-SC-006_cross_product_messaging_events_contract.md`

````markdown
---
title: DOC-SC-006 — Cross-Product Messaging & Events Contract
version: 1.0
status: Stable
category: SaasentialCore / Messaging / Events / Multi-Product Architecture
last_updated: 2025-02-14
---

# 1. Objectif du document

DOC-SC-006 définit le **contrat officiel du système d’événements interne (event-driven architecture)** utilisé par SaasentialCore et l’ensemble des produits enregistrés (Sparkmetriq, Sparkpusher, et futurs produits).

Il garantit :

- un format d’événement uniforme,  
- une propagation fiable entre produits,  
- une intégration facile pour scheduler/workers/dispatcher,  
- de l’observabilité (logs, métriques, traces),  
- de l’isolation tenant (aligné DOC-SC-004),  
- de la sécurité (aligné DOC-SC-005 / DOC-019),  
- de la scalabilité horizontale.  

Ce document organise une “backbone interne” indispensable au monorepo multi-startup.

---

# 2. Principes fondamentaux

## ✔ 2.1. Event-first architecture  
Tout changement important dans le système doit produire un événement.

## ✔ 2.2. Aucun événement synchronisé avec un appel direct cross-produit  
Les produits **ne doivent pas s’appeler entre eux** directement.  
Ils communiquent via événements internes.

## ✔ 2.3. Les événements doivent être :
- immuables,  
- horodatés,  
- signés par un tenant,  
- produits par un produit,  
- consommables par d’autres produits,  
- persistables dans une event log.  

## ✔ 2.4. Multi-tenant isolé  
Un tenant ne peut jamais recevoir les événements d’un autre tenant.

## ✔ 2.5. Observabilité obligatoire  
Chaque événement doit être loggé, métriqué, traçable.

---

# 3. Architecture du Event Bus interne

```mermaid
flowchart TD
    ProductA --> EB((Event Bus))
    ProductB --> EB
    ProductC --> EB

    EB --> ConsumersA
    EB --> ConsumersB
    EB --> ConsumersC
````

Le Event Bus n’est pas nécessairement une technologie externe unique.
Il peut être :

* RabbitMQ (topics),
* Redis Streams,
* NATS,
* Kafka (option future scale),
* ou une abstraction interne par-dessus ces systèmes.

SaasentialCore n’impose pas la technologie, mais impose le **contrat**.

---

# 4. Format d’un événement (Event Envelope)

Chaque événement doit respecter le schéma suivant :

```json
{
  "event_id": "uuid",
  "event_type": "sparkmetriq.s2.post.scheduled",
  "timestamp": "2025-02-14T10:20:12.451Z",
  "producer": {
    "product_id": "sparkmetriq",
    "service": "scheduler"
  },
  "tenant": {
    "startup_id": "stp_1",
    "org_id": "org_77"
  },
  "payload": {
    "...": "..."
  },
  "metadata": {
    "trace_id": "abc-xyz",
    "version": "1.0"
  }
}
```

## Champs obligatoires

| Champ        | Description                           |
| ------------ | ------------------------------------- |
| `event_id`   | identifiant unique (UUIDv4 ou ULID)   |
| `event_type` | namespace clair (voir section 5)      |
| `timestamp`  | horodatage UTC                        |
| `producer`   | identifie le produit/service émetteur |
| `tenant`     | isolation tenant (aligné DOC-SC-004)  |
| `payload`    | contenu métier                        |
| `metadata`   | trace + version                       |

---

# 5. Nommage standard des événements

Chaque événement doit suivre la structure :

```
<product>.<module>.<entity>.<action>
```

Exemples Sparkmetriq S2 :

* `sparkmetriq.s2.post.scheduled`
* `sparkmetriq.s2.post.dispatched`
* `sparkmetriq.s2.post.published`
* `sparkmetriq.s2.quota.reserved`
* `sparkmetriq.s2.quota.released`

Exemples Sparkpusher :

* `sparkpusher.inbox.message_received`
* `sparkpusher.dm.sent`

---

# 6. Production d’événements

### 6.1. Production obligatoire

Tout service métier doit produire un événement lorsque :

* un état change,
* une action utilisateur est effectuée,
* un workflow produit évolue,
* une publication est planifiée / ratée / réussie,
* une erreur critique est détectée.

### 6.2. Règle d’immuabilité

Un événement émis :

* ne peut jamais être modifié,
* ne peut jamais être supprimé,
* ne peut être compensé que par un *nouvel événement* (ex : `post.schedule_cancelled`).

---

# 7. Consommation d’événements

Un produit peut :

* écouter les événements produits par lui-même,
* écouter des événements produits par d’autres produits,
* réagir de façon asynchrone.

Chaque consommateur doit :

* valider le type d’événement,
* valider le tenant,
* s’isoler des erreurs internes,
* être idempotent (aligné DOC-005).

---

# 8. Idempotence (SRE++)

Chaque consommateur doit garantir :

```
Si un événement est reçu plusieurs fois → effet unique
```

Mécanisme :

* clés idempotence stockées dans DB,
* hashing payload + event_id,
* time-based expiration des idempotency markers.

---

# 9. Persisted Event Log (optionnel mais recommandé)

Pour audit et reprocessing :

```
event_log/
    startup_id/
        org_id/
            <event_id>.json
```

Permet :

* replay,
* débogage,
* post-mortem incidents,
* reconstruction d’état partiel.

---

# 10. Observabilité (aligné DOC-SC-009)

Chaque événement doit générer :

## Logs structurés

```json
{
  "event": "event.produced",
  "event_type": "sparkmetriq.s2.post.scheduled",
  "event_id": "uuid",
  "startup_id": "...",
  "org_id": "...",
  "producer": "scheduler",
  "timestamp": "...",
  "status": "success"
}
```

## Métriques Prometheus

```
events_produced_total{event_type="..."}
events_consumed_total{event_type="..."}
event_latency_seconds{event_type="..."}
event_errors_total{event_type="..."}
event_retries_total{event_type="..."}
```

## Traces (OpenTelemetry)

Propagation du `trace_id` de l’événement au consommateur.

---

# 11. Sécurité & isolation (aligné DOC-SC-004 & DOC-SC-005)

### Obligatoire :

* tag tenant dans tous les événements,
* filtrage strict tenant dans consommation,
* interdire propagation cross-startup,
* interdire propagation cross-produit SANS manifest autorisant.

### Interdit :

* produire un événement sans metadata tenant,
* consommer un événement d’un autre tenant,
* publier des secrets dans un événement,
* publier des tokens d’accès dans payload.

---

# 12. Règles pour les produits (DOC-SC-002)

Chaque produit doit fournir :

```
products/<id>/events/
    handlers.py     # consommateurs
    producers.py    # producteurs
    schemas.py      # schémas d’événements
```

Chaque produit doit déclarer ses événements dans son manifest :

```json
{
  "events": [
    "sparkmetriq.s2.post.scheduled",
    "sparkmetriq.s2.post.published"
  ]
}
```

---

# 13. Tests (qualité SRE++)

## Unitaires

* validation du schéma événement,
* test idempotence,
* test isolation tenant.

## Intégration

* test producteur/consommateur,
* test retry/backoff (aligné DOC-005),
* test propagation des traces.

## E2E

* workflow complet S2
  `scheduled → dispatched → published → analytics`

* workflow complet S2 en panne (aligné DOC-017)

---

# 14. CI/CD Compliance Rules

### 🚫 Bloquant :

* absence de metadata tenant,
* absence de event_type standardisé,
* absence de trace_id,
* événement non idempotent,
* consommation cross-produit interdite,
* utilisation d’un bus non configuré via DI (aligné DOC-SC-003),
* événement contenant secrets sensibles,
* event_type non déclaré par produit (aligné DOC-SC-002).

### ⚠ Warning :

* absence de dashboards événementiels,
* absence d’alertes SRE sur erreurs,
* absence de persisted event log (si activé).

---

# 15. Invariants non négociables

1. Aucun événement n’est produit sans tenant.
2. Aucun produit ne doit émettre d’événements hors de son namespace.
3. Aucun événement ne doit contenir d’informations sensibles.
4. Tous les événements doivent être idempotents.
5. Tous les événements doivent être observables (logs + metrics + traces).
6. Tout consommateur doit être isolé, résilient, safe-fail.
7. Toute PR violant DOC-SC-006 doit être bloquée.

---

# 16. Conclusion

DOC-SC-006 fixe la **backbone événementielle** du socle multi-startup SaasentialCore :

* communication cross-produit propre,
* architecture event-driven moderne,
* isolation tenant,
* sécurité, résilience, observabilité,
* compatibilité avec S2/S3/S4 et futurs produits,
* extensibilité parfaite.

C’est l’un des piliers techniques les plus importants du monorep
```
# DOC-SC-006_cross_product_messaging_events_contract.md
