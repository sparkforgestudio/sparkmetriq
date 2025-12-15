Voici **DOC-SC-007 — Versioning & Backward Compatibility Contract**,
version longue, propre, réaliste, pensée pour un **monorepo multi-startup**, avec plusieurs produits indépendants, différents cycles de release, et un socle SaasentialCore stable.

Ce document est essentiel pour éviter que Sparkmetriq, Sparkpusher ou tout futur produit **casse le socle Core** ou casse les autres produits lors d’une mise à jour.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-007_versioning_backward_compatibility_contract.md
```

---

# 📘 `DOC-SC-007_versioning_backward_compatibility_contract.md`

```markdown
---
title: DOC-SC-007 — Versioning & Backward Compatibility Contract
version: 1.0
status: Stable
category: SaasentialCore / Versioning / Compatibility / Releases
last_updated: 2025-02-15
---

# 1. Objectif du document

DOC-SC-007 définit le **contrat formel** de versionning et de compatibilité dans l’écosystème SaasentialCore :

- versioning du socle Core (SaasentialCore),
- versioning des produits (`products/*`),
- règles de compatibilité multi-produit,
- conditions pour breaking changes,
- règles CI/CD empêchant les régressions,
- stratégie d’évolution pour Sparkmetriq, Sparkpusher et futurs produits,
- conventions de documentation associées.

Ce document garantit que :

- le socle Core peut évoluer sans casser les produits existants,
- les produits peuvent évoluer indépendamment les uns des autres,
- l'API globale reste stable au runtime,
- les mises à jour sont traçables, sûres et documentées.

---

# 2. Principes fondamentaux

## ✔ 2.1. "Stability by Default"  
Tout changement doit **préserver la compatibilité** tant qu’une rupture n’est pas strictement nécessaire.

## ✔ 2.2. Versioning explicite  
Chaque composant versionné doit suivre **Semantic Versioning étendu (SemVer-X)**.

## ✔ 2.3. Aucun produit ne doit casser SaasentialCore  
DOC-SC-001 est strict :  
Core → ne dépend de personne  
Produits → dépendent de Core

## ✔ 2.4. Aucun produit ne casse un autre produit  
La compatibilité est *horizontale* ET *verticale*.

## ✔ 2.5. Toute rupture (breaking change) doit être :
- documentée,
- versionnée en major,
- validée en CI/CD,
- communiquée aux produits.

---

# 3. Semantic Versioning étendu (SemVer-X)

Chaque composant suit la forme :

```

MAJOR.MINOR.PATCH

```

Avec extensions :

- `MAJOR` = rupture de compatibilité  
- `MINOR` = ajout compatible  
- `PATCH` = correctifs / optimisations  
- `BUILD` (facultatif) = identifiant interne CI/CD  

### Exemple :

```

saasentialcore  →  1.4.2
sparkmetriq     →  2.1.0
sparkpusher     →  1.0.5

````

---

# 4. Versioning de SaasentialCore

## 4.1. Rythme
Le Core a un rythme de version indépendant des produits.

## 4.2. Compatibilité garantie
Un produit doit déclarer dans son manifest (DOC-SC-002) :

```json
"dependencies": {
  "saasentialcore": ">=1.0,<2.0"
}
````

Interdit :

* ❌ dépendre d’un commit Git particulier
* ❌ dépendre d’une version non publiée
* ❌ dépendre hors de la plage déclarée

## 4.3. Ruptures Core (MAJOR change)

Un changement dans SaasentialCore est considéré **breaking** s'il :

* supprime un provider DI,
* modifie le TenantContext (DOC-SC-004),
* modifie la structure JWT (DOC-SC-005),
* change le modèle d’événements (DOC-SC-006),
* modifie une interface publique stable.

Dans ce cas :

* incrément MAJOR,
* CI bloque tant que tous les produits non compatibles ne sont pas mis à jour.

---

# 5. Versioning des Produits

Chaque produit possède son propre versionnement indépendant du Core.

## 5.1. stocké dans `product_manifest.json`

```json
{
  "product_id": "sparkmetriq",
  "version": "2.0.0"
}
```

