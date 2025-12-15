# 🎬 Intégration ManyVids.com - MuseMgmt Platform

## 📋 **Vue d'ensemble**

ManyVids.com est l'une des plateformes de contenu adulte les plus populaires au monde, permettant aux créateurs de monétiser leurs vidéos, photos et services personnalisés. Cette intégration complète offre une gestion avancée de tous les aspects de la publication et de la monétisation sur ManyVids.

## 🏗️ **Architecture de l'Intégration**

### **Fichiers Créés**

```
api/services/content_distributor/connectors/
└── manyvids.py                    # Connecteur ManyVids complet

api/routes/webhooks/
└── manyvids.py                    # Webhooks ManyVids

tests/unit/
└── test_manyvids_integration.py   # Tests unitaires
```

### **Fichiers Modifiés**

- `api/services/content_distributor/dispatcher.py` - Ajout du dispatcher ManyVids
- `api/core/platform_configs.py` - Configuration ManyVids
- `api/schemas/platforms.py` - Schémas ManyVids
- `api/main.py` - Enregistrement des routes
- `env.platforms.example` - Variables d'environnement

## 🚀 **Fonctionnalités Implémentées**

### **Connecteur ManyVids** (`manyvids.py`)

#### ✅ **Authentification**
- **HMAC Signature** avec API Key et Secret
- **Headers sécurisés** avec timestamp et signature
- **User-Agent** personnalisé pour identification
- **Accept** headers pour format JSON

#### ✅ **Gestion du Profil**
- `get_profile_info()` - Informations du créateur
- Récupération des statistiques de base
- Vérification du statut de vérification
- Données de revenus et de fans

#### ✅ **Upload et Gestion de Vidéos**
- `upload_video()` - Upload de vidéos avec métadonnées
- `create_video()` - Création de vidéos
- `update_video()` - Modification de vidéos existantes
- `delete_video()` - Suppression de vidéos
- `get_videos()` - Liste des vidéos avec filtres

#### ✅ **Vidéos Personnalisées**
- `create_custom_video_request()` - Création de demandes
- `get_custom_video_requests()` - Gestion des demandes
- Suivi des budgets et délais
- Gestion des demandes spéciales

#### ✅ **Gestion des Fans**
- `get_fans()` - Liste des fans
- Suivi des abonnements
- Historique des dépenses
- Dernière activité

#### ✅ **Messages et Communication**
- `send_message()` - Messages aux fans
- `get_messages()` - Historique des messages
- Support des messages payants
- Gestion des médias dans les messages

#### ✅ **Analytics et Revenus**
- `get_earnings()` - Revenus par période
- `get_video_analytics()` - Analytics par vidéo
- `get_analytics_overview()` - Vue d'ensemble
- Métriques détaillées d'engagement

#### ✅ **Catégories et Tags**
- `get_categories()` - Catégories disponibles
- `get_trending_tags()` - Tags tendance
- Optimisation du contenu
- Découverte de contenu

#### ✅ **Sécurité**
- `verify_webhook_signature()` - Vérification HMAC
- Validation des signatures webhook
- Gestion sécurisée des credentials

## 📡 **Webhooks ManyVids**

### **Événements Supportés**

#### 🎬 **Gestion des Vidéos**
- `video.uploaded` - Vidéo uploadée avec succès
- `video.purchased` - Vidéo achetée par un fan
- `video.analytics_updated` - Analytics mises à jour
- Métadonnées complètes (prix, catégorie, durée)

#### 🎯 **Vidéos Personnalisées**
- `custom_video.requested` - Nouvelle demande
- `custom_video.completed` - Vidéo personnalisée terminée
- Suivi des budgets et délais
- Évaluations de satisfaction

#### 👥 **Gestion des Fans**
- `fan.subscribed` - Nouvel abonnement
- `fan.unsubscribed` - Désabonnement
- Gestion des cycles de facturation
- Suivi des dépenses

#### 💬 **Messages**
- `message.sent` - Message envoyé
- Support des messages payants
- Suivi des interactions

#### 💰 **Paiements**
- `payment.completed` - Paiement finalisé
- Détails de transaction (montant, méthode, frais)
- Suivi des revenus nets

### **Endpoints Webhooks**

