# docs/CLOUDPHONE_MODULE.md
"""
# Module CloudPhone Management + OTP Manager

## Vue d'ensemble

Le module CloudPhone Management + OTP Manager permet aux agences de gérer des téléphones cloud virtuels, d'installer des applications en masse, d'assigner des proxies géolocalisés et de gérer la vérification OTP de manière semi-manuelle et agnostique aux providers.

## Architecture

### Composants principaux

1. **CloudPhone Management**
   - Gestion des profils (form-first)
   - Création et gestion des devices
   - Gestion des slots d'applications
   - Bind/unbind des comptes d'applications
   - Exécution d'actions RPA

2. **OTP Manager**
   - Système agnostique aux providers
   - Gestion des sessions OTP avec FSM
   - Parsing et masquage des codes
   - Politiques de géolocalisation
   - Failover automatique

3. **Observabilité**
   - Logs d'audit complets
   - Métriques Prometheus
   - Alertes WebSocket en temps réel
   - Notifications Telegram

### Stack technique

- **Backend**: FastAPI (Python 3.11+)
- **Base de données**: MongoDB avec Motor (driver async)
- **Validation**: Pydantic v2
- **Multi-tenancy**: Isolation par `org_id`
- **Tests**: pytest + pytest-asyncio

## Structure des données

### Collections MongoDB

#### CloudPhone
- `cloudphone_profiles`: Profils de configuration
- `cloudphone_devices`: Devices virtuels
- `cloudphone_app_accounts`: Comptes d'applications
- `cloudphone_device_app_slots`: Slots d'applications par device
- `cloudphone_bindings_appaccount_slot`: Liaisons compte-slot

#### OTP
- `otp_sessions`: Sessions OTP avec FSM
- `otp_providers`: Configuration des providers
- `otp_pools`: Pools de numéros par app/pays

#### Observabilité
- `activity_logs`: Logs d'audit
- `alerts`: Alertes système
- `metrics`: Métriques Prometheus

### Index MongoDB

```javascript
// CloudPhone
db.cloudphone_profiles.createIndex({"org_id": 1, "name": 1}, {unique: true})
db.cloudphone_devices.createIndex({"org_id": 1, "state": 1})
db.cloudphone_device_app_slots.createIndex({"org_id": 1, "device_id": 1, "app": 1})

// OTP
db.otp_sessions.createIndex({"org_id": 1, "state": 1})
db.otp_sessions.createIndex({"org_id": 1, "created_at": -1})
db.otp_sessions.createIndex({"provider_session_id": 1}, {unique: true, sparse: true})

// Observabilité
db.activity_logs.createIndex({"org_id": 1, "timestamp": -1})
db.alerts.createIndex({"org_id": 1, "status": 1})
```

## API Endpoints

### CloudPhone

#### Profils (Form-first)
```
POST   /api/mobile-cloud/profiles              # Créer un profil
GET    /api/mobile-cloud/profiles              # Lister les profils
GET    /api/mobile-cloud/profiles/{id}         # Récupérer un profil
PUT    /api/mobile-cloud/profiles/{id}         # Mettre à jour un profil
DELETE /api/mobile-cloud/profiles/{id}         # Supprimer un profil
```

#### Excel Import (Optionnel)
```
POST   /api/mobile-cloud/profiles/excel/upload    # Import Excel
GET    /api/mobile-cloud/profiles/excel/template   # Télécharger template
```

#### Devices
```
POST   /api/mobile-cloud/devices              # Créer un device
GET    /api/mobile-cloud/devices              # Lister les devices
POST   /api/mobile-cloud/devices/{id}/start  # Démarrer un device
POST   /api/mobile-cloud/devices/{id}/stop   # Arrêter un device
```

#### Slots et Actions
```
POST   /api/mobile-cloud/devices/{id}/slots   # Créer un slot
GET    /api/mobile-cloud/slots                # Lister les slots
POST   /api/mobile-cloud/slots/bind           # Lier un compte
POST   /api/mobile-cloud/slots/unbind         # Délier un compte
POST   /api/mobile-cloud/slots/exec           # Exécuter une action
```

### OTP

#### Sessions
```
POST   /api/otp/reserve                       # Réserver un numéro
POST   /api/otp/poll/{session_id}             # Poller une session
POST   /api/otp/ack/{session_id}              # Accuser réception
POST   /api/otp/apply/{session_id}            # Appliquer le résultat
POST   /api/otp/cancel/{session_id}           # Annuler une session
POST   /api/otp/ban/{session_id}              # Bannir une session
```

#### Gestion
```
GET    /api/otp/sessions                      # Lister les sessions
GET    /api/otp/sessions/{id}                 # Récupérer une session
GET    /api/otp/providers                      # Lister les providers
GET    /api/otp/pools                          # Lister les pools
GET    /api/otp/budget                         # Récupérer le budget
PUT    /api/otp/budget                         # Mettre à jour le budget
```

#### Analytics
```
GET    /api/otp/metrics                       # Métriques OTP
POST   /api/otp/analytics                     # Analytics détaillées
GET    /api/otp/config                        # Configuration
PUT    /api/otp/config                         # Mettre à jour config
```

## États et Transitions

### FSM OTP

```
INIT → RESERVED → WAITING_CODE → DELIVERED_TO_ADMIN → APPLIED_SUCCESS
  ↓       ↓           ↓              ↓                    ↓
CANCELLED FAILED   TIMEOUT        APPLIED_FAILED      COMPLETED
  ↓       ↓           ↓              ↓
BANNED  FAILOVER   RETRY          RETRY
```

### États Device

```
CREATED → STARTING → RUNNING → STOPPING → STOPPED
   ↓         ↓          ↓         ↓         ↓
  ERROR    ERROR      ERROR    ERROR    ERROR
```

### États Slot

```
VACANT → BINDING → BOUND → UNBINDING → VACANT
  ↓         ↓        ↓        ↓
ERROR    ERROR    ERROR    ERROR
```

## Sécurité

### Chiffrement des codes OTP

```python
# Les codes OTP ne sont jamais stockés en clair
code_masked = mask_code(extracted_code)  # "123456" → "12****"
```

### Audit Trail

Chaque action est enregistrée avec :
- `org_id`: Organisation
- `user_id`: Utilisateur
- `scope`: Portée (cloudphone, otp)
- `action`: Action effectuée
- `status`: Succès/échec
- `resource_id`: ID de la ressource
- `timestamp`: Horodatage

### Permissions

- **Admin**: Toutes les opérations
- **Operator**: Gestion des devices et slots
- **Viewer**: Lecture seule

## Configuration

### Variables d'environnement

```bash
# CloudPhone
CLOUDPHONE_BASE_URL=https://api.cloudphone.example.com
CLOUDPHONE_API_KEY=your_api_key
CLOUDPHONE_TIMEOUT=30.0

# OTP
OTP_PRIMARY_PROVIDER=http_json
OTP_HTTP_BASE_URL=https://api.otp-provider.com
OTP_HTTP_TOKEN=your_otp_token
OTP_SESSION_TIMEOUT=10

# Base de données
MONGO_URI=mongodb://localhost:27017
MONGO_DB=musai_dev

# Observabilité
LOG_LEVEL=INFO
ENABLE_PROMETHEUS=true
ENABLE_WEBSOCKETS=true
```

### Configuration centralisée

```python
from api.config.cloudphone_config import config

# Accès à la configuration
cloudphone_config = config.cloudphone
otp_config = config.otp
```

## Tests

### Structure des tests

```
tests/
├── cloudphone/
│   ├── test_profiles_form_crud.py
│   ├── test_device_slot_flow.py
│   └── test_excel_import.py
├── otp/
│   ├── test_otp_flow_manual.py
│   ├── test_providers.py
│   └── test_sessions.py
└── integration/
    ├── test_end_to_end.py
    └── test_performance.py
```

### Exécution des tests

```bash
# Tests unitaires
pytest tests/cloudphone/
pytest tests/otp/

# Tests d'intégration
pytest tests/integration/

# Tests avec couverture
pytest --cov=api tests/
```

## Monitoring

### Métriques Prometheus

```
# CloudPhone
cloudphone_devices_created_total{org_id, area}
cloudphone_devices_running{org_id, area}
cloudphone_slots_active{org_id, app}
cloudphone_action_duration_seconds{org_id, action, app}

# OTP
otp_sessions_reserved_total{org_id, app, country, provider}
otp_sessions_delivered_total{org_id, app, country, provider}
otp_sessions_applied_total{org_id, app, country, provider, status}
otp_response_time_seconds{org_id, app, country, provider}
```

### Alertes

- **Device unreachable**: Device non accessible
- **OTP timeout**: Session OTP expirée
- **Budget exceeded**: Budget OTP dépassé
- **Provider down**: Provider OTP indisponible

## Déploiement

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements-cloudphone.txt .
RUN pip install -r requirements-cloudphone.txt

COPY api/ ./api/
COPY tests/ ./tests/

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloudphone-module
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cloudphone-module
  template:
    metadata:
      labels:
        app: cloudphone-module
    spec:
      containers:
      - name: cloudphone-module
        image: cloudphone-module:latest
        ports:
        - containerPort: 8000
        env:
        - name: MONGO_URI
          value: "mongodb://mongo:27017"
        - name: CLOUDPHONE_BASE_URL
          value: "https://api.cloudphone.example.com"
```

## Maintenance

### Nettoyage des données

```python
# Nettoyage des sessions OTP expirées
await db.otp_sessions.delete_many({
    "state": {"$in": ["CANCELLED", "FAILED", "APPLIED_SUCCESS"]},
    "created_at": {"$lt": datetime.now() - timedelta(days=7)}
})

# Nettoyage des logs d'audit
await db.activity_logs.delete_many({
    "timestamp": {"$lt": datetime.now() - timedelta(days=90)}
})
```

### Optimisation des performances

1. **Index MongoDB**: Vérifier les index manquants
2. **Cache Redis**: Mettre en cache les sessions OTP actives
3. **Pool de connexions**: Optimiser les pools HTTP et MongoDB
4. **Monitoring**: Surveiller les métriques de performance

## Troubleshooting

### Problèmes courants

1. **Device non accessible**
   - Vérifier la connectivité réseau
   - Vérifier les credentials API
   - Consulter les logs d'erreur

2. **OTP timeout**
   - Vérifier la configuration du provider
   - Vérifier les quotas et budgets
   - Consulter les métriques de performance

3. **Erreurs de validation**
   - Vérifier les schémas Pydantic
   - Vérifier les contraintes de données
   - Consulter les logs de validation

### Logs utiles

```bash
# Logs d'application
tail -f logs/app.log | grep "cloudphone\|otp"

# Logs d'erreur
tail -f logs/error.log | grep "ERROR"

# Métriques Prometheus
curl http://localhost:8000/metrics
```




