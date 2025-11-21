# api/databases/databases.py
"""
Gestion des connexions MongoDB pour musAI Platform.
- Deux bases distinctes : CORE (musai_core) & BI (musai_bi)
- Motor (async) pour l'app, PyMongo (sync) pour certains tests
- Helpers: init/close, sélecteur de base par collection, création d'index
"""

from __future__ import annotations

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient, ASCENDING, DESCENDING
from api.core.settings import settings

# -----------------------------
# Clients Async (app)
# -----------------------------
client_core: Optional[AsyncIOMotorClient] = None
client_bi: Optional[AsyncIOMotorClient] = None

db_core: Optional[AsyncIOMotorDatabase] = None
db_bi: Optional[AsyncIOMotorDatabase] = None

# Alias historique (par compat)
db: Optional[AsyncIOMotorDatabase] = None

# -----------------------------
# Clients Sync (tests, outils)
# -----------------------------
client_sync_core: Optional[MongoClient] = None
client_sync_bi: Optional[MongoClient] = None

db_sync_core = None
db_sync_bi = None


def init_clients() -> None:
    """
    Initialise/rafraîchit les clients Mongo (async + sync) selon settings.
    Idempotent : peut être rappelé en tests pour réinitialiser la connexion.
    """
    global client_core, client_bi, db_core, db_bi, db
    global client_sync_core, client_sync_bi, db_sync_core, db_sync_bi

    # --- Async (app) ---
    client_core = AsyncIOMotorClient(
        settings.MONGO_URI,
        maxPoolSize=settings.database.max_pool_size,
        minPoolSize=settings.database.min_pool_size,
        serverSelectionTimeoutMS=settings.database.server_selection_timeout,
        socketTimeoutMS=settings.database.socket_timeout,
        uuidRepresentation="standard",
    )
    client_bi = AsyncIOMotorClient(
        settings.MONGO_URI_BI,
        maxPoolSize=settings.database.max_pool_size,
        minPoolSize=settings.database.min_pool_size,
        serverSelectionTimeoutMS=settings.database.server_selection_timeout,
        socketTimeoutMS=settings.database.socket_timeout,
        uuidRepresentation="standard",
    )

    db_core = client_core[settings.DB_NAME_CORE]
    db_bi = client_bi[settings.DB_NAME_BI]

    # Alias compat historique : db = core
    # (certains modules hérités importent `from api.databases.databases import db`)
    # Vous pouvez progressivement remplacer par get_core_db()
    db = db_core

    # --- Sync (tests, scripts utilitaires) ---
    client_sync_core = MongoClient(
        settings.MONGO_URI,
        uuidRepresentation="standard",
    )
    client_sync_bi = MongoClient(
        settings.MONGO_URI_BI,
        uuidRepresentation="standard",
    )

    db_sync_core = client_sync_core[settings.DB_NAME_CORE]
    db_sync_bi = client_sync_bi[settings.DB_NAME_BI]


def close_clients() -> None:
    """
    Ferme proprement tous les clients (utile pour tests/teardown).
    """
    global client_core, client_bi, client_sync_core, client_sync_bi
    try:
        if client_core:
            client_core.close()
        if client_bi:
            client_bi.close()
        if client_sync_core:
            client_sync_core.close()
        if client_sync_bi:
            client_sync_bi.close()
    finally:
        # Remettre à None
        _reset_globals()


def _reset_globals() -> None:
    global client_core, client_bi, db_core, db_bi, db
    global client_sync_core, client_sync_bi, db_sync_core, db_sync_bi
    client_core = client_bi = None
    db_core = db_bi = db = None
    client_sync_core = client_sync_bi = None
    db_sync_core = db_sync_bi = None


# Initialise par défaut au chargement du module
init_clients()


# -----------------------------
# Getters DB
# -----------------------------
def get_core_db() -> AsyncIOMotorDatabase:
    """
    Retourne la base CORE (opérationnelle).
    """
    if db_core is None:
        init_clients()
    return db_core


def get_bi_db() -> AsyncIOMotorDatabase:
    """
    Retourne la base BI (analytics/scraping/RAG marketing).
    """
    if db_bi is None:
        init_clients()
    return db_bi


