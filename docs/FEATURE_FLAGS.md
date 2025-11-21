# docs/FEATURE_FLAGS.md
"""
# Feature Flags & Entitlements - musAI Platform

## Vue d'ensemble

Le système de feature flags permet d'activer/désactiver des modules (CloudPhone, OTP) globalement et par organisation (tenant).

## Architecture

### Feature Flags Globaux

Les feature flags globaux contrôlent si un module est disponible dans l'application :

- **`FEATURE_CLOUDPHONE_ENABLED`** : Active/désactive CloudPhone globalement
- **`FEATURE_OTP_ENABLED`** : Active/désactive OTP globalement

Si un flag est `false`, les routes du module ne sont **pas montées** dans l'application.

### Entitlements par Organisation

Les entitlements contrôlent l'accès aux fonctionnalités par organisation :

- **`features.cloudphone.active`** : Active/désactive CloudPhone pour une organisation
- **`features.otp.active`** : Active/désactive OTP pour une organisation

Si un entitlement est `false`, les endpoints retournent **403 Forbidden**.

## Configuration

### Variables d'environnement

Dans votre fichier `.env` :

```bash
# Feature flags globaux (par défaut: true)
FEATURE_CLOUDPHONE_ENABLED=true
FEATURE_OTP_ENABLED=true

# Configuration microservice (pour migration future)
USE_REMOTE_CLOUDPHONE=false
USE_REMOTE_OTP=false
CLOUDPHONE_BASE_URL=
CLOUDPHONE_S2S_TOKEN=
OTP_BASE_URL=
OTP_S2S_TOKEN=
```

### Entitlements par organisation

Les entitlements sont stockés dans MongoDB dans la collection `org_entitlements` :

```json
{
  "org_id": "org_123",
  "features": {
    "cloudphone": {
      "active": true
    },
    "otp": {
      "active": false
    }
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Utilisation

### Activer/désactiver globalement

Pour désactiver CloudPhone globalement :

```bash
FEATURE_CLOUDPHONE_ENABLED=false
```

Redémarrez l'application. Les routes CloudPhone ne seront plus accessibles.

### Activer/désactiver par organisation

Via l'API :

```bash
# Récupérer les entitlements
GET /api/org/entitlements

# Mettre à jour les entitlements (admin uniquement)
PUT /api/org/entitlements
{
  "features": {
    "cloudphone": {"active": true},
    "otp": {"active": false}
  }
}
```

Ou via Python :

```python
from api.services.orgs import set_entitlements

await set_entitlements("org_123", {
    "cloudphone": {"active": True},
    "otp": {"active": False}
})
```

## Vérification dans le code

### Dans les routes

Chaque endpoint CloudPhone/OTP vérifie automatiquement l'entitlement :

```python
@router.post("/devices")
async def create_device(
    payload: DeviceCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    # Vérification automatique de l'entitlement
    await check_cloudphone_entitlement(current_user)
    
    # Logique métier...
```

### Helper functions

```python
from api.core.feature_gate import require_feature
from api.services.orgs import get_entitlements

# Vérifier qu'une fonctionnalité est activée
entitlements = await get_entitlements(current_user.org_id)
require_feature(entitlements, "cloudphone")  # Lève 403 si non activé
```

## Comportement

### Flag global OFF

- ✅ Routes non montées (404 Not Found)
- ✅ Pas de code exécuté
- ✅ Aucune dépendance chargée

### Flag global ON + Entitlement OFF

- ✅ Routes montées
- ✅ Endpoints retournent 403 Forbidden
- ✅ Message: "Feature 'cloudphone' is not enabled for this organization."

### Flag global ON + Entitlement ON

- ✅ Routes montées
- ✅ Endpoints fonctionnent normalement
- ✅ Accès complet à la fonctionnalité

## Tests

Exécuter les tests de bascule :

```bash
pytest tests/toggles/test_feature_toggles.py -v
```

Les tests vérifient :
- ✅ Flag off → routes non montées
- ✅ Flag on + entitlement off → 403
- ✅ Flag on + entitlement on → OK

## Migration future (microservices)

Les variables `USE_REMOTE_*` sont préparées pour une migration future vers des microservices :

```python
if settings.use_remote_cloudphone:
    # Appel SDK client vers microservice CloudPhone
    client = CloudPhoneClient(settings.cloudphone_base_url)
else:
    # Logique locale (code actuel)
    ...
```

## Dépannage

### Routes toujours accessibles même avec flag off

**Problème** : Routes encore montées malgré `FEATURE_*_ENABLED=false`

**Solution** : Vérifier que :
1. Le `.env` est bien chargé
2. L'application a été redémarrée
3. Les routes sont bien montées conditionnellement dans `main.py`

### 403 sur toutes les routes même avec entitlement on

**Problème** : Entitlements non créés ou mal formatés

**Solution** : Vérifier la structure dans MongoDB :

```python
from api.services.orgs import get_entitlements

entitlements = await get_entitlements("org_id")
print(entitlements)  # Devrait avoir {"features": {"cloudphone": {"active": True}}}
```

### UserResponse n'a pas org_id

**Problème** : `current_user.org_id` est None

**Solution** : Vérifier que `get_current_user()` remplit bien `org_id` depuis la base de données.

## API Endpoints

### Organisations

- **GET** `/api/org/entitlements` : Récupérer les entitlements
- **PUT** `/api/org/entitlements` : Mettre à jour les entitlements (admin uniquement)

### CloudPhone

- Tous les endpoints préfixés par `/api/mobile-cloud/`
- Nécessitent `features.cloudphone.active = true`

### OTP

- Tous les endpoints préfixés par `/api/otp/`
- Nécessitent `features.otp.active = true`

## Exemples

### Activer CloudPhone pour une organisation

```bash
curl -X PUT http://localhost:8000/api/org/entitlements \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "cloudphone": {"active": true}
    }
  }'
```

### Vérifier les entitlements

```bash
curl http://localhost:8000/api/org/entitlements \
  -H "Authorization: Bearer $TOKEN"
```

---

**Note** : Le système est conçu pour être non-régressif. Aucun endpoint existant n'est cassé, et les modules fonctionnent par défaut si rien n'est configuré.



