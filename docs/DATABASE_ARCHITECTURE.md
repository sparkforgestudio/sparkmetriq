# docs/DATABASE_ARCHITECTURE.md
"""
# Architecture des Bases de Données - musAI Platform

## Vue d'ensemble

L'architecture utilise **2 bases de données MongoDB distinctes** pour séparer les responsabilités :

1. **Base Core** (`musai_core`) : Données principales de l'application
2. **Base BI** (`musai_bi`) : Analytics, scraping et données de business intelligence

## Séparation des responsabilités

### Base Core (`musai_core`)

**Usage** : Données critiques et opérationnelles de l'application

**Collections** :
- `users` - Utilisateurs et authentification
- `org_entitlements` - Entitlements par organisation
- `profiles` - Profils CloudPhone
- `devices` - Devices CloudPhone
- `device_app_slots` - Slots d'applications
- `bindings_appaccount_slot` - Liaisons app/slot
- `otp_sessions` - Sessions OTP
- `chat_messages` - Messages de conversation
- `payments` - Paiements et transactions
- `tunnels` - Tunnels de connexion
- `ppv_logs` - Logs PPV

**Services utilisant Core** :
- `api.services.auth`
- `api.services.users`
- `api.services.cloudphone.*`
- `api.services.otp.*`
- `api.services.chat_omnichannel.*`
- `api.services.payment_gateway.*`

### Base BI (`musai_bi`)

**Usage** : Analytics, business intelligence et données scrapées

**Collections** :
- `events_funnel` - Événements de funnel
- `conversation_daily` - Métriques conversation quotidiennes
- `revenue_daily` - Revenus quotidiens
- `ppv_daily` - PPV quotidiens
- `scheduled_drafts` - Brouillons programmés
- `scheduled_jobs` - Jobs programmés
- `publish_logs` - Logs de publication
- `ai_action_plans` - Plans d'action IA
- `ai_alerts` - Alertes IA
- `ai_collab_suggestions` - Suggestions de collaboration
- `ai_reco_history` - Historique des recommandations
- `trends_cache` - Cache des tendances
- `rag_documents` - Documents pour RAG marketing
- `rag_embeddings` - Embeddings vectoriels
- `scraped_contents` - Contenus scrapés
- `creator_analytics` - Analytics des créateurs
- `platform_metrics` - Métriques des plateformes
- `chat_threads` - Threads de conversation (BI)
- `fan_tags` - Tags des fans
- `fan_notes` - Notes des fans
- `operator_roles` - Rôles des opérateurs
- `muse_assignments` - Assignations des muses
- `audit_events` - Événements d'audit
- `muse_metrics_daily` - Métriques quotidiennes des muses

**Services utilisant BI** :
- `api.services.analytics.*`
- `api.services.assistant.*`
- `api.services.scheduler.*`
- `api.services.talent.*`
- `api.services.ai_marketing.*`
- `api.services.logs.*`

## Configuration

### Variables d'environnement

```bash
# Base Core (données principales)
MONGO_URI=mongodb://localhost:27017
DB_NAME_CORE=musai_core

# Base BI (analytics et scraping)
MONGO_URI_BI=mongodb://localhost:27017  # Peut être différent
DB_NAME_BI=musai_bi
```

### Connexions

```python
from api.databases.databases import get_core_db, get_bi_db

# Base Core
db_core = get_core_db()

# Base BI
db_bi = get_bi_db()

# Fonction automatique
from api.databases.databases import get_db_for_collection
db = get_db_for_collection('users')  # Retourne db_core
db = get_db_for_collection('ai_action_plans')  # Retourne db_bi
```

## RAG et Bases de Données

### RAG Chat (Base Core)

**Service** : `api.services.chat_omnichannel.rag_service`

**Usage** : Recherche dans les conversations et documents de chat

**Collections** :
- `chat_messages` - Messages de conversation
- `chat_documents` - Documents de chat (si applicable)

### RAG Marketing (Base BI)

**Service** : `api.services.ai_marketing.rag_system`

**Usage** : Recommandations marketing et analytics

**Collections** :
- `rag_documents` - Documents pour recommandations
- `rag_embeddings` - Embeddings vectoriels
- `scraped_contents` - Contenus scrapés des plateformes

## Migration

### Script de migration

```bash
python scripts/migrate_databases_separation.py
```

**Étapes** :
1. Création des index sur les deux bases
2. Migration des collections Core
3. Migration des collections BI
4. Vérification des données
5. Nettoyage optionnel de l'ancienne base

### Mise à jour des imports

```bash
python scripts/update_database_imports.py
```

Met à jour automatiquement les imports selon le type de service.

## Index et Performance

### Index Core

```javascript
// Users
db.users.createIndex({email: 1}, {unique: true})
db.users.createIndex({org_id: 1})

// CloudPhone
db.profiles.createIndex({org_id: 1, name: 1}, {unique: true})
db.devices.createIndex({org_id: 1})
db.device_app_slots.createIndex({device_id: 1, app: 1})

// OTP
db.otp_sessions.createIndex({org_id: 1, state: 1})
db.otp_sessions.createIndex({session_id: 1}, {unique: true})
db.otp_sessions.createIndex({expires_at: 1}, {expireAfterSeconds: 0})

// Chat
db.chat_messages.createIndex({conversation_id: 1, timestamp: 1})
db.chat_messages.createIndex({org_id: 1, muse_id: 1, platform: 1})
```

### Index BI

```javascript
// Analytics
db.events_funnel.createIndex({tenant_id: 1, muse_id: 1, phase: 1, ts: 1})
db.conversation_daily.createIndex({tenant_id: 1, muse_id: 1, day: 1}, {unique: true})
db.revenue_daily.createIndex({tenant_id: 1, muse_id: 1, day: 1}, {unique: true})

// RAG Marketing
db.rag_documents.createIndex({tenant_id: 1, muse_id: 1})
db.rag_documents.createIndex({content_type: 1, created_at: -1})
db.rag_embeddings.createIndex({document_id: 1}, {unique: true})

// Scraped content
db.scraped_contents.createIndex({platform: 1, creator_id: 1, scraped_at: -1})
db.creator_analytics.createIndex({creator_id: 1, platform: 1, date: -1})
```

## Avantages de cette architecture

### 1. Séparation des responsabilités
- **Core** : Données critiques, faible latence
- **BI** : Analytics, traitement en batch

### 2. Performance
- Index optimisés par usage
- Requêtes plus rapides
- Moins de contention

### 3. Scalabilité
- Bases indépendantes
- Scaling horizontal possible
- Réplication différenciée

### 4. Maintenance
- Backup/restore séparés
- Monitoring ciblé
- Évolutions indépendantes

### 5. Sécurité
- Accès différenciés
- Chiffrement par base
- Audit séparé

## Monitoring

### Métriques Core
- TPS (Transactions Per Second)
- Latence des requêtes
- Taille des collections
- Index hit ratio

### Métriques BI
- Taille des données scrapées
- Performance des agrégations
- Latence des requêtes analytics
- Utilisation du RAG

## Backup et Restore

### Core (Critique)
- Backup quotidien
- RTO : 1 heure
- RPO : 15 minutes

### BI (Moins critique)
- Backup hebdomadaire
- RTO : 4 heures
- RPO : 1 heure

## Évolutions futures

### Microservices
- Base Core → Service Core
- Base BI → Service Analytics
- API Gateway pour l'accès

### Data Lake
- Base BI → Data Lake (S3, MinIO)
- Analytics → Spark/Presto
- RAG → Vector Database (Pinecone, Weaviate)

---

**Note** : Cette architecture est conçue pour évoluer avec les besoins de l'application tout en maintenant la performance et la maintenabilité.