def get_db_for_collection(collection_name: str) -> AsyncIOMotorDatabase:
    """
    Sélectionne la base selon la collection.
    - Orienté par domaines : les collections BI listées partent sur DB BI.
    - Sinon, retourne CORE par défaut.
    """
    bi_collections = {
        # BI (analytics, scraping, RAG marketing)
        "trends_cache", "ai_action_plans", "ai_alerts", "ai_collab_suggestions",
        "ai_reco_history", "events_funnel", "conversation_daily", "revenue_daily",
        "ppv_daily", "scheduled_drafts", "scheduled_jobs", "publish_logs",
        "ab_tests", "recycle_policies", "muse_metrics_daily", "audit_events",
        "fan_tags", "fan_notes", "operator_roles", "muse_assignments",
        "integration_hooks", "rag_documents", "rag_embeddings", "vector_index",
        "scraped_contents", "creator_analytics", "platform_metrics",
        "analytics_events", "revenue_attribution_daily", "chat_threads",
        "funnel_events", "ppv_sales", "payments", "messages",
    }
    return get_bi_db() if collection_name in bi_collections else get_core_db()


# -----------------------------
# Indexation
# -----------------------------
async def ensure_all_indexes() -> None:
    """
    Crée tous les index des deux bases.
    À appeler au startup de l'application.
    """
    await ensure_core_indexes()
    await ensure_bi_indexes()


async def _safe_create_index(coll, keys, **kwargs):
    """
    Crée un index et ignore silencieusement les collisions ou duplications.
    """
    try:
        await coll.create_index(keys, **kwargs)
    except Exception:
        # Collisions/duplications possibles si déployé plusieurs fois
        pass