## 5.2. Conditions d’un changement de version produit

| Type  | Conditions                                    | Impact            |
| ----- | --------------------------------------------- | ----------------- |
| MAJOR | rupture API, rupture logicielle, rupture data | impact Core + API |
| MINOR | ajout de fonctionnalités compatibles          | safe              |
| PATCH | bugfix, perf, logs                            | safe              |

## 5.3. Interdiction absolue

Un produit ne peut **jamais** introduire un changement qui nécessite :

* la modification d’un autre produit,
* une régression dans SaasentialCore.

---

# 6. Compatibilité API (Core → Produits → API publique)

## 6.1. Chaque route API est versionnée implicitement par produit

Ex :

```
/p/sparkmetriq/v1/posts/schedule
/p/sparkmetriq/v2/posts/schedule
```

## 6.2. Règles de compatibilité API

* une route existante ne doit jamais changer de comportement,
* une nouvelle version doit créer un nouveau namespace (`v2`),
* suppression de version → seulement après période de dépréciation.

---

# 7. Compatibilité des événements (DOC-SC-006)

Un événement est considéré **breaking** si :

* son `event_type` change,
* sa structure change (payload),
* son tenant mapping change,
* son comportement métier se modifie.

### Règle :

Les consommateurs doivent rester compatibles pendant une fenêtre de transition.

---

# 8. Compatibilité DI (DOC-SC-003)

Le container doit garantir :

* aucun provider Core supprimé en MINOR/PATCH,
* annonce dans un changelog Core avant suppression,
* période de compatibilité de 2 versions MINOR minimum.

Exemple :

```
v1.3 → annonce dépréciation
v1.4 → provider encore présent
v1.5 → suppression autorisée
```

---

# 9. Compatibilité Multi-Startup et Multi-Tenant (DOC-SC-004)

Toute modification doit préserver :

* la structure TenantContext,
* les identifiants essentiels (startup_id, org_id),
* les invariants de séparation des données.

Rupture = MAJOR uniquement.

---

# 10. Conventions de documentation

Chaque version doit fournir :

* `CHANGELOG.md` dans le dossier du produit,
* release notes dans `docs/saasentialcore/releases/`,
* documentation API versionnée (Swagger/OpenAPI par produit),
* migration guides si rupture.

---

# 11. Tests de compatibilité

CI doit exécuter :

* tests Core unitaires,
* tests produits unitaires,
* tests d’intégration Core ←→ Produits,
* tests E2E composés multi-produits,
* tests de compatibilité DI,
* tests d’événements cross-produits.

### Obligatoire :

Pour chaque PR modifiant la structure Core :

* exécuter `compatibility_suite`
* vérifier stabilité API
* vérifier stabilité events
* vérifier stabilité tenant model

---

# 12. CI/CD Compliance Rules

### 🚫 Bloquant :

* suppression non documentée d’un champ Core,
* rupture non déclarée dans version produit,
* produit incompatible avec version Core déclarée,
* modification de `TenantContext` sans bump MAJOR,
* modification de routes sans versionnement,
* modification d’un événement sans compat layer.

### ⚠ Warning :

* absence de changelog,
* absence de documentation de migration,
* absence de tests backward compatibility.

---

# 13. Invariants non négociables

1. SaasentialCore = stabilité contractuelle.
2. Les produits évoluent indépendamment, mais dans leur namespace.
3. Jamais de breaking change sans MAJOR.
4. Toute rupture doit offrir période de transition.
5. L’API globale doit rester stable dans le temps.
6. Les événements doivent rester lisibles par les versions N et N-1.
7. Toute PR violant DOC-SC-007 est bloquée.

---

# 14. Conclusion

DOC-SC-007 assure :

* la stabilité du socle SaasentialCore,
* l’indépendance évolutive des produits,
* la compatibilité multi-startup,
* la robustesse du runtime (SRE++),
* l’absence d’effets de bord entre produits,
* la sécurité des upgrades dans un monorepo complexe.

C’est un pilier de gouvernance technique du projet.
```
# DOC-SC-007_versioning_backward_compatibility_contract.md
