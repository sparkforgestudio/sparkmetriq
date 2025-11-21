# 🚀 Intégrations de Plateformes - MuseMgmt Platform

Ce document décrit les nouvelles intégrations de plateformes développées pour MuseMgmt Platform.

## 📋 Plateformes Supportées

### ✅ Plateformes Existantes (Améliorées)
- **Instagram** - API Graph Facebook
- **Telegram** - Bot API
- **Threads** - API Graph Meta
- **Snapchat** - Ads API
- **Reddit** - OAuth API
- **Twitter** - API v2
- **Facebook** - API Graph

### 🆕 Nouvelles Plateformes
- **TikTok** - API TikTok for Business
- **OnlyFans** - API OnlyFans (simulée)
- **Fanvue** - API Fanvue (simulée)

## 🔧 Configuration

### Variables d'Environnement

#### TikTok
```bash
# Obligatoires
TIKTOK_CLIENT_KEY=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
TIKTOK_REDIRECT_URI=your_redirect_uri

# Optionnelles
TIKTOK_WEBHOOK_SECRET=your_webhook_secret
TIKTOK_VERIFY_TOKEN=your_verify_token
```

#### Fanvue
```bash
# Obligatoires
FANVUE_API_KEY=your_api_key
FANVUE_API_SECRET=your_api_secret

# Optionnelles
FANVUE_WEBHOOK_SECRET=your_webhook_secret
FANVUE_VERIFY_TOKEN=your_verify_token
```

#### OnlyFans
```bash
# Obligatoires
ONLYFANS_API_KEY=your_api_key
ONLYFANS_API_SECRET=your_api_secret

# Optionnelles
ONLYFANS_WEBHOOK_SECRET=your_webhook_secret
ONLYFANS_VERIFY_TOKEN=your_verify_token
```

## 🏗️ Architecture

### Structure des Fichiers

```
api/
├── services/content_distributor/connectors/
│   ├── tiktok.py          # Connecteur TikTok complet
│   ├── fanvue.py          # Connecteur Fanvue complet
│   └── onlyfans.py        # Connecteur OnlyFans amélioré
├── routes/webhooks/
│   ├── tiktok.py          # Webhooks TikTok
│   └── fanvue.py          # Webhooks Fanvue
├── schemas/
│   └── platforms.py       # Schémas Pydantic pour les plateformes
├── core/
│   └── platform_configs.py # Configuration des plateformes
└── routes/
    └── platforms.py       # API de gestion des plateformes
```

### Connecteurs

Chaque connecteur implémente:
- **Authentification** avec tokens et refresh automatique
- **Upload de médias** (images, vidéos)
- **Publication de contenu** avec paramètres avancés
- **Récupération d'analytics** et statistiques
- **Gestion d'erreurs** robuste
- **Logging** complet des événements

### Webhooks

Les webhooks gèrent:
- **Vérification** des signatures de sécurité
- **Événements de publication** (succès, échec)
- **Notifications d'analytics** en temps réel
- **Événements de paiement** (pour les plateformes monétisées)
- **Gestion des abonnements** (pour les plateformes premium)

## 📡 API Endpoints

### Publication Multi-Plateformes

```http
POST /api/platforms/publish
Content-Type: application/json

{
  "platforms": ["tiktok", "fanvue", "onlyfans"],
  "content": {
    "title": "Mon contenu",
    "text": "Description du contenu",
    "media_urls": ["https://example.com/video.mp4"],
    "price": 10.0,
    "tags": ["tag1", "tag2"]
  },
  "agency_id": "agency_123",
  "muse_id": "muse_456"
}
```

### Analytics

```http
GET /api/platforms/analytics?agency_id=agency_123&platform=tiktok&start_date=2024-01-01&end_date=2024-01-31
```

### Gestion des Credentials

```http
# Récupérer les credentials
GET /api/platforms/credentials?agency_id=agency_123

# Créer/Mettre à jour les credentials
POST /api/platforms/credentials
{
  "platform": "tiktok",
  "credentials": {
    "access_token": "token_123",
    "refresh_token": "refresh_456"
  },
  "is_active": true
}

# Supprimer les credentials
DELETE /api/platforms/credentials/tiktok?agency_id=agency_123
```

## 🔗 Webhooks

### TikTok

```http
# Vérification
GET /webhook/tiktok/verify?hub.challenge=123&hub.verify_token=token

# Callback
POST /webhook/tiktok/callback
X-TikTok-Signature: signature
Content-Type: application/json

{
  "event": "video.publish",
  "data": {
    "publish_id": "pub_123",
    "video_id": "vid_456",
    "status": "success"
  }
}
```

