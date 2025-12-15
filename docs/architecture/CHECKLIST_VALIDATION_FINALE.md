# Checklist de Validation Finale

*Checklist complète pour valider la conformité architecturale avant merge*

```yaml
---
title: Checklist Validation Finale
version: 1.0
status: Stable
category: Validation / CI
last_updated: 2025-01-28
---
```

---

## 1. Validation automatique (CI)

### Script de validation

```bash
# Exécuter le script de validation
./scripts/validate_architecture_compliance.sh
```

**Résultat attendu** : `✅ Architecture Compliance : OK`

---

## 2. Checklist manuelle (avant PR)

### DOC-001 : Dependency Injection

- [ ] Aucun `QuotasService()` dans `api/routes/*` ou `products/*/api/routes/*`
- [ ] Aucun `SchedulerService()` dans les routes
- [ ] Aucun `SaasentialCoreBridge()` sans `Depends`
- [ ] Toutes les routes utilisent `Depends(get_saasential_bridge)` depuis `api.deps`
- [ ] Aucun `localhost:27017` hardcodé
- [ ] Aucun `os.environ` dans les services (utiliser `settings`)
- [ ] Aucun `MongoClient()` dans le code métier

### DOC-002 : Shim Pattern

- [ ] Les shims importent depuis `products/*` (pas de duplication)
- [ ] Les shims délèguent via `include_router` ou ré-export
- [ ] Aucune logique métier dans les shims
- [ ] Docstring explique le rôle et la destination

### DOC-003 : API Schema & Response

- [ ] Toutes les routes ont un `response_model` explicite
- [ ] Tous les schémas utilisent Pydantic v2 (`model_config = ConfigDict(...)`)
- [ ] Tous les `datetime` sont timezone-aware (UTC)
- [ ] Tous les enums héritent de `str`

### DOC-004 : Quotas State Machine

- [ ] Vérification des quotas AVANT création de job
- [ ] Incrément `scheduled_posts` APRÈS création réussie
- [ ] Décrément `scheduled_posts` dans `on_success` ou `on_failure`
- [ ] Incrément `published_today` dans `on_success` uniquement
- [ ] Opérations atomiques MongoDB (`$inc`, `$set`)

### DOC-005 : Retry Policy & Idempotency

- [ ] MAX_ATTEMPTS = 3 (configurable)
- [ ] Backoff exponentiel entre tentatives
- [ ] Statut `FAILED` après échec définitif
- [ ] `completed_at` défini pour SUCCESS et FAILED
- [ ] Idempotency keys pour toutes les opérations externes

### Tests E2E

- [ ] Tous les tests E2E override `get_core_db` et `get_saasential_bridge`
- [ ] Aucun test n'utilise `localhost:27017` par défaut
- [ ] Fixture `override_dependencies` utilisée dans les tests

---

## 3. Validation pytest

```bash
# Tests core (doivent rester verts)
pytest saasentialcore/tests -q

# Tests S2 E2E (doivent passer)
pytest tests/test_s2_e2e.py -v

# Tests globaux
pytest -q
```

**Résultat attendu** : Tous les tests passent

---

## 4. Validation OpenAPI

```bash
# Générer la spec OpenAPI
python -c "from api.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > openapi.json

# Vérifier que toutes les routes ont un response_model
python -c "
import json
with open('openapi.json') as f:
    spec = json.load(f)
    for path, methods in spec['paths'].items():
        for method, details in methods.items():
            if 'responses' not in details or '200' not in details['responses']:
                print(f'⚠️  {method.upper()} {path} : pas de response 200')
            elif 'content' not in details['responses']['200']:
                print(f'⚠️  {method.upper()} {path} : response 200 sans content')
"
```

**Résultat attendu** : Aucun warning

---

## 5. Validation imports

```bash
# Vérifier qu'il n'y a pas d'imports circulaires
python -c "
import sys
sys.path.insert(0, '.')
try:
    from api.deps import get_core_db, get_saasential_bridge
    from api.services.core.saasential_bridge import SaasentialCoreBridge
    from products.sparkpusher.api.routes.scheduler import router
    print('✅ Imports OK')
except ImportError as e:
    print(f'❌ Erreur d\\'import: {e}')
    sys.exit(1)
"
```

**Résultat attendu** : `✅ Imports OK`

---

## 6. Résumé

### Critères de succès

- ✅ Script de validation : 0 erreur
- ✅ Tests pytest : tous verts
- ✅ OpenAPI : toutes les routes documentées
- ✅ Imports : aucun import circulaire
- ✅ Checklist manuelle : tous les items cochés

### En cas d'échec

1. Corriger les erreurs détectées
2. Relancer la validation
3. Mettre à jour la checklist
4. Documenter les exceptions (si justifiées)

---

## 7. Commandes rapides

```bash
# Validation complète
./scripts/validate_architecture_compliance.sh && pytest -q && echo "✅ Validation OK"

# Validation DI uniquement
grep -r "QuotasService(\|SchedulerService(\|SaasentialCoreBridge()" api/routes/ products/*/api/routes/ || echo "✅ DI OK"

# Validation response_model
grep -r "@router\.\(get\|post\)" api/routes/ products/*/api/routes/ | grep -v "response_model" || echo "✅ response_model OK"
```

---

## Conclusion

**Toute PR doit passer cette checklist avant merge.**

