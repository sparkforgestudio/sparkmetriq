# Classification des modules pour migration CORE / PRODUCT

## Légende
- **[CORE]** : Module générique réutilisable (saasentialcore)
- **[PRODUCT:sparkmetriq]** : Module spécifique au domaine Sparkmetriq
- **[MIXED/À DISCUTER]** : Module mixte nécessitant un split

---

## Tableau de classification

| Fichier / Module | Catégorie cible | Raison |
|------------------|-----------------|--------|
| **AUTHENTIFICATION & SÉCURITÉ** |
| `api/core/auth.py` | [CORE] | Authentification générique (JWT, tokens, get_current_user) |
| `api/core/security.py` | [CORE] | Utilitaires de sécurité génériques (hash, validation) |
| `api/core/configs.py` | [CORE] | Configuration générique (SECRET_KEY, ALGORITHM) |
| `api/routes/auth.py` | [CORE] | Routes d'authentification génériques (login/password) |
| `api/routes/auth_google.py` | [MIXED/À DISCUTER] | OAuth Google : séparer en core_oauth (générique) + sparkmetriq_google (spécifique) |
| `api/services/auth/google_oauth.py` | [MIXED/À DISCUTER] | OAuth Google : partie générique vers core, partie config vers sparkmetriq |
| `api/auth/google/login.py` | [MIXED/À DISCUTER] | OAuth Google : même traitement que auth_google |
| **ORGANISATIONS & UTILISATEURS** |
| `api/routes/users.py` | [CORE] | Gestion générique des utilisateurs (CRUD, rôles) |
| `api/routes/orgs.py` | [CORE] | Gestion des organisations et entitlements (multitenant) |
| `api/services/orgs.py` | [CORE] | Service générique de gestion des organisations |
| `api/models/users.py` | [CORE] | Modèles génériques d'utilisateurs |
| `api/models/user_model.py` | [CORE] | Modèles génériques d'utilisateurs |
| `api/schemas/users.py` | [CORE] | Schémas génériques d'utilisateurs |
| `api/core/permissions.py` | [CORE] | Système RBAC générique (rôles, permissions) |
| `api/core/dependencies.py` | [CORE] | Dépendances FastAPI génériques (injection) |
| **SCHEDULER** |
| `api/routes/scheduler.py` | [MIXED/À DISCUTER] | Routes scheduler : partie générique (jobs, retries) vers core, partie spécifique (drafts, AB tests, recycle) vers sparkmetriq |
| `api/services/scheduler/scheduler_engine.py` | [CORE] | Moteur de planification générique (jobs, status, retries) |
| `api/services/scheduler/manager.py` | [MIXED/À DISCUTER] | Manager : partie générique (job management) vers core, partie spécifique (UnifiedPostPayload) vers sparkmetriq |
| `api/services/scheduler/job_runner.py` | [CORE] | Exécution générique des jobs planifiés |
| `api/services/scheduler/task.py` | [CORE] | Modèle générique de tâche planifiée |
| `api/services/scheduler/config.py` | [CORE] | Configuration générique du scheduler (JobStatus, MAX_ATTEMPTS) |
| `api/services/scheduler/logger.py` | [CORE] | Logging générique du scheduler |
| `api/services/scheduler/quotas_service.py` | [MIXED/À DISCUTER] | Quotas : logique générique vers core, vérification UnifiedPostPayload vers sparkmetriq |
| `api/services/scheduler/publish_service.py` | [PRODUCT:sparkmetriq] | Service de publication spécifique (utilise dispatcher Sparkmetriq) |
| `api/services/scheduler/planner_service.py` | [PRODUCT:sparkmetriq] | Planification de contenu spécifique (drafts, weekly plan) |
| `api/services/scheduler/abtest_service.py` | [PRODUCT:sparkmetriq] | AB testing spécifique au domaine Sparkmetriq |
| `api/services/scheduler/recycle_service.py` | [PRODUCT:sparkmetriq] | Recyclage de contenu spécifique Sparkmetriq |
| `api/services/scheduler/ai_copy_service.py` | [PRODUCT:sparkmetriq] | Génération IA de contenu spécifique |
| `api/repositories/jobs_repository.py` | [CORE] | Repository générique des jobs |
| `api/schemas/scheduler.py` | [MIXED/À DISCUTER] | Schémas : partie générique (Job, Status) vers core, partie spécifique (Draft, ABTest) vers sparkmetriq |
| `api/schemas/job_details_schema.py` | [CORE] | Schéma générique de détails de job |
| `api/routes/scheduler_stats.py` | [PRODUCT:sparkmetriq] | Statistiques spécifiques du scheduler Sparkmetriq |
| **QUOTAS** |
| `api/routes/admin_quotas.py` | [CORE] | Routes d'administration des quotas (générique) |
| `api/repositories/quotas_repository.py` | [CORE] | Repository générique des quotas (shim vers saasentialcore) |
| `api/schemas/quotas_schema.py` | [CORE] | Schémas génériques des quotas |
| `api/exceptions/quotas.py` | [CORE] | Exceptions génériques de quotas |
| `api/services/core/saasential_bridge.py` | [MIXED/À DISCUTER] | Bridge : partie générique vers core, partie UnifiedPostPayload vers sparkmetriq |
| `api/core/saasentialcore_deps.py` | [CORE] | Dépendances centralisées saasentialcore |
| **OBSERVABILITÉ** |
| `api/routes/metrics.py` | [CORE] | Route générique d'exposition Prometheus |
| `api/routes/health.py` | [CORE] | Routes génériques de santé (healthz, readyz) |
| `api/services/observability/metrics.py` | [CORE] | Service générique de métriques Prometheus |
| `api/services/observability/activity.py` | [CORE] | Logging structuré générique d'activité |
| `api/core/logging.py` | [CORE] | Configuration générique du logging |
| **DATABASES & REPOSITORIES** |
| `api/databases/databases.py` | [CORE] | Gestion générique des connexions MongoDB (CORE/BI) |
| `api/repositories/__init__.py` | [CORE] | Initialisation générique des repositories |
| **CONFIGURATION** |
| `api/core/settings.py` | [MIXED/À DISCUTER] | Settings : partie générique (DB, security) vers core, partie feature flags spécifiques vers sparkmetriq |
| `api/core/feature_gate.py` | [CORE] | Feature flags génériques |
| `api/core/platform_configs.py` | [PRODUCT:sparkmetriq] | Configuration spécifique des plateformes Sparkmetriq |
| `api/core/rate_limit.py` | [CORE] | Rate limiting générique |
| `api/core/mailing.py` | [CORE] | Service générique d'envoi d'emails |
| **CONTENU & DISTRIBUTION** |
| `api/routes/dispatcher.py` | [PRODUCT:sparkmetriq] | Dispatch de contenu spécifique (utilise UnifiedPostPayload) |
| `api/services/content_distributor/dispatcher.py` | [PRODUCT:sparkmetriq] | Dispatcher de contenu spécifique Sparkmetriq |
| `api/services/content_distributor/scheduler.py` | [PRODUCT:sparkmetriq] | Planification de distribution spécifique |
| `api/services/content_distributor/logger.py` | [PRODUCT:sparkmetriq] | Logger spécifique du dispatcher |
| `api/services/content_distributor/connectors/base.py` | [CORE] | Classe abstraite générique de connecteur |
| `api/services/content_distributor/connectors/registry.py` | [CORE] | Registry générique des connecteurs |
| `api/services/content_distributor/connectors/instagram.py` | [PRODUCT:sparkmetriq] | Connecteur Instagram spécifique (modèle Sparkmetriq) |
| `api/services/content_distributor/connectors/telegram.py` | [PRODUCT:sparkmetriq] | Connecteur Telegram spécifique |
| `api/services/content_distributor/connectors/tiktok.py` | [PRODUCT:sparkmetriq] | Connecteur TikTok spécifique |
| `api/services/content_distributor/connectors/threads.py` | [PRODUCT:sparkmetriq] | Connecteur Threads spécifique |
| `api/services/content_distributor/connectors/snapchat.py` | [PRODUCT:sparkmetriq] | Connecteur Snapchat spécifique |
| `api/services/content_distributor/connectors/twitter.py` | [PRODUCT:sparkmetriq] | Connecteur Twitter spécifique |
| `api/services/content_distributor/connectors/facebook.py` | [PRODUCT:sparkmetriq] | Connecteur Facebook spécifique |
| `api/services/content_distributor/connectors/reddit.py` | [PRODUCT:sparkmetriq] | Connecteur Reddit spécifique |
| `api/services/content_distributor/connectors/whatsapp.py` | [PRODUCT:sparkmetriq] | Connecteur WhatsApp spécifique |
| `api/services/content_distributor/connectors/discord.py` | [PRODUCT:sparkmetriq] | Connecteur Discord spécifique |
| `api/services/content_distributor/connectors/onlyfans.py` | [PRODUCT:sparkmetriq] | Connecteur OnlyFans spécifique |
| `api/services/content_distributor/connectors/fansly.py` | [PRODUCT:sparkmetriq] | Connecteur Fansly spécifique |
| `api/services/content_distributor/connectors/fanvue.py` | [PRODUCT:sparkmetriq] | Connecteur Fanvue spécifique |
| `api/services/content_distributor/connectors/mymfans.py` | [PRODUCT:sparkmetriq] | Connecteur MYM.fans spécifique |
| `api/services/content_distributor/connectors/manyvids.py` | [PRODUCT:sparkmetriq] | Connecteur ManyVids spécifique |
| `api/services/content_distributor/connectors/loyalfans.py` | [PRODUCT:sparkmetriq] | Connecteur LoyalFans spécifique |
| `api/services/content_distributor/connectors/patreon.py` | [PRODUCT:sparkmetriq] | Connecteur Patreon spécifique |
| `api/schemas/payload_schema.py` | [PRODUCT:sparkmetriq] | Schéma UnifiedPostPayload spécifique Sparkmetriq |
| `api/routes/public_contents.py` | [PRODUCT:sparkmetriq] | Gestion de contenu public spécifique (muses, agences) |
| `api/schemas/publics.py` | [PRODUCT:sparkmetriq] | Schémas de contenu public spécifique |
| **MUSES & DOMAINE SPARKMETRIQ** |
| `api/routes/muses.py` | [PRODUCT:sparkmetriq] | Gestion des muses spécifique au domaine Sparkmetriq |
| `api/schemas/muses.py` | [PRODUCT:sparkmetriq] | Schémas des muses spécifiques |
| **TUNNELS** |
| `api/routes/tunnels_test.py` | [PRODUCT:sparkmetriq] | Routes de test des tunnels (concept spécifique Sparkmetriq) |
| `api/routes/tunnel_analysis.py` | [PRODUCT:sparkmetriq] | Analyse des tunnels spécifique |
| `api/routes/analysis/tunnel.py` | [PRODUCT:sparkmetriq] | Analyse avancée des tunnels |
| `api/services/tunnels.py` | [PRODUCT:sparkmetriq] | Service d'analyse des tunnels |
| `api/schemas/tunnels.py` | [PRODUCT:sparkmetriq] | Schémas des tunnels spécifiques |
| `api/schemas/tunnel_analysis.py` | [PRODUCT:sparkmetriq] | Schémas d'analyse des tunnels |
| `api/stats/tunnels.py` | [PRODUCT:sparkmetriq] | Statistiques des tunnels |
| **STATS & ANALYTICS** |
| `api/routes/stats.py` | [PRODUCT:sparkmetriq] | Routes de statistiques spécifiques Sparkmetriq |
| `api/routes/stats_tunnels.py` | [PRODUCT:sparkmetriq] | Statistiques des tunnels |
| `api/routes/stats_export.py` | [PRODUCT:sparkmetriq] | Export de statistiques |
| `api/routes/stats/base.py` | [PRODUCT:sparkmetriq] | Stats de base spécifiques |
| `api/routes/stats/timeline.py` | [PRODUCT:sparkmetriq] | Timeline de stats spécifique |
| `api/routes/stats/tunnels.py` | [PRODUCT:sparkmetriq] | Stats tunnels spécifiques |
| `api/routes/analytics.py` | [PRODUCT:sparkmetriq] | Analytics spécifiques Sparkmetriq |
| `api/routes/analytics_bi.py` | [PRODUCT:sparkmetriq] | Analytics BI spécifiques |
| `api/routes/analytics_conversations.py` | [PRODUCT:sparkmetriq] | Analytics conversations spécifiques |
| `api/routes/analytics_muses.py` | [PRODUCT:sparkmetriq] | Analytics muses spécifiques |
| `api/services/analytics/events.py` | [PRODUCT:sparkmetriq] | Service d'événements analytics spécifiques |
| `api/services/analytics/conversation_service.py` | [PRODUCT:sparkmetriq] | Service analytics conversations spécifique |
| `api/services/analytics/forecast_service.py` | [PRODUCT:sparkmetriq] | Service de prévision spécifique |
| `api/services/analytics/funnel_service.py` | [PRODUCT:sparkmetriq] | Service de funnel spécifique |
| `api/services/analytics/materialize_jobs.py` | [PRODUCT:sparkmetriq] | Matérialisation jobs spécifique |
| `api/services/analytics/timeline.py` | [PRODUCT:sparkmetriq] | Timeline analytics spécifique |
| `api/services/analytics/tunnel_analysis.py` | [PRODUCT:sparkmetriq] | Analyse tunnels spécifique |
| `api/services/analytics/tunnels.py` | [PRODUCT:sparkmetriq] | Service tunnels analytics spécifique |
| `api/schemas/analytics.py` | [PRODUCT:sparkmetriq] | Schémas analytics spécifiques |
| **BI (BUSINESS INTELLIGENCE)** |
| `api/routes/bi_insights.py` | [PRODUCT:sparkmetriq] | Routes BI Insights spécifiques |
| `api/routes/bi_pricing.py` | [PRODUCT:sparkmetriq] | Routes BI Pricing spécifiques |
| `api/services/bi/insight_engine.py` | [PRODUCT:sparkmetriq] | Moteur d'insights BI spécifique |
| `api/services/bi/pricing_optimizer.py` | [PRODUCT:sparkmetriq] | Optimiseur de pricing spécifique |
| `api/services/bi/rag2_client.py` | [PRODUCT:sparkmetriq] | Client RAG2 spécifique BI |
| `api/schemas/bi_insights.py` | [PRODUCT:sparkmetriq] | Schémas BI Insights spécifiques |
| `api/schemas/bi_pricing.py` | [PRODUCT:sparkmetriq] | Schémas BI Pricing spécifiques |
| **AI MARKETING** |
| `api/routes/ai_marketing.py` | [PRODUCT:sparkmetriq] | Routes AI Marketing spécifiques |
| `api/services/ai_marketing/creator_analyzer.py` | [PRODUCT:sparkmetriq] | Analyseur de créateurs spécifique |
| `api/services/ai_marketing/data_collector.py` | [PRODUCT:sparkmetriq] | Collecteur de données spécifique |
| `api/services/ai_marketing/logger.py` | [PRODUCT:sparkmetriq] | Logger AI Marketing spécifique |
| `api/services/ai_marketing/rag_system.py` | [PRODUCT:sparkmetriq] | Système RAG spécifique |
| `api/services/ai_marketing/recommendation_engine.py` | [PRODUCT:sparkmetriq] | Moteur de recommandations spécifique |
| **ASSISTANT IA** |
| `api/routes/assistant.py` | [PRODUCT:sparkmetriq] | Routes assistant stratégique spécifiques |
| `api/services/assistant/alerts_service.py` | [PRODUCT:sparkmetriq] | Service d'alertes spécifique |
| `api/services/assistant/collab_service.py` | [PRODUCT:sparkmetriq] | Service collaborations spécifique |
| `api/services/assistant/context_service.py` | [PRODUCT:sparkmetriq] | Service contexte spécifique |
| `api/services/assistant/history_service.py` | [PRODUCT:sparkmetriq] | Service historique spécifique |
| `api/services/assistant/plan_service.py` | [PRODUCT:sparkmetriq] | Service plans spécifique |
| `api/services/assistant/trends_service.py` | [PRODUCT:sparkmetriq] | Service tendances spécifique |
| `api/services/assistant/jobs.py` | [PRODUCT:sparkmetriq] | Jobs assistant spécifiques |
| `api/schemas/assistant.py` | [PRODUCT:sparkmetriq] | Schémas assistant spécifiques |
| **CHAT OMNICANAL** |
| `api/routes/chats.py` | [PRODUCT:sparkmetriq] | Routes chat omnicanal spécifiques (modèle Sparkmetriq) |
| `api/services/chat_omnichannel/manager.py` | [PRODUCT:sparkmetriq] | Manager chat spécifique (utilise muses, orgs Sparkmetriq) |
| `api/services/chat_omnichannel/llm_service.py` | [CORE] | Service LLM générique (abstraction) |
| `api/services/chat_omnichannel/deepseek_service.py` | [PRODUCT:sparkmetriq] | Implémentation DeepSeek spécifique |
| `api/services/chat_omnichannel/rag_service.py` | [PRODUCT:sparkmetriq] | Service RAG spécifique |
| `api/services/chat_omnichannel/doc_store.py` | [PRODUCT:sparkmetriq] | Store documents spécifique |
| `api/services/chat_omnichannel/vector_store.py` | [PRODUCT:sparkmetriq] | Store vectoriel spécifique |
| `api/schemas/chat.py` | [PRODUCT:sparkmetriq] | Schémas chat spécifiques |
| **INTENT ENGINE** |
| `api/routes/intent.py` | [PRODUCT:sparkmetriq] | Routes intent engine spécifiques |
| `api/services/intent/intent_engine.py` | [PRODUCT:sparkmetriq] | Moteur d'intentions spécifique |
| `api/services/intent/dispatcher.py` | [PRODUCT:sparkmetriq] | Dispatcher intent spécifique |
| `api/services/intent/llm_handler.py` | [PRODUCT:sparkmetriq] | Handler LLM intent spécifique |
| `api/services/intent/rag_unified.py` | [PRODUCT:sparkmetriq] | RAG unifié intent spécifique |
| `api/services/intent/scenario_engine.py` | [PRODUCT:sparkmetriq] | Moteur de scénarios spécifique |
| `api/services/intent/validator.py` | [PRODUCT:sparkmetriq] | Validateur intent spécifique |
| `api/schemas/intent.py` | [PRODUCT:sparkmetriq] | Schémas intent spécifiques |
| **CALENDAR** |
| `api/routes/calendar.py` | [PRODUCT:sparkmetriq] | Routes calendrier spécifiques (vue calendaire Sparkmetriq) |
| `api/routes/ws_calendar.py` | [PRODUCT:sparkmetriq] | WebSocket calendrier spécifique |
| `api/services/calendar/service.py` | [PRODUCT:sparkmetriq] | Service calendrier spécifique |
| `api/services/calendar/ws_hub.py` | [PRODUCT:sparkmetriq] | Hub WebSocket calendrier spécifique |
| `api/schemas/calendar.py` | [PRODUCT:sparkmetriq] | Schémas calendrier spécifiques |
| `api/schemas/calendar_schema.py` | [PRODUCT:sparkmetriq] | Schémas calendrier spécifiques |
| **PAYMENTS** |
| `api/routes/payments.py` | [PRODUCT:sparkmetriq] | Routes paiements spécifiques (modèle Sparkmetriq avec muses) |
| `api/routes/webhooks/payments_webhook.py` | [PRODUCT:sparkmetriq] | Webhook paiements spécifique |
| `api/services/payment_gateway/nowpayments.py` | [PRODUCT:sparkmetriq] | Gateway NOWPayments spécifique |
| `api/services/payment_gateway/cryptobot.py` | [PRODUCT:sparkmetriq] | Gateway CryptoBot spécifique |
| `api/services/payments/nowpayments.py` | [PRODUCT:sparkmetriq] | Service NOWPayments spécifique |
| `api/schemas/payments.py` | [PRODUCT:sparkmetriq] | Schémas paiements spécifiques |
| **PPV (PAY PER VIEW)** |
| `api/routes/ppv.py` | [PRODUCT:sparkmetriq] | Routes PPV spécifiques (modèle Sparkmetriq) |
| `api/routes/ppv_tracking.py` | [PRODUCT:sparkmetriq] | Tracking PPV spécifique |
| `api/schemas/ppv.py` | [PRODUCT:sparkmetriq] | Schémas PPV spécifiques |
| **WEBHOOKS** |
| `api/routes/webhooks/telegram.py` | [PRODUCT:sparkmetriq] | Webhook Telegram spécifique |
| `api/routes/webhooks/instagram.py` | [PRODUCT:sparkmetriq] | Webhook Instagram spécifique |
| `api/routes/webhooks/whatsapp.py` | [PRODUCT:sparkmetriq] | Webhook WhatsApp spécifique |
| `api/routes/webhooks/tiktok.py` | [PRODUCT:sparkmetriq] | Webhook TikTok spécifique |
| `api/routes/webhooks/fanvue.py` | [PRODUCT:sparkmetriq] | Webhook Fanvue spécifique |
| `api/routes/webhooks/mymfans.py` | [PRODUCT:sparkmetriq] | Webhook MYM.fans spécifique |
| `api/routes/webhooks/manyvids.py` | [PRODUCT:sparkmetriq] | Webhook ManyVids spécifique |
| `api/routes/webhooks/reddit.py` | [PRODUCT:sparkmetriq] | Webhook Reddit spécifique |
| **PLATFORMS** |
| `api/routes/platforms.py` | [PRODUCT:sparkmetriq] | Routes plateformes spécifiques |
| `api/schemas/platforms.py` | [PRODUCT:sparkmetriq] | Schémas plateformes spécifiques |
| **TALENT** |
| `api/routes/talent.py` | [PRODUCT:sparkmetriq] | Routes talent spécifiques (gestion talents Sparkmetriq) |
| `api/services/talent/assignment_service.py` | [PRODUCT:sparkmetriq] | Service assignation talents spécifique |
| `api/services/talent/audit_service.py` | [PRODUCT:sparkmetriq] | Service audit talents spécifique |
| `api/services/talent/dashboard_service.py` | [PRODUCT:sparkmetriq] | Service dashboard talents spécifique |
| `api/services/talent/inbox_service.py` | [PRODUCT:sparkmetriq] | Service inbox talents spécifique |
| `api/services/talent/integrations_service.py` | [PRODUCT:sparkmetriq] | Service intégrations talents spécifique |
| `api/schemas/talent.py` | [PRODUCT:sparkmetriq] | Schémas talents spécifiques |
| **COLLAB** |
| `api/routes/collab.py` | [PRODUCT:sparkmetriq] | Routes collaborations spécifiques |
| `api/services/collab/chat_service.py` | [PRODUCT:sparkmetriq] | Service chat collab spécifique |
| `api/services/collab/integrations.py` | [PRODUCT:sparkmetriq] | Intégrations collab spécifiques |
| `api/services/collab/reminders.py` | [PRODUCT:sparkmetriq] | Rappels collab spécifiques |
| `api/services/collab/task_service.py` | [PRODUCT:sparkmetriq] | Service tâches collab spécifique |
| `api/services/collab/ws.py` | [PRODUCT:sparkmetriq] | WebSocket collab spécifique |
| `api/schemas/collab.py` | [PRODUCT:sparkmetriq] | Schémas collab spécifiques |
| **MESSAGING** |
| `api/routes/message_builder.py` | [PRODUCT:sparkmetriq] | Routes message builder spécifiques |
| `api/services/messaging/message_builder.py` | [PRODUCT:sparkmetriq] | Service message builder spécifique |
| `api/services/messaging/outbox_worker.py` | [PRODUCT:sparkmetriq] | Worker outbox spécifique |
| `api/services/messaging/segmentation.py` | [PRODUCT:sparkmetriq] | Segmentation spécifique |
| `api/services/messaging/template_engine.py` | [PRODUCT:sparkmetriq] | Moteur templates spécifique |
| `api/schemas/message_builder.py` | [PRODUCT:sparkmetriq] | Schémas message builder spécifiques |
| **TRACKING** |
| `api/routes/tracking.py` | [PRODUCT:sparkmetriq] | Routes tracking spécifiques |
| `api/routes/redirect.py` | [PRODUCT:sparkmetriq] | Routes redirect spécifiques |
| `api/services/tracking/attribution_service.py` | [PRODUCT:sparkmetriq] | Service attribution spécifique |
| `api/services/tracking/link_service.py` | [PRODUCT:sparkmetriq] | Service liens spécifique |
| `api/services/tracking/redirect_service.py` | [PRODUCT:sparkmetriq] | Service redirect spécifique |
| `api/schemas/tracking.py` | [PRODUCT:sparkmetriq] | Schémas tracking spécifiques |
| **AI SERVICES** |
| `api/routes/recap.py` | [PRODUCT:sparkmetriq] | Routes recap spécifiques |
| `api/routes/translator.py` | [PRODUCT:sparkmetriq] | Routes traduction spécifiques |
| `api/services/ai/recap_service.py` | [PRODUCT:sparkmetriq] | Service recap spécifique |
| `api/services/ai/recap_scheduler.py` | [PRODUCT:sparkmetriq] | Scheduler recap spécifique |
| `api/services/ai/translate_service.py` | [PRODUCT:sparkmetriq] | Service traduction spécifique |
| `api/schemas/recap.py` | [PRODUCT:sparkmetriq] | Schémas recap spécifiques |
| `api/schemas/translator.py` | [PRODUCT:sparkmetriq] | Schémas traduction spécifiques |
| **CONFIG & FUNNEL** |
| `api/routes/funnel_config.py` | [PRODUCT:sparkmetriq] | Routes config funnel spécifiques |
| `api/services/config/funnel_config.py` | [PRODUCT:sparkmetriq] | Service config funnel spécifique |
| `api/schemas/funnel_config.py` | [PRODUCT:sparkmetriq] | Schémas config funnel spécifiques |
| **ANALYSIS** |
| `api/routes/analysis/filters.py` | [PRODUCT:sparkmetriq] | Routes filtres analyse spécifiques |
| `api/routes/analysis_tunnels.py` | [PRODUCT:sparkmetriq] | Routes analyse tunnels spécifiques |
| **CLOUDPHONE** |
| `api/routes/cloudphone.py` | [PRODUCT:sparkmetriq] | Routes CloudPhone spécifiques (module spécifique) |
| `api/services/cloudphone/cloudphone_client.py` | [PRODUCT:sparkmetriq] | Client CloudPhone spécifique |
| `api/services/cloudphone/excel_import.py` | [PRODUCT:sparkmetriq] | Import Excel CloudPhone spécifique |
| `api/services/cloudphone/manager.py` | [PRODUCT:sparkmetriq] | Manager CloudPhone spécifique |
| `api/services/cloudphone/repository.py` | [PRODUCT:sparkmetriq] | Repository CloudPhone spécifique |
| `api/services/cloudphone/selection.py` | [PRODUCT:sparkmetriq] | Sélection CloudPhone spécifique |
| `api/config/cloudphone_config.py` | [PRODUCT:sparkmetriq] | Config CloudPhone spécifique |
| `api/schemas/cloudphone.py` | [PRODUCT:sparkmetriq] | Schémas CloudPhone spécifiques |
| **OTP** |
| `api/routes/otp.py` | [MIXED/À DISCUTER] | Routes OTP : partie générique (sessions, validation) vers core, partie parsers spécifiques vers sparkmetriq |
| `api/services/otp/sessions.py` | [CORE] | Gestion générique des sessions OTP |
| `api/services/otp/policy.py` | [CORE] | Politique générique OTP |
| `api/services/otp/parsers.py` | [PRODUCT:sparkmetriq] | Parsers OTP spécifiques (formats Sparkmetriq) |
| `api/services/otp/providers/base.py` | [CORE] | Classe abstraite provider OTP générique |
| `api/services/otp/providers/registry.py` | [CORE] | Registry providers OTP générique |
| `api/schemas/otp.py` | [MIXED/À DISCUTER] | Schémas OTP : partie générique vers core, partie spécifique vers sparkmetriq |
| **LOGS** |
| `api/routes/logs.py` | [PRODUCT:sparkmetriq] | Routes logs spécifiques |
| `api/services/logs/activity_logger.py` | [PRODUCT:sparkmetriq] | Logger activité spécifique |
| **MEDIA** |
| `api/routes/media.py` | [PRODUCT:sparkmetriq] | Routes média spécifiques |
| **BOTS** |
| `api/routes/bots.py` | [PRODUCT:sparkmetriq] | Routes bots spécifiques |
| `api/services/instagram_bot.py` | [PRODUCT:sparkmetriq] | Bot Instagram spécifique |
| `api/services/telegram_bot.py` | [PRODUCT:sparkmetriq] | Bot Telegram spécifique |
| `api/services/tiktok_bot.py` | [PRODUCT:sparkmetriq] | Bot TikTok spécifique |
| **TEST ROUTES** |
| `api/routes/instagram_test.py` | [PRODUCT:sparkmetriq] | Routes test Instagram spécifiques |
| `api/routes/threads_test.py` | [PRODUCT:sparkmetriq] | Routes test Threads spécifiques |
| `api/routes/snapchat_test.py` | [PRODUCT:sparkmetriq] | Routes test Snapchat spécifiques |
| **UTILS** |
| `api/utils/dates.py` | [CORE] | Utilitaires dates génériques |
| `api/utils/responses.py` | [CORE] | Utilitaires réponses génériques |
| **WEBSOCKETS** |
| `api/websockets/alerts.py` | [PRODUCT:sparkmetriq] | WebSocket alertes spécifique |
| **MAIN** |
| `api/main.py` | [MIXED/À DISCUTER] | Point d'entrée : partie générique (setup FastAPI) vers core, partie routes spécifiques vers sparkmetriq |
| `api/__init__.py` | [CORE] | Initialisation générique |
| **SAASENTIALCORE (DÉJÀ CORE)** |
| `saasentialcore/` | [CORE] | Module core générique déjà structuré |
| **PRODUCTS (NOUVEAU)** |
| `saasentialcore/products/sparkmetriq/` | [PRODUCT:sparkmetriq] | Structure produit Sparkmetriq (produit complet multi-modules) |
| `saasentialcore/products/sparkpusher/` | [PRODUCT:sparkpusher] | Structure produit SparkPusher (S2 Content Studio) |