### Fanvue

```http
# Vérification
GET /webhook/fanvue/verify?hub.challenge=123&hub.verify_token=token

# Callback
POST /webhook/fanvue/callback
X-Fanvue-Signature: signature
Content-Type: application/json

{
  "event": "post.purchased",
  "data": {
    "post_id": "post_123",
    "buyer_id": "buyer_456",
    "amount": 10.0
  }
}
```

## 🧪 Tests

### Tests Unitaires

```bash
# Tests TikTok
pytest tests/unit/test_tiktok_integration.py -v

# Tests Fanvue
pytest tests/unit/test_fanvue_integration.py -v

# Tests OnlyFans
pytest tests/unit/test_onlyfans_integration.py -v
```

### Tests d'Intégration

```bash
# Tests des webhooks
python test_webhooks.py

# Tests de publication
pytest tests/integration/test_platform_publishing.py -v
```

## 🚀 Déploiement

### 1. Configuration des Variables d'Environnement

```bash
# Utiliser le script de configuration
python scripts/setup_platforms.py

# Ou configurer manuellement
cp .env.example .env
# Éditer .env avec vos credentials
```

### 2. Création des Collections MongoDB

```bash
# Le script de configuration crée automatiquement les collections
python scripts/setup_platforms.py
# Choisir l'option 4
```

### 3. Configuration des Webhooks

```bash
# Générer les URLs de webhooks
python scripts/setup_platforms.py
# Choisir l'option 3 et fournir votre URL de base
```

### 4. Test de la Configuration

```bash
# Vérifier le statut des plateformes
python scripts/setup_platforms.py
# Choisir l'option 1

# Tester les webhooks
python test_webhooks.py
```

## 📊 Monitoring et Analytics

### Logs de Plateforme

Tous les événements sont loggés dans la collection `platform_logs`:

```javascript
{
  "platform": "tiktok",
  "agency_id": "agency_123",
  "muse_id": "muse_456",
  "content_id": "content_789",
  "status": "success",
  "message": "Publication TikTok réussie",
  "metadata": {
    "title": "Mon vidéo",
    "publish_id": "pub_123",
    "views": 1000,
    "likes": 50
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Analytics Avancés

Les analytics sont disponibles via l'API:

- **Métriques par plateforme** (vues, likes, commentaires, partages)
- **Revenus** (pour les plateformes monétisées)
- **Taux d'engagement** calculé automatiquement
- **Comparaisons** entre plateformes
- **Tendances** temporelles

## 🔒 Sécurité

### Authentification

- **Tokens OAuth2** avec refresh automatique
- **Signatures HMAC** pour les webhooks
- **Validation** des credentials en base
- **Chiffrement** des tokens sensibles

### Rate Limiting

Chaque plateforme a ses limites de taux configurées:

```python
RATE_LIMITS = {
    "tiktok": {"requests_per_hour": 100, "requests_per_day": 2400},
    "fanvue": {"requests_per_hour": 100, "requests_per_day": 2400},
    "onlyfans": {"requests_per_hour": 50, "requests_per_day": 1200}
}
```

## 🐛 Dépannage

### Problèmes Courants

1. **Credentials manquants**
   ```bash
   # Vérifier les variables d'environnement
   python scripts/setup_platforms.py
   ```

2. **Webhooks non reçus**
   ```bash
   # Tester les webhooks
   python test_webhooks.py
   ```

3. **Erreurs de publication**
   ```bash
   # Vérifier les logs
   tail -f logs/platform.log
   ```

### Support

Pour toute question ou problème:
1. Vérifier les logs dans `logs/`
2. Consulter la documentation des APIs des plateformes
3. Tester avec le script de diagnostic
4. Contacter l'équipe de développement

## 🔄 Mises à Jour

### Ajout d'une Nouvelle Plateforme

1. **Créer le connecteur** dans `api/services/content_distributor/connectors/`
2. **Ajouter les schémas** dans `api/schemas/platforms.py`
3. **Créer les webhooks** dans `api/routes/webhooks/`
4. **Mettre à jour la configuration** dans `api/core/platform_configs.py`
5. **Ajouter les tests** dans `tests/unit/`
6. **Documenter** dans ce fichier

### Mise à Jour d'une Plateforme Existante

1. **Tester** les changements en local
2. **Mettre à jour** les tests unitaires
3. **Vérifier** la compatibilité avec l'existant
4. **Déployer** en staging puis en production
5. **Monitorer** les logs après déploiement

---

**Note**: Ce document est mis à jour régulièrement. Consultez la version la plus récente pour les dernières fonctionnalités.