```http
# Callback principal
POST /webhook/manyvids/callback

# Vérification webhook
GET /webhook/manyvids/verify?hub_mode=subscribe&hub_challenge=CHALLENGE&hub_verify_token=TOKEN

# Analytics d'une vidéo
GET /webhook/manyvids/analytics/{video_id}?start_date=2024-01-01&end_date=2024-01-31

# Catégories disponibles
GET /webhook/manyvids/categories

# Tags tendance
GET /webhook/manyvids/trending/tags
```

## 🔧 **Configuration**

### **Variables d'Environnement**

```bash
# Credentials API
MANYVIDS_API_KEY=your_api_key_here
MANYVIDS_API_SECRET=your_api_secret_here

# Configuration webhook
MANYVIDS_WEBHOOK_SECRET=your_webhook_secret_here
MANYVIDS_VERIFY_TOKEN=your_verify_token_here

# URL API (optionnel)
MANYVIDS_BASE_URL=https://api.manyvids.com/v1
```

### **Configuration des Webhooks**

1. **URL de Callback** : `https://your-domain.com/webhook/manyvids/callback`
2. **Token de Vérification** : Utilisez `MANYVIDS_VERIFY_TOKEN`
3. **Événements** : Sélectionnez tous les événements disponibles
4. **Signature** : Activez la vérification HMAC

## 📊 **Utilisation de l'API**

### **Publication Multi-Plateformes**

```http
POST /api/platforms/publish
{
  "platforms": ["manyvids", "onlyfans", "fansly"],
  "content": {
    "title": "Vidéo Premium",
    "description": "Description de la vidéo",
    "video_url": "https://example.com/video.mp4",
    "price": 45.0,
    "is_premium": true,
    "tags": ["premium", "exclusive", "hd"],
    "category": "adult",
    "duration": 600
  },
  "agency_id": "agency_123",
  "muse_id": "muse_456"
}
```

### **Publication Directe ManyVids**

```python
from api.services.content_distributor.connectors.manyvids import publish_to_manyvids

content = {
    "title": "Ma Vidéo Premium",
    "description": "Description détaillée",
    "video_url": "https://example.com/video.mp4",
    "price": 50.0,
    "is_premium": True,
    "tags": ["premium", "exclusive", "custom"],
    "category": "adult",
    "duration": 900,
    "thumbnail_url": "https://example.com/thumb.jpg"
}

model_info = {
    "manyvids_api_key": "your_api_key",
    "manyvids_api_secret": "your_api_secret",
    "agency_id": "agency_123",
    "muse_id": "muse_456"
}

result = await publish_to_manyvids(content, model_info)
```

### **Gestion des Vidéos Personnalisées**

```python
from api.services.content_distributor.connectors.manyvids import ManyVidsConnector

connector = ManyVidsConnector("api_key", "api_secret")

# Créer une demande de vidéo personnalisée
request_data = {
    "title": "Vidéo Personnalisée",
    "description": "Description de la demande",
    "budget": 200.0,
    "deadline": "2024-02-15",
    "special_requests": "Costume spécifique et scénario personnalisé"
}

request = await connector.create_custom_video_request(request_data)

# Récupérer les demandes
requests = await connector.get_custom_video_requests(limit=20)
```

### **Messages aux Fans**

```python
# Envoyer un message payant à un fan
message_result = await connector.send_message(
    fan_id="fan_123",
    message="Message privé exclusif avec contenu premium",
    media_url="https://example.com/private.jpg",
    price=25.0
)
```

## 📈 **Analytics et Monitoring**

### **Métriques Disponibles**

#### **Revenus**
- Revenus totaux par période
- Répartition par source (ventes vidéos, vidéos personnalisées, tips, abonnements)
- Tendance des revenus
- Statut des paiements

#### **Engagement**
- Vues totales des vidéos
- Likes et interactions
- Taux d'engagement
- Vidéos les plus performantes

#### **Fans**
- Croissance des fans
- Abonnements actifs/annulés
- Dépenses moyennes par fan
- Analyse démographique

#### **Vidéos Personnalisées**
- Nombre de demandes
- Taux de completion
- Revenus générés
- Évaluations de satisfaction

### **Exemple d'Analytics**

```python
# Analytics d'une vidéo spécifique
video_analytics = await connector.get_video_analytics(
    video_id="video_123",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# Vue d'ensemble des analytics
overview = await connector.get_analytics_overview(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

print(f"Revenus totaux: {overview['total_earnings']}$")
print(f"Vues totales: {overview['total_views']:,}")
print(f"Vidéos personnalisées: {overview['custom_video_requests']}")
print(f"Taux d'engagement: {overview['engagement_rate']}%")
```