async def ensure_core_indexes() -> None:
    """
    Index pour la base CORE (opérationnelle).
    """
    core = get_core_db()

    # Users & Auth
    await _safe_create_index(core["users"], [("email", ASCENDING)], unique=True)
    await _safe_create_index(core["users"], [("org_id", ASCENDING)])
    await _safe_create_index(core["users"], [("google_id", ASCENDING)], unique=True, sparse=True)

    # CloudPhone
    await _safe_create_index(core["profiles"], [("org_id", ASCENDING), ("name", ASCENDING)], unique=True)
    await _safe_create_index(core["devices"], [("org_id", ASCENDING)])
    await _safe_create_index(core["device_app_slots"], [("device_id", ASCENDING), ("app", ASCENDING)])
    await _safe_create_index(core["bindings_appaccount_slot"], [("slot_id", ASCENDING)], unique=True)

    # OTP
    await _safe_create_index(core["otp_sessions"], [("org_id", ASCENDING), ("state", ASCENDING)])
    await _safe_create_index(core["otp_sessions"], [("session_id", ASCENDING)], unique=True)
    # TTL (expire à 'expires_at')
    await _safe_create_index(core["otp_sessions"], [("expires_at", ASCENDING)], expireAfterSeconds=0)

    # Entitlements
    await _safe_create_index(core["org_entitlements"], [("org_id", ASCENDING)], unique=True)

    # Chat (conversations)
    await _safe_create_index(core["chat_messages"], [("conversation_id", ASCENDING), ("timestamp", ASCENDING)])
    await _safe_create_index(core["chat_messages"], [("org_id", ASCENDING), ("muse_id", ASCENDING), ("platform", ASCENDING)])

    # Payments
    await _safe_create_index(core["payments"], [("org_id", ASCENDING), ("muse_id", ASCENDING)])
    await _safe_create_index(core["payments"], [("invoice_id", ASCENDING)], unique=True)

    # Activity Logs
    await _safe_create_index(core["activity_logs"], [("org_id", ASCENDING), ("scope", ASCENDING), ("created_at", DESCENDING)])
    await _safe_create_index(core["activity_logs"], [("org_id", ASCENDING), ("timestamp", DESCENDING)])
    await _safe_create_index(core["activity_logs"], [("org_id", ASCENDING), ("user_id", ASCENDING), ("timestamp", DESCENDING)])

    # Conversation Recaps
    await _safe_create_index(core["conversation_recaps"], [("org_id", ASCENDING), ("conversation_id", ASCENDING)], unique=True, name="ux_org_convo")
    await _safe_create_index(core["conversation_recaps"], [("org_id", ASCENDING), ("muse_id", ASCENDING), ("updated_at", DESCENDING)], name="ix_muse_updated")

    # Message Builder
    await _safe_create_index(core["message_templates"], [("org_id", ASCENDING), ("name", ASCENDING)], unique=True, name="ux_org_name")
    await _safe_create_index(core["campaigns"], [("org_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)], name="ix_status_created")
    await _safe_create_index(core["campaigns"], [("org_id", ASCENDING), ("scheduled_at", ASCENDING)], name="ix_scheduled")
    await _safe_create_index(core["campaign_targets"], [("campaign_id", ASCENDING), ("user_ref", ASCENDING)], unique=True, name="ux_campaign_user")
    await _safe_create_index(core["outbox_messages"], [("status", ASCENDING), ("scheduled_at", ASCENDING)], name="ix_outbox_status_sched")
    await _safe_create_index(core["outbox_messages"], [("dedupe_key", ASCENDING)], unique=True, name="ux_dedupe")

    # Link Tracking
    await _safe_create_index(core["tracking_links"], [("org_id", ASCENDING), ("code", ASCENDING)], unique=True, name="ux_org_code")
    await _safe_create_index(core["tracking_links"], [("org_id", ASCENDING), ("campaign_id", ASCENDING)], name="ix_campaign")
    await _safe_create_index(core["tracking_links"], [("org_id", ASCENDING), ("created_at", DESCENDING)], name="ix_created")
    await _safe_create_index(core["tracking_clicks"], [("org_id", ASCENDING), ("code", ASCENDING), ("ts", DESCENDING)], name="ix_clicks_code_ts")
    await _safe_create_index(core["tracking_clicks"], [("org_id", ASCENDING), ("campaign_id", ASCENDING), ("ts", DESCENDING)], name="ix_clicks_campaign_ts")
    await _safe_create_index(core["tracking_clicks"], [("user_ref", ASCENDING), ("ts", DESCENDING)], name="ix_clicks_user_ts")

    # Collaboration
    await _safe_create_index(core["collab_threads"], [("org_id", ASCENDING), ("updated_at", DESCENDING)], name="ix_threads_org_updated")
    await _safe_create_index(core["collab_messages"], [("thread_id", ASCENDING), ("created_at", ASCENDING)], name="ix_msgs_thread_ts")
    await _safe_create_index(core["collab_tasks"], [("org_id", ASCENDING), ("status", ASCENDING), ("due_at", ASCENDING)], name="ix_tasks_org_status_due")
    await _safe_create_index(core["collab_tasks"], [("org_id", ASCENDING), ("assignees", ASCENDING), ("status", ASCENDING)], name="ix_tasks_org_assignees")
    await _safe_create_index(core["collab_activity"], [("org_id", ASCENDING), ("ts", DESCENDING)], name="ix_collab_activity_ts")

    # Muses & Categories
    await _safe_create_index(core["muses"], [("org_id", ASCENDING), ("status", ASCENDING)], name="ix_muses_org_status")
    await _safe_create_index(core["muses"], [("org_id", ASCENDING), ("categories", ASCENDING)], name="ix_muses_org_categories")

    # Intent Engine
    await _safe_create_index(core["chat_scenarios"], [("org_id", ASCENDING), ("muse_id", ASCENDING), ("is_active", ASCENDING), ("version", ASCENDING)], name="ix_scenarios_org_muse_active")
    await _safe_create_index(core["chat_scenarios"], [("org_id", ASCENDING), ("muse_id", ASCENDING), ("trigger.type", ASCENDING), ("platforms", ASCENDING)], name="ix_scenarios_trigger")
    await _safe_create_index(core["chat_sessions"], [("org_id", ASCENDING), ("muse_id", ASCENDING), ("conversation_id", ASCENDING), ("status", ASCENDING)], name="ix_sessions_org_muse_conv")
    await _safe_create_index(core["persona_profiles"], [("org_id", ASCENDING), ("muse_id", ASCENDING)], name="ux_persona_org_muse", unique=True)
    await _safe_create_index(core["knowledge_chunks"], [("org_id", ASCENDING), ("muse_id", ASCENDING), ("kind", ASCENDING), ("ts", DESCENDING)], name="ix_knowledge_org_muse_kind")
    await _safe_create_index(core["chat_policies"], [("org_id", ASCENDING), ("muse_id", ASCENDING)], name="ux_policies_org_muse", unique=True)
    await _safe_create_index(core["conversation_overrides"], [("org_id", ASCENDING), ("muse_id", ASCENDING), ("conversation_id", ASCENDING)], name="ux_overrides_org_muse_conv", unique=True)

    # Calendar/Publishing
    await _safe_create_index(core["scheduled_posts"], [("org_id", ASCENDING), ("muse_id", ASCENDING), ("schedule.start_at_utc", ASCENDING)], name="ix_scheduled_org_muse_start")
    await _safe_create_index(core["scheduled_posts"], [("org_id", ASCENDING), ("platform", ASCENDING), ("status", ASCENDING), ("schedule.start_at_utc", ASCENDING)], name="ix_scheduled_org_platform_status")
    await _safe_create_index(core["scheduled_posts"], [("org_id", ASCENDING), ("labels", ASCENDING)], name="ix_scheduled_org_labels")
    await _safe_create_index(core["publishing_jobs"], [("org_id", ASCENDING), ("scheduled_post_id", ASCENDING), ("state", ASCENDING), ("next_retry_at_utc", ASCENDING)], name="ix_publishing_org_post_state")
    await _safe_create_index(core["content_assets"], [("org_id", ASCENDING), ("muse_id", ASCENDING), ("type", ASCENDING)], name="ix_assets_org_muse_type")
    await _safe_create_index(core["categories"], [("org_id", ASCENDING), ("name", ASCENDING)], name="ux_categories_org_name", unique=True)


async def ensure_bi_indexes() -> None:
    """
    Index pour la base BI (analytics / scraping / RAG marketing).
    """
    bi = get_bi_db()

    # Analytics BI
    await _safe_create_index(bi["events_funnel"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("phase", ASCENDING), ("ts", ASCENDING)])
    await _safe_create_index(bi["conversation_daily"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("day", ASCENDING)], unique=True)
    await _safe_create_index(bi["revenue_daily"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("day", ASCENDING)], unique=True)
    await _safe_create_index(bi["ppv_daily"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("day", ASCENDING)], unique=True)

    # Scheduler (BI side : drafts / logs)
    await _safe_create_index(bi["scheduled_drafts"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("status", ASCENDING), ("scheduled_at", ASCENDING)])
    await _safe_create_index(bi["scheduled_drafts"], [("job_id", ASCENDING)], unique=True, sparse=True)
    await _safe_create_index(bi["scheduled_jobs"], [("tenant_id", ASCENDING), ("status", ASCENDING), ("next_run_at", ASCENDING)])
    await _safe_create_index(bi["publish_logs"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("platform", ASCENDING), ("status", ASCENDING), ("ts", ASCENDING)])

    # AI Assistant
    await _safe_create_index(bi["ai_action_plans"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("month", ASCENDING)], unique=True)
    await _safe_create_index(bi["ai_alerts"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("status", ASCENDING), ("ts", ASCENDING)])
    await _safe_create_index(bi["ai_collab_suggestions"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("ts", ASCENDING)])
    await _safe_create_index(bi["ai_reco_history"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("ts", ASCENDING)])
    await _safe_create_index(bi["trends_cache"], [("tenant_id", ASCENDING), ("source", ASCENDING), ("topic", ASCENDING), ("ts", ASCENDING)])

    # Talent Management (BI)
    await _safe_create_index(bi["chat_threads"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("user_hash", ASCENDING)], unique=True)
    await _safe_create_index(bi["fan_tags"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("user_hash", ASCENDING), ("tag", ASCENDING)], unique=True)
    await _safe_create_index(bi["fan_notes"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("user_hash", ASCENDING), ("ts", DESCENDING)])
    await _safe_create_index(bi["operator_roles"], [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("role", ASCENDING)])
    await _safe_create_index(bi["muse_assignments"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("platform", ASCENDING), ("operator_id", ASCENDING)], unique=True)
    await _safe_create_index(bi["audit_events"], [("tenant_id", ASCENDING), ("ts", DESCENDING)])
    await _safe_create_index(bi["muse_metrics_daily"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING), ("day", ASCENDING)], unique=True)

    # RAG Marketing
    await _safe_create_index(bi["rag_documents"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING)])
    await _safe_create_index(bi["rag_documents"], [("content_type", ASCENDING), ("created_at", DESCENDING)])
    await _safe_create_index(bi["rag_embeddings"], [("document_id", ASCENDING)], unique=True)
    await _safe_create_index(bi["rag_embeddings"], [("tenant_id", ASCENDING), ("muse_id", ASCENDING)])

    # Scraping / Metrics
    await _safe_create_index(bi["scraped_contents"], [("platform", ASCENDING), ("creator_id", ASCENDING), ("scraped_at", DESCENDING)])
    await _safe_create_index(bi["creator_analytics"], [("creator_id", ASCENDING), ("platform", ASCENDING), ("date", DESCENDING)])
    await _safe_create_index(bi["platform_metrics"], [("platform", ASCENDING), ("date", DESCENDING)])

    # Analytics Events (transverse)
    await _safe_create_index(bi["analytics_events"], [("org_id", ASCENDING), ("type", ASCENDING), ("ts", DESCENDING)])
    await _safe_create_index(bi["analytics_events"], [("org_id", ASCENDING), ("conversation_id", ASCENDING), ("ts", DESCENDING)])
    await _safe_create_index(bi["analytics_events"], [("type", ASCENDING), ("ts", DESCENDING)])
    await _safe_create_index(bi["analytics_events"], [("campaign_id", ASCENDING), ("ts", DESCENDING)])

    # Revenue Attribution
    await _safe_create_index(bi["revenue_attribution_daily"], [("org_id", ASCENDING), ("day", ASCENDING), ("source", ASCENDING), ("medium", ASCENDING), ("campaign", ASCENDING), ("content", ASCENDING)], name="ux_day_source")
    await _safe_create_index(bi["revenue_attribution_daily"], [("org_id", ASCENDING), ("user_ref", ASCENDING), ("ts", DESCENDING)], name="ix_user_ts")

    # (collections “miroirs” optionnelles pour agrégations)
    for coll_name, keys, name in [
        ("payments", [("org_id", ASCENDING), ("muse_id", ASCENDING), ("ts", DESCENDING)], "ix_payments_org_muse_ts"),
        ("ppv_sales", [("org_id", ASCENDING), ("muse_id", ASCENDING), ("ts", DESCENDING)], "ix_ppv_org_muse_ts"),
        ("messages", [("org_id", ASCENDING), ("muse_id", ASCENDING), ("ts", DESCENDING)], "ix_messages_org_muse_ts"),
        ("funnel_events", [("org_id", ASCENDING), ("muse_id", ASCENDING), ("event", ASCENDING), ("ts", DESCENDING)], "ix_funnel_org_muse_event_ts"),
    ]:
        await _safe_create_index(bi[coll_name], keys, name=name)


# -----------------------------
# Utilitaires Tests
# -----------------------------
def get_test_db_core():
    """DB sync CORE pour tests unitaires"""
    return db_sync_core


def get_test_db_bi():
    """DB sync BI pour tests unitaires"""
    return db_sync_bi


async def cleanup_test_data():
    """Purge quelques collections Core/BI standards (utilitaire tests)."""
    core = get_core_db()
    bi = get_bi_db()

    collections_core = [
        "users", "profiles", "devices", "otp_sessions",
        "org_entitlements", "chat_messages", "payments",
        "message_templates", "campaigns", "campaign_targets",
        "outbox_messages", "tracking_links", "tracking_clicks",
        "collab_threads", "collab_messages", "collab_tasks", "collab_activity",
        "muses", "categories",
        "chat_scenarios", "chat_sessions", "persona_profiles",
        "knowledge_chunks", "chat_policies", "conversation_overrides",
        "scheduled_posts", "publishing_jobs", "content_assets",
        "activity_logs", "conversation_recaps",
    ]
    collections_bi = [
        "events_funnel", "conversation_daily", "revenue_daily", "ppv_daily",
        "scheduled_drafts", "scheduled_jobs", "publish_logs",
        "ai_action_plans", "ai_alerts", "ai_collab_suggestions", "ai_reco_history",
        "trends_cache", "chat_threads", "fan_tags", "fan_notes", "operator_roles",
        "muse_assignments", "audit_events", "muse_metrics_daily",
        "rag_documents", "rag_embeddings",
        "scraped_contents", "creator_analytics", "platform_metrics",
        "analytics_events", "revenue_attribution_daily",
        "payments", "ppv_sales", "messages", "funnel_events",
    ]

    for c in collections_core:
        try:
            await core[c].delete_many({})
        except Exception:
            pass
    for c in collections_bi:
        try:
            await bi[c].delete_many({})
        except Exception:
            pass