---

## Résumé des catégories

- **[CORE]** : ~45 modules (auth, orgs, scheduler générique, quotas, observabilité, connecteurs abstraits)
- **[PRODUCT:sparkmetriq]** : ~180 modules (BI, AI Marketing, Tunnels, Stats, muses, contenus, webhooks, etc.)
- **[MIXED/À DISCUTER]** : ~10 modules nécessitant un split (scheduler routes, OAuth Google, OTP, settings, main.py)

---

## Notes importantes

1. **Connecteurs** : La classe abstraite `base.py` et le `registry.py` sont CORE, mais toutes les implémentations sont PRODUCT:sparkmetriq car elles utilisent le modèle de données spécifique.

2. **Scheduler** : Le moteur générique (jobs, retries, status) est CORE, mais les fonctionnalités métier (drafts, AB tests, recycle) sont PRODUCT:sparkmetriq.

3. **Chat** : Le service LLM abstrait est CORE, mais le manager et les implémentations sont PRODUCT:sparkmetriq car liés au modèle muses/orgs.

4. **OTP** : La logique de sessions et validation est CORE, mais les parsers de formats spécifiques sont PRODUCT:sparkmetriq.

5. **Settings** : La configuration de base (DB, security) est CORE, mais les feature flags spécifiques sont PRODUCT:sparkmetriq.