## 🔒 **Sécurité et Conformité**

### **Authentification**
- **HMAC SHA-256** pour toutes les requêtes
- **Timestamp** pour prévenir les attaques de replay
- **Signature unique** par requête
- **Headers sécurisés** avec User-Agent personnalisé

### **Validation des Webhooks**
- Vérification HMAC des signatures
- Validation des tokens de vérification
- Logging de tous les événements
- Gestion des erreurs robuste

### **Gestion des Données**
- Chiffrement des credentials
- Logs sécurisés sans données sensibles
- Conformité RGPD pour les données utilisateur
- Audit trail complet

## 📋 **Limites et Contraintes**

### **Rate Limiting**
- **100 requêtes/heure**
- **2400 requêtes/jour**
- Gestion automatique des limites
- Retry avec backoff exponentiel

### **Tailles de Fichiers**
- **Images** : 10 MB maximum
- **Vidéos** : 500 MB maximum
- Formats supportés : MP4, AVI, MOV, WebM
- Compression automatique si nécessaire

### **Contenu**
- **Titre** : 100 caractères maximum
- **Description** : 2000 caractères maximum
- **Tags** : 15 tags maximum par vidéo
- **Durée** : 5 minutes minimum, 2 heures maximum

## 🧪 **Tests et Validation**

### **Tests Unitaires**
- Tests du connecteur complet
- Tests d'upload de vidéos
- Tests des webhooks
- Tests de sécurité
- Tests d'erreurs

### **Exécution des Tests**

```bash
# Tests unitaires ManyVids
pytest tests/unit/test_manyvids_integration.py -v

# Tests avec couverture
pytest tests/unit/test_manyvids_integration.py --cov=api.services.content_distributor.connectors.manyvids
```

## 🚀 **Déploiement**

### **Prérequis**
1. Credentials API ManyVids valides
2. Configuration des webhooks
3. Variables d'environnement définies
4. Base de données MongoDB accessible

### **Étapes de Déploiement**

1. **Configuration des Variables**
   ```bash
   cp env.platforms.example .env
   # Éditer .env avec vos credentials ManyVids
   ```

2. **Configuration des Webhooks**
   - URL : `https://your-domain.com/webhook/manyvids/callback`
   - Token : Votre `MANYVIDS_VERIFY_TOKEN`
   - Événements : Tous les événements disponibles

3. **Test de l'Intégration**
   ```bash
   python scripts/demo_platforms.py
   ```

4. **Monitoring**
   - Vérifier les logs d'upload
   - Surveiller les webhooks
   - Analyser les performances

## 📚 **Documentation API ManyVids**

### **Endpoints Principaux**

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/profile` | GET | Informations du profil |
| `/videos` | POST/GET | Gestion des vidéos |
| `/videos/{id}` | GET/PUT/DELETE | Gérer une vidéo |
| `/videos/upload` | POST | Upload de vidéo |
| `/custom-videos/requests` | POST/GET | Vidéos personnalisées |
| `/fans` | GET | Liste des fans |
| `/messages` | POST/GET | Messages |
| `/earnings` | GET | Revenus |
| `/analytics/overview` | GET | Analytics globales |
| `/categories` | GET | Catégories |
| `/trending/tags` | GET | Tags tendance |

### **Codes de Réponse**

| Code | Description |
|------|-------------|
| 200 | Succès |
| 201 | Créé avec succès |
| 400 | Requête invalide |
| 401 | Non autorisé |
| 403 | Interdit |
| 404 | Non trouvé |
| 429 | Limite de taux dépassée |
| 500 | Erreur serveur |

## 🎯 **Prochaines Améliorations**

### **Fonctionnalités Futures**
1. **Streaming en direct** - Support des lives ManyVids
2. **Analytics avancées** - Tableaux de bord détaillés
3. **Automatisation** - Publication programmée
4. **Intégration CRM** - Gestion des fans
5. **Notifications push** - Alertes en temps réel

### **Optimisations**
1. **Cache intelligent** - Réduction des appels API
2. **Batch processing** - Traitement par lots
3. **Retry automatique** - Gestion des erreurs
4. **Monitoring avancé** - Métriques détaillées

---

**✅ L'intégration ManyVids.com est complète et prête à l'emploi !**

Pour plus d'informations, consultez la documentation complète des plateformes dans `PLATFORMS_INTEGRATION.md`.




