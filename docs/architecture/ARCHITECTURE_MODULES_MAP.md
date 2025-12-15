# 🗺️ Cartographie Complète des Modules - musAI Platform

> **Document généré depuis le code réel du projet**  
> Date: 2024  
> Base: Analyse exhaustive du codebase

---

## 📋 Table des Matières

1. [Vue d'ensemble de l'architecture](#vue-densemble)
2. [Carte des Modules par Couches](#carte-des-modules)
3. [Synthèse Architecturale](#synthèse)
4. [Flux Principaux End-to-End](#flux)
5. [Points de Couplage et Risques](#couplage)
6. [Opportunités de Refactorisation](#refactorisation)
7. [Next Steps](#next-steps)

---

## 🏗️ Vue d'ensemble de l'architecture {#vue-densemble}

### Architecture Générale

**musAI Platform** est une plateforme **multi-tenant** de gestion d'influenceuses (muses) avec les caractéristiques suivantes :

- **Backend**: FastAPI (Python 3.11+) avec architecture modulaire
- **Bases de données**: MongoDB (Motor async) - **2 bases distinctes** :
  - `musai_core` : Données opérationnelles temps réel (users, chats, scheduler, content)
  - `musai_bi` : Données analytiques/IA (insights, pricing, RAG 2.0)
- **Frontend**: Next.js 14 (séparé, dans `frontend/admin_panel/`)
- **Feature Flags**: Modules activables via `.env` (BI, Scheduler, CloudPhone, OTP)
- **Authentification**: JWT + Google OAuth 2.0
- **Multi-tenant**: Isolation par `org_id` partout

### Grands Domaines Fonctionnels

1. **Auth & Identity** - Authentification, autorisation, RBAC
2. **Agences & Utilisateurs** - Gestion multi-tenant, rôles, permissions
3. **Gestion des Contenus** - PPV, Public, Scheduling, Distribution
4. **Connecteurs Réseaux Sociaux** - 17+ plateformes (Instagram, TikTok, OnlyFans, etc.)
5. **Orchestration** - Dispatcher, Scheduler, Jobs
6. **Chat Omnicanal & IA** - LLM, RAG, Intent Engine, Scénarios
7. **Analytics & BI** - Insights IA, Pricing IA, Tunnels, KPIs
8. **Paiements** - Crypto (NowPayments), PPV, Subscriptions
9. **Infrastructure** - Logging, Monitoring, Health Checks, WebSockets

---

## 🗺️ Carte des Modules par Couches {#carte-des-modules}

### 1. Couche Interface / API

#### 1.1 Routes d'Authentification

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités | Endpoints |
|--------|--------|------|---------------------|---------------------|---------|-----------|
| **Auth (Email/Password)** | `api/routes/auth.py` | Authentification classique (login, register, reset password) | `api.core.auth`, `api.services.auth`, `api.schemas.auth` | `fastapi`, `jose`, `passlib` | `User`, `Token` | `POST /api/auth/login`, `POST /api/auth/register`, `POST /api/auth/reset-password` |
| **Auth Google OAuth** | `api/routes/auth_google.py` | Authentification Google OAuth 2.0 | `api.core.auth`, `api.services.auth.google_oauth` | `google-auth`, `fastapi` | `User`, `GoogleTokenRequest` | `POST /api/auth/google/login`, `POST /api/auth/google/register` |
| **Users Management** | `api/routes/users.py` | CRUD utilisateurs, gestion rôles | `api.core.auth`, `api.core.permissions`, `api.schemas.users` | `fastapi`, `pydantic` | `User`, `UserRole` | `GET /api/users`, `POST /api/users`, `PATCH /api/users/{id}` |

#### 1.2 Routes de Contenu

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités | Endpoints |
|--------|--------|------|---------------------|---------------------|---------|-----------|
| **PPV Content** | `api/routes/ppv.py` | Gestion contenu PPV (Pay-Per-View) | `api.services.content_distributor`, `api.schemas.ppv` | `fastapi`, `motor` | `PPVContent`, `PPVBundle` | `POST /api/ppv`, `GET /api/ppv/{id}`, `PATCH /api/ppv/{id}` |
| **Public Contents** | `api/routes/public_contents.py` | Gestion contenu public (posts, stories) | `api.services.content_distributor`, `api.schemas.publics` | `fastapi` | `PublicContent` | `GET /api/public-contents`, `POST /api/public-contents` |
| **Scheduler** | `api/routes/scheduler.py` | Planification et publication de contenus | `api.services.scheduler.*`, `api.schemas.scheduler` | `fastapi`, `asyncio` | `ScheduledTask`, `Draft`, `WeeklyPlan` | `POST /api/scheduler/schedule`, `GET /api/scheduler/drafts`, `POST /api/scheduler/recycle` |
| **Calendar** | `api/routes/calendar.py` | Vue calendaire unifiée (Mois/Semaine/Jour) | `api.services.calendar.service`, `api.services.calendar.ws_hub` | `fastapi`, `websockets` | `ScheduledPost`, `CalendarQuery` | `GET /api/calendar/items`, `POST /api/calendar/schedule`, `POST /api/calendar/reschedule` |
| **Dispatcher** | `api/routes/dispatcher.py` | Dispatch de contenu vers plateformes | `api.services.content_distributor.dispatcher` | `fastapi` | `Content`, `Platform` | `POST /api/dispatcher/dispatch` |

#### 1.3 Routes Chat & IA

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités | Endpoints |
|--------|--------|------|---------------------|---------------------|---------|-----------|
| **Chats** | `api/routes/chats.py` | Chat omnicanal (messages, conversations) | `api.services.chat_omnichannel.manager`, `api.schemas.chat` | `fastapi` | `ChatMessage`, `Conversation` | `POST /api/chats/send`, `GET /api/chats/history` |
| **Intent Engine** | `api/routes/intent.py` | Moteur d'intentions (LLM Pilote / Scénarios) | `api.services.intent.intent_engine`, `api.schemas.intent` | `fastapi` | `InboundEvent`, `OutboundMessage`, `ChatScenario` | `POST /api/intent/event`, `POST /api/intent/scenarios` |
| **Assistant IA** | `api/routes/assistant.py` | Assistant stratégique (alertes, collabs, plans) | `api.services.assistant.*`, `api.schemas.assistant` | `fastapi` | `Alert`, `CollabCandidate`, `Plan` | `GET /api/assistant/alerts`, `GET /api/assistant/collabs` |
| **Message Builder** | `api/routes/message_builder.py` | Construction de messages avec templates | `api.services.messaging.message_builder`, `api.schemas.message_builder` | `fastapi` | `MessageTemplate`, `Segment` | `POST /api/message-builder/build` |
| **Translator** | `api/routes/translator.py` | Traduction de contenus | `api.services.ai.translate_service` | `fastapi` | `TranslationRequest` | `POST /api/translator/translate` |

#### 1.4 Routes Analytics & BI

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités | Endpoints |
|--------|--------|------|---------------------|---------------------|---------|-----------|
| **BI Insights** | `api/routes/bi_insights.py` | Insights stratégiques IA (alertes, collabs) | `api.services.bi.insight_engine`, `api.schemas.bi_insights` | `fastapi` | `InsightAlert`, `CollabCandidate` | `POST /api/bi/insights/alerts`, `GET /api/bi/insights/alerts` |
| **BI Pricing** | `api/routes/bi_pricing.py` | Optimisation de prix IA | `api.services.bi.pricing_optimizer`, `api.schemas.bi_pricing` | `fastapi` | `PricingRecommendation` | `POST /api/bi/pricing/recommend`, `GET /api/bi/pricing/recommendations` |
| **Analytics Conversations** | `api/routes/analytics_conversations.py` | KPIs conversations | `api.services.analytics.conversation_service` | `fastapi` | `ConversationKPI` | `GET /api/analytics/conversations` |
| **Analytics BI** | `api/routes/analytics_bi.py` | Analytics BI agrégées | `api.services.analytics.*` | `fastapi` | `BIMetric` | `GET /api/analytics/bi` |
| **Tunnel Analysis** | `api/routes/analysis/tunnel.py` | Analyse de tunnels de vente | `api.services.analytics.tunnels`, `api.schemas.tunnels` | `fastapi` | `TunnelOverview`, `TunnelDetail` | `GET /api/analysis/tunnel/overview`, `GET /api/analysis/tunnel/recommendations` |
| **Stats** | `api/routes/stats.py` | Statistiques générales | `api.services.analytics.*` | `fastapi` | `Stat` | `GET /api/stats` |
| **Stats Timeline** | `api/routes/stats/timeline.py` | Timeline de statistiques | `api.services.analytics.timeline` | `fastapi` | `TimelineEvent` | `GET /api/stats/timeline` |

#### 1.5 Routes Webhooks (Plateformes)

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités | Endpoints |
|--------|--------|------|---------------------|---------------------|---------|-----------|
| **Instagram Webhook** | `api/routes/webhooks/instagram.py` | Webhooks Instagram (messages, posts) | `api.services.content_distributor.connectors.instagram` | `fastapi` | `WebhookEvent` | `POST /api/webhooks/instagram` |
| **TikTok Webhook** | `api/routes/webhooks/tiktok.py` | Webhooks TikTok | `api.services.content_distributor.connectors.tiktok` | `fastapi` | `WebhookEvent` | `POST /api/webhooks/tiktok` |
| **Telegram Webhook** | `api/routes/webhooks/telegram.py` | Webhooks Telegram Bot | `api.services.content_distributor.connectors.telegram` | `fastapi`, `python-telegram-bot` | `WebhookEvent` | `POST /api/webhooks/telegram` |
| **WhatsApp Webhook** | `api/routes/webhooks/whatsapp.py` | Webhooks WhatsApp | `api.services.content_distributor.connectors.whatsapp` | `fastapi` | `WebhookEvent` | `POST /api/webhooks/whatsapp` |
| **OnlyFans Webhook** | `api/routes/webhooks/fanvue.py` | Webhooks OnlyFans/FanVue | `api.services.content_distributor.connectors.fanvue` | `fastapi` | `WebhookEvent` | `POST /api/webhooks/fanvue` |
| **ManyVids Webhook** | `api/routes/webhooks/manyvids.py` | Webhooks ManyVids | `api.services.content_distributor.connectors.manyvids` | `fastapi` | `WebhookEvent` | `POST /api/webhooks/manyvids` |
| **MyMFans Webhook** | `api/routes/webhooks/mymfans.py` | Webhooks MyMFans | `api.services.content_distributor.connectors.mymfans` | `fastapi` | `WebhookEvent` | `POST /api/webhooks/mymfans` |
| **Payments Webhook** | `api/routes/webhooks/payments_webhook.py` | Webhooks paiements (NowPayments) | `api.services.payment_gateway.nowpayments` | `fastapi` | `PaymentEvent` | `POST /api/webhooks/payments` |

#### 1.6 Routes Infrastructure

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités | Endpoints |
|--------|--------|------|---------------------|---------------------|---------|-----------|
| **Health** | `api/routes/health.py` | Health checks (healthz, readyz) | `api.core.settings`, `api.databases.databases` | `fastapi` | - | `GET /api/healthz`, `GET /api/readyz` |
| **Platforms** | `api/routes/platforms.py` | Configuration plateformes | `api.services.platform_configs` | `fastapi` | `PlatformConfig` | `GET /api/platforms`, `POST /api/platforms` |
| **Logs** | `api/routes/logs.py` | Consultation logs | `api.services.logs.activity_logger` | `fastapi` | `LogEntry` | `GET /api/logs` |

#### 1.7 Routes Optionnelles (Feature Flags)

| Module | Chemin | Rôle | Feature Flag | Dépendances Internes | Endpoints |
|--------|--------|------|--------------|---------------------|-----------|
| **CloudPhone** | `api/routes/cloudphone.py` | Gestion devices CloudPhone | `ENABLE_CLOUDPHONE` | `api.services.cloudphone.*` | `POST /api/cloudphone/devices`, `GET /api/cloudphone/devices` |
| **OTP** | `api/routes/otp.py` | Gestion OTP (One-Time Password) | `ENABLE_OTP` | `api.services.otp.*` | `POST /api/otp/sessions`, `GET /api/otp/sessions` |

#### 1.8 WebSockets

| Module | Chemin | Rôle | Dépendances Internes | Endpoints |
|--------|------|------|---------------------|-----------|
| **Calendar WS** | `api/routes/ws_calendar.py` | WebSocket pour mises à jour calendrier temps réel | `api.services.calendar.ws_hub` | `WS /ws/calendar?org_id=...` |

---

### 2. Couche Domaine / Services Métier

#### 2.1 Services de Contenu

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités Manipulées |
|--------|--------|------|---------------------|---------------------|-------------------|
| **Content Dispatcher** | `api/services/content_distributor/dispatcher.py` | Orchestre la distribution de contenu vers les plateformes | `api.services.content_distributor.connectors.*`, `api.services.config.funnel_config` | `motor` | `Content`, `Platform`, `FunnelStage` |
| **Content Scheduler** | `api/services/content_distributor/scheduler.py` | Planification de publication | `api.services.content_distributor.dispatcher` | `asyncio`, `motor` | `ScheduledTask` |
| **Calendar Service** | `api/services/calendar/service.py` | Gestion vue calendaire (query, reschedule, duplicate) | `api.services.calendar.ws_hub` (lazy) | `motor`, `bson` | `ScheduledPost`, `CalendarQuery` |
| **Calendar WS Hub** | `api/services/calendar/ws_hub.py` | Hub WebSocket pour notifications calendrier | - | `fastapi.websockets` | - |

#### 2.2 Services Scheduler

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités Manipulées |
|--------|--------|------|---------------------|---------------------|-------------------|
| **Scheduler Engine** | `api/services/scheduler/scheduler_engine.py` | Moteur de planification principal | `api.services.scheduler.manager`, `api.services.scheduler.job_runner` | `asyncio`, `motor` | `ScheduledTask`, `Job` |
| **Scheduler Manager** | `api/services/scheduler/manager.py` | Gestion des tâches planifiées | `api.services.scheduler.task`, `api.services.content_distributor.dispatcher` | `motor` | `ScheduledTask` |
| **Job Runner** | `api/services/scheduler/job_runner.py` | Exécution des jobs planifiés | `api.services.scheduler.publish_service` | `asyncio` | `Job` |
| **Publish Service** | `api/services/scheduler/publish_service.py` | Service de publication | `api.services.content_distributor.dispatcher` | `motor` | `Content`, `Platform` |
| **Planner Service** | `api/services/scheduler/planner_service.py` | Planification hebdomadaire | `api.services.scheduler.manager` | `motor` | `WeeklyPlan` |
| **Recycle Service** | `api/services/scheduler/recycle_service.py` | Recyclage de contenus | `api.services.scheduler.manager` | `motor` | `Content` |
| **A/B Test Service** | `api/services/scheduler/abtest_service.py` | Gestion tests A/B | `api.services.scheduler.manager` | `motor` | `ABTest` |
| **AI Copy Service** | `api/services/scheduler/ai_copy_service.py` | Génération de copies IA | `api.services.chat_omnichannel.llm_service` | `motor` | `Content` |

#### 2.3 Services Chat & IA

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités Manipulées |
|--------|--------|------|---------------------|---------------------|-------------------|
| **Chat Manager** | `api/services/chat_omnichannel/manager.py` | Gestion messages chat (save, history, reply) | `api.services.chat_omnichannel.llm_service`, `api.services.chat_omnichannel.rag_service` | `motor`, `openai`, `deepseek` | `ChatMessage`, `Conversation` |
| **LLM Service** | `api/services/chat_omnichannel/llm_service.py` | Abstraction LLM (OpenAI, DeepSeek) | `api.services.chat_omnichannel.deepseek_service` (indirect) | `openai`, `httpx` | `Message`, `LLMResponse` |
| **DeepSeek Service** | `api/services/chat_omnichannel/deepseek_service.py` | Implémentation DeepSeek LLM | - | `httpx` | `Message` |
| **RAG Service** | `api/services/chat_omnichannel/rag_service.py` | RAG 1.0 (DM) - Recherche contexte | `api.services.chat_omnichannel.vector_store`, `api.services.chat_omnichannel.doc_store` | `motor`, `qdrant-client` (optionnel) | `KnowledgeChunk` |
| **Vector Store** | `api/services/chat_omnichannel/vector_store.py` | Stockage vecteurs (embeddings) | - | `qdrant-client` (optionnel) | `Vector` |
| **Doc Store** | `api/services/chat_omnichannel/doc_store.py` | Stockage documents RAG | `api.databases.databases` | `motor` | `Document` |
| **Intent Engine** | `api/services/intent/intent_engine.py` | Moteur d'intentions (Mode A: LLM Pilote, Mode B: Scénarios) | `api.services.intent.rag_unified`, `api.services.intent.llm_handler`, `api.services.intent.scenario_engine` | `motor` | `InboundEvent`, `OutboundMessage`, `ChatScenario` |
| **RAG Unified** | `api/services/intent/rag_unified.py` | RAG unifié avec boosting branding | `api.databases.databases` | `motor` | `KnowledgeChunk`, `PersonaProfile` |
| **LLM Handler** | `api/services/intent/llm_handler.py` | Handler LLM (freeform + style_rewrite) | `api.services.chat_omnichannel.llm_service` | `openai`, `deepseek` | `Message` |
| **Scenario Engine** | `api/services/intent/scenario_engine.py` | Moteur de scénarios guidés | `api.databases.databases` | `motor` | `ChatScenario`, `ChatSession` |
| **Message Validator** | `api/services/intent/validator.py` | Validation conformité messages | - | - | `Message` |
| **Channel Dispatcher** | `api/services/intent/dispatcher.py` | Dispatch multi-plateforme | `api.services.content_distributor.connectors.*` | - | `OutboundMessage` |

#### 2.4 Services Analytics & BI

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités Manipulées |
|--------|--------|------|---------------------|---------------------|-------------------|
| **Insight Engine** | `api/services/bi/insight_engine.py` | Moteur d'insights stratégiques (alertes, collabs) | `api.databases.databases.get_bi_db()` | `motor` | `InsightAlert`, `CollabCandidate` |
| **Pricing Optimizer** | `api/services/bi/pricing_optimizer.py` | Optimisation de prix IA (heuristique MVP → ML) | `api.databases.databases.get_bi_db()` | `motor` | `PricingRecommendation` |
| **RAG2 Client** | `api/services/bi/rag2_client.py` | Client RAG 2.0 (benchmarks, tendances) - Abstraction | - | `qdrant-client` (optionnel), LLM | `Benchmark`, `Trend` |
| **Conversation Service** | `api/services/analytics/conversation_service.py` | KPIs conversations | `api.databases.databases` | `motor` | `ConversationKPI` |
| **Tunnel Analysis** | `api/services/analytics/tunnels.py` | Analyse tunnels de vente | `api.databases.databases` | `motor` | `TunnelOverview`, `TunnelDetail` |
| **Forecast Service** | `api/services/analytics/forecast_service.py` | Prévisions (time series) | `api.databases.databases` | `motor`, `pandas` (optionnel) | `Forecast` |
| **Funnel Service** | `api/services/analytics/funnel_service.py` | Analyse de funnels | `api.databases.databases` | `motor` | `FunnelStage` |
| **Timeline Service** | `api/services/analytics/timeline.py` | Timeline d'événements | `api.databases.databases` | `motor` | `TimelineEvent` |
| **Events Service** | `api/services/analytics/events.py` | Gestion événements analytiques | `api.databases.databases` | `motor` | `AnalyticsEvent` |

#### 2.5 Services Assistant IA

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités Manipulées |
|--------|--------|------|---------------------|---------------------|-------------------|
| **Alerts Service** | `api/services/assistant/alerts_service.py` | Service d'alertes stratégiques | `api.services.bi.insight_engine` | `motor` | `Alert` |
| **Collab Service** | `api/services/assistant/collab_service.py` | Service de collaboration | `api.services.bi.insight_engine` | `motor` | `CollabCandidate` |
| **History Service** | `api/services/assistant/history_service.py` | Historique assistant | `api.databases.databases` | `motor` | `HistoryEntry` |
| **Plan Service** | `api/services/assistant/plan_service.py` | Plans stratégiques | `api.databases.databases` | `motor` | `Plan` |
| **Trends Service** | `api/services/assistant/trends_service.py` | Tendances marché | `api.services.bi.rag2_client` | `motor` | `Trend` |
| **Context Service** | `api/services/assistant/context_service.py` | Contexte assistant | `api.databases.databases` | `motor` | `Context` |

#### 2.6 Services Paiements

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités Manipulées |
|--------|--------|------|---------------------|---------------------|-------------------|
| **NowPayments Service** | `api/services/payment_gateway/nowpayments.py` | Intégration NowPayments (crypto) | `api.databases.databases` | `httpx` | `Payment`, `Transaction` |
| **CryptoBot Service** | `api/services/payment_gateway/cryptobot.py` | Intégration CryptoBot (optionnel) | `api.databases.databases` | `httpx` | `Payment` |

#### 2.7 Services Optionnels (Feature Flags)

| Module | Chemin | Rôle | Feature Flag | Dépendances Internes | Entités Manipulées |
|--------|--------|------|--------------|---------------------|-------------------|
| **CloudPhone Manager** | `api/services/cloudphone/manager.py` | Gestion devices CloudPhone | `ENABLE_CLOUDPHONE` | `api.services.cloudphone.cloudphone_client` | `Device`, `Slot`, `App` |
| **CloudPhone Client** | `api/services/cloudphone/cloudphone_client.py` | Client API CloudPhone | `ENABLE_CLOUDPHONE` | `httpx` | `Device` |
| **OTP Sessions** | `api/services/otp/sessions.py` | Gestion sessions OTP | `ENABLE_OTP` | `api.services.otp.providers.*` | `OTPSession` |
| **OTP Providers** | `api/services/otp/providers/registry.py` | Registry providers OTP | `ENABLE_OTP` | - | `OTPProvider` |

#### 2.8 Services Utilitaires

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Entités Manipulées |
|--------|--------|------|---------------------|---------------------|-------------------|
| **Message Builder** | `api/services/messaging/message_builder.py` | Construction messages avec templates | `api.services.messaging.template_engine` | - | `MessageTemplate` |
| **Template Engine** | `api/services/messaging/template_engine.py` | Moteur de templates | - | `jinja2` (optionnel) | `Template` |
| **Segmentation** | `api/services/messaging/segmentation.py` | Segmentation audience | `api.databases.databases` | `motor` | `Segment` |
| **Translate Service** | `api/services/ai/translate_service.py` | Traduction de contenus | `api.services.chat_omnichannel.llm_service` | `openai`, `deepseek` | `Translation` |
| **Recap Service** | `api/services/ai/recap_service.py` | Génération de récapitulatifs | `api.services.chat_omnichannel.llm_service` | `openai`, `deepseek` | `Recap` |
| **Tracking Service** | `api/services/tracking/redirect_service.py` | Tracking de liens | `api.databases.databases` | `motor` | `Link`, `Click` |
| **Activity Logger** | `api/services/logs/activity_logger.py` | Logging d'activités | `api.databases.databases` | `motor` | `ActivityLog` |

---

### 3. Couche Données / Persistance

#### 3.1 Gestion Bases de Données

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Collections Principales |
|--------|--------|------|---------------------|---------------------|------------------------|
| **Databases Manager** | `api/databases/databases.py` | Gestion connexions MongoDB (CORE + BI) | `api.core.settings` | `motor`, `pymongo` | - |
| **Core DB Helper** | `api/databases/databases.py::get_core_db()` | Accès base `musai_core` | `api.core.settings` | `motor` | `users`, `chat_messages`, `scheduled_posts`, `ppv_contents`, `public_contents`, `scheduled_tasks`, `tunnels`, `persona_profiles`, `chat_scenarios`, `chat_sessions`, `knowledge_chunks`, `chat_policies` |
| **BI DB Helper** | `api/databases/databases.py::get_bi_db()` | Accès base `musai_bi` | `api.core.settings` | `motor` | `insights_alerts`, `pricing_recommendations`, `agg_creator_stats_daily`, `agg_ppv_performance_daily`, `sales_transactions`, `fan_profiles`, `collab_candidates`, `knowledge_vectors`, `models_registry` |
| **Index Manager** | `api/databases/databases.py::ensure_all_indexes()` | Création index MongoDB | - | `motor` | Toutes collections (CORE + BI) |

#### 3.2 Schémas Pydantic

| Module | Chemin | Rôle | Entités Définies |
|--------|--------|------|-----------------|
| **Auth Schemas** | `api/schemas/auth.py` | Schémas authentification | `LoginRequest`, `TokenResponse`, `GoogleTokenRequest` |
| **User Schemas** | `api/schemas/users.py` | Schémas utilisateurs | `User`, `UserResponse`, `UserRole` (enum) |
| **Chat Schemas** | `api/schemas/chat.py` | Schémas chat | `ChatMessageIn`, `ChatMessageOut`, `Conversation` |
| **PPV Schemas** | `api/schemas/ppv.py` | Schémas PPV | `PPVContent`, `PPVBundle` |
| **Scheduler Schemas** | `api/schemas/scheduler.py` | Schémas scheduler | `ScheduledTask`, `Draft`, `WeeklyPlan` |
| **Calendar Schemas** | `api/schemas/calendar.py` | Schémas calendrier | `ScheduledPostIn`, `ScheduledPostOut`, `CalendarQuery`, `RescheduleIn` |
| **BI Insights Schemas** | `api/schemas/bi_insights.py` | Schémas insights BI | `InsightAlertIn`, `InsightAlertOut`, `CollabCandidate` |
| **BI Pricing Schemas** | `api/schemas/bi_pricing.py` | Schémas pricing BI | `PricingRecommendationIn`, `PricingRecommendationOut` |
| **Intent Schemas** | `api/schemas/intent.py` | Schémas intent engine | `InboundEvent`, `OutboundMessage`, `ChatScenario`, `PersonaProfile`, `ChatPolicies` |
| **Tunnels Schemas** | `api/schemas/tunnels.py` | Schémas tunnels | `TunnelOverviewItem`, `TunnelDetailItem`, `TunnelRecommendationsResponse` |
| **Platforms Schemas** | `api/schemas/platforms.py` | Schémas plateformes | `PlatformConfig`, `PlatformConnection` |
| **Payments Schemas** | `api/schemas/payments.py` | Schémas paiements | `Payment`, `Transaction` |

---

### 4. Couche Intégration & Connecteurs

#### 4.1 Connecteurs Plateformes Sociales

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes | Plateforme |
|--------|--------|------|---------------------|---------------------|------------|
| **Instagram Connector** | `api/services/content_distributor/connectors/instagram.py` | Publication Instagram (API Graph) | `api.services.content_distributor.logger` | `httpx`, `facebook-sdk` (optionnel) | Instagram |
| **TikTok Connector** | `api/services/content_distributor/connectors/tiktok.py` | Publication TikTok (API) | `api.services.content_distributor.logger` | `httpx` | TikTok |
| **Threads Connector** | `api/services/content_distributor/connectors/threads.py` | Publication Threads | `api.services.content_distributor.logger` | `httpx` | Threads |
| **Snapchat Connector** | `api/services/content_distributor/connectors/snapchat.py` | Publication Snapchat | `api.services.content_distributor.logger` | `httpx` | Snapchat |
| **Twitter/X Connector** | `api/services/content_distributor/connectors/twitter.py` | Publication Twitter/X | `api.services.content_distributor.logger` | `httpx`, `tweepy` (optionnel) | Twitter/X |
| **Reddit Connector** | `api/services/content_distributor/connectors/reddit.py` | Publication Reddit | `api.services.content_distributor.logger` | `httpx`, `praw` (optionnel) | Reddit |
| **Telegram Connector** | `api/services/content_distributor/connectors/telegram.py` | Publication Telegram | `api.services.content_distributor.logger` | `python-telegram-bot` | Telegram |
| **WhatsApp Connector** | `api/services/content_distributor/connectors/whatsapp.py` | Publication WhatsApp (Business API) | `api.services.content_distributor.logger` | `httpx` | WhatsApp |
| **Facebook Connector** | `api/services/content_distributor/connectors/facebook.py` | Publication Facebook | `api.services.content_distributor.logger` | `httpx`, `facebook-sdk` | Facebook |
| **Discord Connector** | `api/services/content_distributor/connectors/discord.py` | Publication Discord | `api.services.content_distributor.logger` | `httpx`, `discord.py` (optionnel) | Discord |
| **OnlyFans Connector** | `api/services/content_distributor/connectors/onlyfans.py` | Publication OnlyFans | `api.services.content_distributor.logger` | `httpx` | OnlyFans |
| **FanVue Connector** | `api/services/content_distributor/connectors/fanvue.py` | Publication FanVue | `api.services.content_distributor.logger` | `httpx` | FanVue |
| **Fansly Connector** | `api/services/content_distributor/connectors/fansly.py` | Publication Fansly | `api.services.content_distributor.logger` | `httpx` | Fansly |
| **LoyalFans Connector** | `api/services/content_distributor/connectors/loyalfans.py` | Publication LoyalFans | `api.services.content_distributor.logger` | `httpx` | LoyalFans |
| **Patreon Connector** | `api/services/content_distributor/connectors/patreon.py` | Publication Patreon | `api.services.content_distributor.logger` | `httpx` | Patreon |
| **MyMFans Connector** | `api/services/content_distributor/connectors/mymfans.py` | Publication MyMFans | `api.services.content_distributor.logger` | `httpx` | MyMFans |
| **ManyVids Connector** | `api/services/content_distributor/connectors/manyvids.py` | Publication ManyVids | `api.services.content_distributor.logger` | `httpx` | ManyVids |
| **Connector Registry** | `api/services/content_distributor/connectors/registry.py` | Registry centralisé des connecteurs | Tous les connecteurs | - | - |

#### 4.2 Intégrations Externes

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes |
|--------|--------|------|---------------------|---------------------|
| **Google OAuth** | `api/services/auth/google_oauth.py` | Authentification Google OAuth 2.0 | `api.databases.databases`, `api.core.auth` | `google-auth` |
| **NowPayments API** | `api/services/payment_gateway/nowpayments.py` | API NowPayments (crypto) | `api.databases.databases` | `httpx` |
| **CloudPhone API** | `api/services/cloudphone/cloudphone_client.py` | API CloudPhone (devices) | `api.core.settings` | `httpx` |

---

### 5. Couche Infrastructure / DevOps / Monitoring

#### 5.1 Core Infrastructure

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes |
|--------|--------|------|---------------------|---------------------|
| **Settings** | `api/core/settings.py` | Configuration centralisée (Pydantic v2) | - | `pydantic-settings` |
| **Logging** | `api/core/logging.py` | Configuration logging structuré (JSON/text) | - | `logging`, `dictConfig` |
| **Auth Core** | `api/core/auth.py` | JWT, tokens, authentification | `api.databases.databases`, `api.core.configs` | `jose`, `passlib` |
| **Permissions** | `api/core/permissions.py` | RBAC (rôles, permissions) | `api.core.auth` (lazy) | `fastapi` |
| **Security** | `api/core/security.py` | Utilitaires sécurité (hash, encrypt) | - | `passlib`, `cryptography` |
| **Configs** | `api/core/configs.py` | Configurations (SECRET_KEY, ALGORITHM) | - | - |
| **Feature Gate** | `api/core/feature_gate.py` | Feature flags runtime | `api.core.settings` | - |
| **Rate Limit** | `api/core/rate_limit.py` | Rate limiting | - | `slowapi` (optionnel) |
| **Platform Configs** | `api/core/platform_configs.py` | Configuration plateformes | `api.databases.databases` | `motor` |
| **Mailing** | `api/core/mailing.py` | Envoi emails | - | `smtplib`, `sendgrid` (optionnel) |

#### 5.2 Observability

| Module | Chemin | Rôle | Dépendances Internes | Dépendances Externes |
|--------|--------|------|---------------------|---------------------|
| **Metrics** | `api/services/observability/metrics.py` | Métriques applicatives | `api.databases.databases` | `motor` |
| **Activity** | `api/services/observability/activity.py` | Tracking d'activités | `api.databases.databases` | `motor` |

#### 5.3 Docker & DevOps

| Module | Chemin | Rôle | Dépendances |
|--------|--------|------|-------------|
| **Dockerfile** | `Dockerfile` | Build image backend FastAPI | Python 3.11, uvicorn |
| **Dockerfile Frontend** | `Dockerfile.frontend` | Build image frontend Next.js | Node.js 20 |
| **Docker Compose** | `docker-compose.yml` | Orchestration API + MongoDB | Docker Compose |
| **Makefile** | `Makefile` | Commandes DevOps | Make |

#### 5.4 Scripts

| Module | Chemin | Rôle |
|--------|--------|------|
| **Setup MongoDB BI** | `scripts/setup_musai_bi.mjs` | Création collections/indexes `musai_bi` |
| **Setup Calendar** | `scripts/calendar_setup.mjs` | Création collections/indexes calendrier |
| **Setup Intent Engine** | `scripts/intent_engine_setup.mjs` | Création collections/indexes intent |
| **Optimize Indexes** | `scripts/optimize_mongodb_indexes.py` | Optimisation index MongoDB |
| **Security Audit** | `scripts/security_audit.py` | Audit sécurité |
| **Demo Scripts** | `scripts/demo_*.py` | Scripts de démonstration |

---

## 🔄 Synthèse Architecturale {#synthèse}

### Vue d'ensemble des Domaines Fonctionnels

1. **Auth & Identity** ✅
   - Authentification email/password + Google OAuth
   - RBAC (rôles: admin, lead_agent, supervisor, strategist, operator)
   - JWT tokens, refresh tokens
   - Multi-tenant strict (`org_id`)

2. **Agences & Utilisateurs** ✅
   - Gestion organisations (`orgs`)
   - Gestion muses (`muses`)
   - Assignments, permissions par muse

3. **Gestion des Contenus** ✅
   - PPV (Pay-Per-View)
   - Public contents (posts, stories)
   - Scheduling (planification, drafts, weekly plans)
   - Calendar view (Mois/Semaine/Jour)
   - Recyclage, A/B testing

4. **Connecteurs Réseaux Sociaux** ✅
   - **17 plateformes** : Instagram, TikTok, Threads, Snapchat, Twitter/X, Reddit, Telegram, WhatsApp, Facebook, Discord, OnlyFans, FanVue, Fansly, LoyalFans, Patreon, MyMFans, ManyVids
   - Architecture modulaire (registry pattern)
   - Webhooks entrants pour chaque plateforme

5. **Orchestration** ✅
   - **Dispatcher** : Distribution de contenu vers plateformes
   - **Scheduler Engine** : Planification et exécution de jobs
   - **Job Runner** : Exécution asynchrone
   - **Funnel Config** : Configuration dynamique de tunnels

6. **Chat Omnicanal & IA** ✅
   - **Chat Manager** : Gestion messages multi-plateformes
   - **LLM Service** : Abstraction OpenAI/DeepSeek
   - **RAG 1.0** : RAG pour DM (chat)
   - **Intent Engine** : Mode A (LLM Pilote) / Mode B (Scénarios)
   - **RAG Unified** : RAG avec boosting branding
   - **Scenario Engine** : Scénarios guidés par muse

7. **Analytics & BI** ✅
   - **BI Insights** : Alertes stratégiques, détection anomalies
   - **BI Pricing** : Optimisation de prix IA (heuristique → ML)
   - **RAG 2.0** : RAG stratégique (benchmarks, tendances)
   - **Tunnel Analysis** : Analyse tunnels de vente
   - **Conversation KPIs** : Métriques conversations
   - **Forecast** : Prévisions time series

8. **Paiements** ✅
   - NowPayments (crypto)
   - CryptoBot (optionnel)
   - Webhooks paiements

9. **Infrastructure** ✅
   - Logging structuré (JSON/text)
   - Health checks (`/healthz`, `/readyz`)
   - Feature flags (BI, Scheduler, CloudPhone, OTP)
   - WebSockets (calendrier temps réel)
   - Observability (metrics, activity)

### Séparation CORE / BI

- **`musai_core`** : Données opérationnelles temps réel
  - `users`, `chat_messages`, `scheduled_posts`, `ppv_contents`, `public_contents`, `scheduled_tasks`, `tunnels`, `persona_profiles`, `chat_scenarios`, `chat_sessions`, `knowledge_chunks`, `chat_policies`

- **`musai_bi`** : Données analytiques/IA
  - `insights_alerts`, `pricing_recommendations`, `agg_creator_stats_daily`, `agg_ppv_performance_daily`, `sales_transactions`, `fan_profiles`, `collab_candidates`, `knowledge_vectors`, `models_registry`

---

## 🔀 Flux Principaux End-to-End {#flux}

### Flux 1 : Publication de Contenu Planifié

1. **Création** : `POST /api/scheduler/schedule` → `api/routes/scheduler.py`
2. **Validation** : `api/schemas/scheduler.py` (Pydantic)
3. **Stockage** : `api/services/scheduler/manager.py` → MongoDB `musai_core.scheduled_tasks`
4. **Planification** : `api/services/scheduler/scheduler_engine.py` (loop asyncio)
5. **Exécution** : `api/services/scheduler/job_runner.py` → `api/services/scheduler/publish_service.py`
6. **Dispatch** : `api/services/content_distributor/dispatcher.py`
7. **Connexion Plateforme** : `api/services/content_distributor/connectors/{platform}.py`
8. **Publication** : API externe (Instagram Graph, TikTok API, etc.)
9. **Logging** : `api/services/content_distributor/logger.py` → MongoDB
10. **Notification** : WebSocket (optionnel) → `api/services/calendar/ws_hub.py`

### Flux 2 : Chat Omnicanal avec IA

1. **Réception Webhook** : `POST /api/webhooks/{platform}` → `api/routes/webhooks/{platform}.py`
2. **Parsing** : Extraction message utilisateur
3. **Stockage** : `api/services/chat_omnichannel/manager.py::save_message()` → MongoDB `musai_core.chat_messages`
4. **Intent Engine** : `api/services/intent/intent_engine.py`
   - **Mode A (LLM Pilote)** :
     - RAG Unified : `api/services/intent/rag_unified.py` → Contexte + Branding
     - LLM Handler : `api/services/intent/llm_handler.py` → Génération réponse
   - **Mode B (Scénario)** :
     - Scenario Engine : `api/services/intent/scenario_engine.py` → Sélection scénario
     - Exécution étapes → LLM styling optionnel
5. **Validation** : `api/services/intent/validator.py` (conformité)
6. **Dispatch** : `api/services/intent/dispatcher.py` → Plateforme cible
7. **Stockage Réponse** : `api/services/chat_omnichannel/manager.py::save_message()` (role='bot')
8. **Analytics** : `api/services/analytics/events.py` → Événement conversation

### Flux 3 : Assistant Stratégique IA

1. **Détection** : Job périodique → `api/services/bi/insight_engine.py::detect_reach_drop()`
2. **RAG 2.0** : `api/services/bi/rag2_client.py` → Benchmarks, tendances
3. **Analyse** : Calculs sur `musai_bi.agg_creator_stats_daily`
4. **Alerte** : `api/services/bi/insight_engine.py::record_alert()` → MongoDB `musai_bi.insights_alerts`
5. **Exposition** : `GET /api/bi/insights/alerts` → `api/routes/bi_insights.py`
6. **Frontend** : Dashboard insights

### Flux 4 : Optimisation de Prix IA

1. **Requête** : `POST /api/bi/pricing/recommend` → `api/routes/bi_pricing.py`
2. **Service** : `api/services/bi/pricing_optimizer.py::recommend_price()`
3. **Calcul** : Heuristique MVP (taux conversion estimé) → ML (futur)
4. **Stockage** : MongoDB `musai_bi.pricing_recommendations`
5. **Retour** : Recommandation (prix, confiance, gain prédit)

### Flux 5 : Authentification Google OAuth

1. **Frontend** : `@react-oauth/google` → Google consent screen
2. **Token** : `id_token` Google → `POST /api/auth/google/login`
3. **Vérification** : `api/services/auth/google_oauth.py::verify_google_token()`
4. **User** : `api/services/auth/google_oauth.py::get_or_create_google_user()`
   - Recherche par `email` ou `google_id`
   - Création si inexistant
5. **JWT** : `api/core/auth.py::create_access_token()` → Token interne
6. **Retour** : `{access_token, user}` → Frontend
7. **Stockage** : Frontend → `localStorage`

---

## ⚠️ Points de Couplage Fort et Risques {#couplage}

### 1. Couplage Fort API ↔ Persistance

- **Problème** : Routes importent directement `api.databases.databases` (pas de repository pattern)
- **Risque** : Difficile de tester, changer de DB, ou mock
- **Impact** : Moyen
- **Recommandation** : Introduire des repositories/interfaces

### 2. Dépendances Circulaires (Corrigées)

- ✅ **Corrigé** : `api/core/permissions.py` ↔ `api/core/auth.py` (import lazy)
- ✅ **Corrigé** : `api/services/chat_omnichannel/llm_service.py` ↔ `deepseek_service.py` (import direct dans manager)

### 3. Duplication de Logique

- **Problème** : `api/core/dependencies.py` duplique `api/core/auth.py::get_current_user()`
- **Risque** : Incohérences, maintenance difficile
- **Impact** : Faible (un fichier semble legacy)
- **Recommandation** : Supprimer `dependencies.py` ou unifier

### 4. Code Dupliqué dans `main.py`

- **Problème** : Imports de routes dupliqués (lignes 35-69 et 565-598)
- **Risque** : Confusion, maintenance
- **Impact** : Faible
- **Recommandation** : Nettoyer les duplications

### 5. Schémas Mélangés avec Routes

- **Problème** : `api/schemas/tunnel_analysis.py` contenait du code de route (corrigé)
- **Risque** : Violation séparation des couches
- **Impact** : Faible (corrigé)
- **Recommandation** : Audit similaire sur autres schémas

### 6. Feature Flags Non Centralisés

- **Problème** : Certains modules vérifient des flags directement dans le code
- **Risque** : Incohérences, oubli de vérifications
- **Impact** : Moyen
- **Recommandation** : Utiliser `api/core/feature_gate.py` partout

### 7. Connecteurs Plateformes : Stubs vs Réels

- **Problème** : Certains connecteurs sont des stubs (MVP)
- **Risque** : Erreurs en production si utilisés
- **Impact** : Élevé si plateforme critique
- **Recommandation** : Documenter état (stub/real) dans chaque connecteur

---

## 🔧 Opportunités de Refactorisation {#refactorisation}

### 1. Repository Pattern

**Objectif** : Découpler API de persistance

**Actions** :
- Créer `api/repositories/` avec interfaces
- Implémenter `UserRepository`, `ContentRepository`, etc.
- Injecter dans services (pas dans routes)

**Bénéfices** : Testabilité, flexibilité DB, mock facile

### 2. Domain-Driven Design (DDD)

**Objectif** : Clarifier bounded contexts

**Actions** :
- Regrouper par domaine : `auth/`, `content/`, `chat/`, `analytics/`, `payments/`
- Chaque domaine = package indépendant
- Interfaces publiques claires

**Bénéfices** : Maintenabilité, évolutivité, onboarding

### 3. Event-Driven Architecture (Optionnel)

**Objectif** : Découpler modules via événements

**Actions** :
- Introduire bus d'événements (Redis Pub/Sub ou RabbitMQ)
- Émettre événements : `ContentPublished`, `MessageReceived`, `AlertTriggered`
- Consumers asynchrones

**Bénéfices** : Scalabilité, résilience, découplage

### 4. Service Layer Unifié

**Objectif** : Harmoniser signatures de services

**Actions** :
- Interface `BaseService` avec méthodes communes
- Typage strict (TypeHints partout)
- Gestion d'erreurs unifiée

**Bénéfices** : Cohérence, maintenabilité

### 5. Configuration Externalisée

**Objectif** : Centraliser configs plateformes

**Actions** :
- Déplacer configs connecteurs → MongoDB `platform_configs`
- API de gestion : `GET /api/platforms`, `POST /api/platforms`
- Cache en mémoire (TTL)

**Bénéfices** : Dynamisme, pas de redéploiement

### 6. Tests Structure

**Objectif** : Améliorer couverture tests

**Actions** :
- Tests unitaires : `tests/unit/services/`
- Tests intégration : `tests/integration/`
- Tests E2E : `tests/e2e/`
- Fixtures : `tests/conftest.py`

**Bénéfices** : Confiance, régression détectée tôt

---

## 🚀 Next Steps {#next-steps}

### 1. Modules à Analyser en Profondeur

**Priorité Haute** :
- `api/services/content_distributor/dispatcher.py` (orchestration critique)
- `api/services/scheduler/scheduler_engine.py` (planification)
- `api/services/chat_omnichannel/manager.py` (chat core)
- `api/services/intent/intent_engine.py` (IA chat)

**Priorité Moyenne** :
- `api/services/bi/insight_engine.py` (détection MVP → ML)
- `api/services/bi/pricing_optimizer.py` (heuristique → ML)
- Tous les connecteurs plateformes (état stub/real)

### 2. Parties Critiques pour Fonctionnement Global

1. **`api/databases/databases.py`** : Point central, toutes les opérations DB
2. **`api/core/settings.py`** : Configuration, feature flags
3. **`api/core/auth.py`** : Authentification, sécurité
4. **`api/main.py`** : Point d'entrée, montage routes
5. **`api/services/content_distributor/dispatcher.py`** : Distribution contenu
6. **`api/services/scheduler/scheduler_engine.py`** : Planification

### 3. Ordre de Lecture Recommandé (Onboarding)

**Jour 1 : Fondations**
1. `README.md` (vue d'ensemble)
2. `api/core/settings.py` (configuration)
3. `api/databases/databases.py` (persistance)
4. `api/core/auth.py` (authentification)
5. `api/main.py` (point d'entrée)

**Jour 2 : Domaines Métier**
6. `api/routes/auth.py` + `api/services/auth/` (auth)
7. `api/routes/scheduler.py` + `api/services/scheduler/` (scheduling)
8. `api/routes/ppv.py` + `api/services/content_distributor/` (contenu)
9. `api/routes/chats.py` + `api/services/chat_omnichannel/` (chat)

**Jour 3 : IA & Analytics**
10. `api/routes/intent.py` + `api/services/intent/` (intent engine)
11. `api/routes/bi_insights.py` + `api/services/bi/` (BI)
12. `api/routes/analytics_*.py` + `api/services/analytics/` (analytics)

**Jour 4 : Connecteurs & Intégrations**
13. `api/services/content_distributor/connectors/` (connecteurs)
14. `api/routes/webhooks/` (webhooks)
15. `api/services/payment_gateway/` (paiements)

**Jour 5 : Infrastructure & Tests**
16. `api/core/logging.py`, `api/routes/health.py` (infra)
17. `tests/` (structure tests)
18. `scripts/` (scripts utilitaires)

### 4. Actions Immédiates Recommandées

1. ✅ **Nettoyer `main.py`** : Supprimer duplications imports
2. ✅ **Supprimer `api/core/dependencies.py`** : Legacy, utiliser `auth.py`
3. ✅ **Documenter état connecteurs** : Stub vs Real dans chaque fichier
4. ✅ **Audit feature flags** : Utiliser `feature_gate.py` partout
5. ✅ **Tests smoke** : Compléter `chat_tests/test_health.py`

---

## 📊 Statistiques du Codebase

- **Routes** : ~66 fichiers
- **Services** : ~128 fichiers
- **Schémas** : ~28 fichiers
- **Connecteurs Plateformes** : 17
- **Bases MongoDB** : 2 (CORE + BI)
- **Feature Flags** : 4 (BI, Scheduler, CloudPhone, OTP)
- **Tests** : Structure présente, couverture à améliorer

---

**Document généré automatiquement depuis le code réel du projet.**  
**Dernière mise à jour** : Analyse complète du codebase 2024



