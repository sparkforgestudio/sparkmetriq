# api/main.py
"""
Point d'entrée principal de l'application musAI Platform.
Configure FastAPI, monte les routes, gère les feature flags et les handlers d'erreurs.
"""

import os
import logging
import traceback
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configurer le logging (doit être fait avant les imports qui utilisent logging)
from api.core.logging import setup_logging, get_logger
setup_logging()

logger = get_logger(__name__)

# Import des settings pour les feature flags
from api.core.settings import settings

# Création de l'application
app = FastAPI(
    title="SparkMetrics",
    version=settings.app_version,
    description="API multitenant pour la gestion des influenceuses, chat omnicanal et paiement crypto-transparent."
)

# --- Import des routeurs ---
from api.routes.auth import router as auth_router
from api.routes.auth_google import router as auth_google_router
from api.routes.users import router as users_router
from api.routes.payments import router as payments_router
from api.routes.webhooks.payments_webhook import router as payments_webhook_router
from api.routes.ppv import router as ppv_router
from api.routes.public_contents import router as public_router
from api.routes.dispatcher import router as dispatcher_router
from api.routes.tunnels_test import router as tunnels_router
from api.routes.instagram_test import router as instagram_test_router
from api.routes.threads_test import router as threads_test_router
from api.routes.snapchat_test import router as snapchat_test_router
from api.routes.scheduler import router as scheduler_router
from api.routes.stats import router as stats_router
from api.routes.stats_tunnels import router as stats_tunnels_router
from api.routes.stats.timeline import router as timeline_router
from api.routes.chats import router as chats_router
from api.routes.analysis.filters import router as filters_router
from api.routes.analysis.tunnel import router as tunnel_analysis_router
from api.routes.webhooks.telegram import router as telegram_webhook_router
from api.routes.webhooks.instagram import router as instagram_webhook_router
from api.routes.webhooks.whatsapp import router as whatsapp_webhook_router
from api.routes.webhooks.tiktok import router as tiktok_webhook_router
from api.routes.webhooks.fanvue import router as fanvue_webhook_router
from api.routes.webhooks.mymfans import router as mymfans_webhook_router
from api.routes.webhooks.manyvids import router as manyvids_webhook_router
from api.routes.platforms import router as platforms_router
from api.routes.ai_marketing import router as ai_marketing_router
from api.routes.analytics_conversations import router as analytics_conv_router
from api.routes.analytics_bi import router as analytics_bi_router
from api.routes.ppv_tracking import router as ppv_tracking_router
from api.routes.scheduler import router as scheduler_router
from api.routes.assistant import router as assistant_router
from api.routes.talent import router as talent_router
from api.routes.orgs import router as orgs_router

# --- Handlers d'erreurs globaux ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler pour les erreurs de validation Pydantic."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler global pour les erreurs non gérées."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # En production, ne pas exposer la stack trace complète
    if settings.environment == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc),
                "traceback": traceback.format_exc()
            }
        )


# --- Route racine ---
@app.get("/", tags=["Root"])
def root():
    """Route racine de l'API."""
    return {"message": "Bienvenue sur l'API musAI Platform", "version": settings.app_version}

# --- Enregistrement des routeurs ---
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(auth_google_router, prefix="/api", tags=["Auth Google"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])
app.include_router(payments_webhook_router, prefix="/api/payments/webhook", tags=["Payments Webhook"])
app.include_router(ppv_router, prefix="/api/ppv", tags=["PPV Contents"])
app.include_router(public_router, prefix="/api/contents", tags=["Public Contents"])
app.include_router(dispatcher_router, prefix="/api/dispatch", tags=["Dispatcher"])
app.include_router(tunnels_router, prefix="/api/tunnels", tags=["Tunnels"])
app.include_router(instagram_test_router, prefix="/api/instagram", tags=["Instagram Test"])
app.include_router(threads_test_router, prefix="/api/threads", tags=["Threads Test"])
app.include_router(snapchat_test_router, prefix="/api/test", tags=["Snapchat Test"])
# Routes Health (toujours montées)
from api.routes.health import router as health_router
app.include_router(health_router)

# Scheduler (conditionnel)
if settings.enable_scheduler:
    app.include_router(scheduler_router, prefix="/api/scheduler", tags=["Scheduler"])
    logger.info("Scheduler routes mounted")
else:
    logger.info("Scheduler feature disabled (ENABLE_SCHEDULER=false)")
app.include_router(stats_router, prefix="/api/stats", tags=["Stats"])
app.include_router(stats_tunnels_router, prefix="/api/stats/tunnels", tags=["Tunnel Stats"])
app.include_router(timeline_router, prefix="/api/stats/timeline", tags=["Timeline Stats"])
app.include_router(chats_router, prefix="/api")  # -> URL = /api/chat/send
app.include_router(filters_router, prefix="/analysis/filters", tags=["Filters"])
app.include_router(tunnel_analysis_router, prefix="/analysis/tunnel", tags=["Tunnel Analysis"])
app.include_router(telegram_webhook_router, prefix="/webhook/telegram", tags=["Telegram Webhook"])
app.include_router(instagram_webhook_router, prefix="/webhook/instagram", tags=["Instagram Webhook"])
app.include_router(whatsapp_webhook_router, prefix="/webhook/whatsapp", tags=["WhatsApp Webhook"])
app.include_router(tiktok_webhook_router, prefix="/webhook/tiktok", tags=["TikTok Webhook"])
app.include_router(fanvue_webhook_router, prefix="/webhook/fanvue", tags=["Fanvue Webhook"])
app.include_router(mymfans_webhook_router, prefix="/webhook/mymfans", tags=["MYM.fans Webhook"])
app.include_router(manyvids_webhook_router, prefix="/webhook/manyvids", tags=["ManyVids Webhook"])
app.include_router(platforms_router, prefix="/api/platforms", tags=["Platforms"])
app.include_router(ai_marketing_router, prefix="/api/ai-marketing", tags=["AI Marketing"])
app.include_router(analytics_conv_router, prefix="/api", tags=["Analytics"])
app.include_router(analytics_bi_router, prefix="/api", tags=["Analytics"])
app.include_router(ppv_tracking_router, prefix="/api", tags=["Monetization"])
app.include_router(scheduler_router, prefix="/api", tags=["Scheduler"])
app.include_router(assistant_router, prefix="/api", tags=["Assistant"])
app.include_router(talent_router, prefix="/api", tags=["Talent"])
app.include_router(orgs_router, tags=["Organizations"])  # Prefix déjà défini dans le router

# --- Feature flags: CloudPhone ---
if settings.feature_cloudphone_enabled:
    try:
        from api.routes.cloudphone import router as cloudphone_router
        app.include_router(cloudphone_router, prefix="/api/mobile-cloud", tags=["CloudPhone"])
        logger.info("CloudPhone routes mounted")
    except Exception as e:
        # Ne jamais casser le boot si le module est mal installé
        logger.warning(f"CloudPhone routes not mounted: {e}")
else:
    logger.info("CloudPhone feature disabled (FEATURE_CLOUDPHONE_ENABLED=false)")

# --- Feature flags: OTP ---
if settings.feature_otp_enabled:
    try:
        from api.routes.otp import router as otp_router
        app.include_router(otp_router, prefix="/api/otp", tags=["OTP"])
        logger.info("OTP routes mounted")
    except Exception as e:
        # Ne jamais casser le boot si le module est mal installé
        logger.warning(f"OTP routes not mounted: {e}")
    else:
        logger.info("OTP feature disabled (FEATURE_OTP_ENABLED=false)")

# --- Feature flags: Translator ---
if settings.feature_translator_enabled:
    try:
        from api.routes.translator import router as translator_router
        app.include_router(translator_router, prefix="/api", tags=["Translator"])
        print("[INFO] Translator routes mounted")
    except Exception as e:
        # Ne jamais casser le boot si le module est mal installé
        print(f"[WARN] Translator routes not mounted: {e}")
else:
    print("[INFO] Translator feature disabled (FEATURE_TRANSLATOR_ENABLED=false)")

# --- Feature flags: Conversation Recap ---
if settings.feature_convo_recap_enabled:
    try:
        from api.routes.recap import router as recap_router
        app.include_router(recap_router, prefix="/api", tags=["Recap"])
        print("[INFO] Conversation Recap routes mounted")
    except Exception as e:
        # Ne jamais casser le boot si le module est mal installé
        print(f"[WARN] Conversation Recap routes not mounted: {e}")
else:
    print("[INFO] Conversation Recap feature disabled (FEATURE_CONVO_RECAP_ENABLED=false)")

# --- Feature flags: Message Builder ---
if settings.feature_message_builder_enabled:
    try:
        from api.routes.message_builder import router as message_builder_router
        app.include_router(message_builder_router, prefix="/api", tags=["Message Builder"])
        print("[INFO] Message Builder routes mounted")
    except Exception as e:
        # Ne jamais casser le boot si le module est mal installé
        print(f"[WARN] Message Builder routes not mounted: {e}")
else:
    print("[INFO] Message Builder feature disabled (FEATURE_MESSAGE_BUILDER_ENABLED=false)")

# --- Feature flags: Link Tracking & Attribution ---
if settings.feature_link_tracking_enabled:
    try:
        from api.routes.tracking import router as tracking_router
        from api.routes.redirect import router as redirect_router
        app.include_router(tracking_router, prefix="/api", tags=["Tracking"])
        app.include_router(redirect_router)  # Pas de prefix pour /r/{code}
        print("[INFO] Link Tracking routes mounted")
    except Exception as e:
        # Ne jamais casser le boot si le module est mal installé
        print(f"[WARN] Link Tracking routes not mounted: {e}")
else:
    print("[INFO] Link Tracking feature disabled (FEATURE_LINK_TRACKING_ENABLED=false)")

# --- Feature flags: Collaboration Interne ---
if settings.feature_collab_enabled:
    try:
        from api.routes.collab import router as collab_router
        from api.services.collab.ws import hub
        from api.core.auth import get_current_user
        from fastapi import WebSocket, WebSocketDisconnect
        from api.schemas.users import UserResponse
        
        app.include_router(collab_router, prefix="/api", tags=["Collaboration"])
        print("[INFO] Collaboration routes mounted")
        
        # WebSocket endpoint pour collaboration
        @app.websocket(f"{settings.collab_ws_path}/{{org_id}}")
        async def collab_ws(org_id: str, websocket: WebSocket):
            """
            WebSocket endpoint pour la collaboration en temps réel.
            Note: Pour MVP, on accepte sans authentification. En prod, ajouter vérification.
            """
            await hub.connect(org_id, websocket)
            try:
                while True:
                    # Recevoir des messages (ping/pong ou messages clients optionnels)
                    data = await websocket.receive_text()
                    # Optionnel: traiter les messages clients (pings, etc.)
            except WebSocketDisconnect:
                hub.disconnect(org_id, websocket)
        
        print(f"[INFO] Collaboration WebSocket mounted at {settings.collab_ws_path}/{{org_id}}")
    except Exception as e:
        # Ne jamais casser le boot si le module est mal installé
        print(f"[WARN] Collaboration routes not mounted: {e}")
else:
    print("[INFO] Collaboration feature disabled (FEATURE_COLLAB_ENABLED=false)")

# --- Routes Muses & Analytics ---
try:
    from api.routes.muses import router as muses_router
    from api.routes.analytics_muses import router as analytics_muses_router
    app.include_router(muses_router, prefix="/api", tags=["Muses"])
    app.include_router(analytics_muses_router, prefix="/api", tags=["Analytics"])
    print("[INFO] Muses & Analytics routes mounted")
except Exception as e:
    print(f"[WARN] Muses & Analytics routes not mounted: {e}")

# --- Routes Intent Engine ---
try:
    from api.routes.intent import router as intent_router
    app.include_router(intent_router, prefix="/api", tags=["Intent Engine"])
    print("[INFO] Intent Engine routes mounted")
except Exception as e:
    print(f"[WARN] Intent Engine routes not mounted: {e}")

# --- Routes Calendar ---
try:
    from api.routes.calendar import router as calendar_router
    from api.routes.ws_calendar import router as ws_calendar_router
    app.include_router(calendar_router, prefix="/api", tags=["Calendar"])
    app.include_router(ws_calendar_router, tags=["WebSocket"])
    print("[INFO] Calendar routes and WebSocket mounted")
except Exception as e:
    print(f"[WARN] Calendar routes not mounted: {e}")

# --- Routes BI (Insights & Pricing) - Conditionnel ---
if settings.enable_bi:
    try:
        from api.routes.bi_insights import router as bi_insights_router
        from api.routes.bi_pricing import router as bi_pricing_router
        app.include_router(bi_insights_router, prefix="/api", tags=["BI Insights"])
        app.include_router(bi_pricing_router, prefix="/api", tags=["BI Pricing"])
        logger.info("BI routes (Insights & Pricing) mounted")
    except Exception as e:
        logger.warning(f"BI routes not mounted: {e}")
else:
    logger.info("BI feature disabled (ENABLE_BI=false)")

# --- Index MongoDB pour Analytics ---
from api.databases import databases

@app.on_event("startup")
async def ensure_bi_indexes():
    """Créer les index nécessaires pour l'analytics BI."""
    db = databases.db

    await db["chat_messages"].create_index([("tenant_id", 1), ("muse_id", 1), ("channel", 1), ("role", 1), ("timestamp", 1)])
    await db["chat_messages"].create_index([("conversation_id", 1), ("timestamp", 1)])

    await db["events_funnel"].create_index([("tenant_id", 1), ("muse_id", 1), ("phase", 1), ("ts", 1)])
    await db["payments"].create_index([("tenant_id", 1), ("muse_id", 1), ("status", 1), ("ts", 1)])

    await db["ppv_logs"].create_index([("tenant_id", 1), ("muse_id", 1), ("platform", 1), ("status", 1), ("ts", 1)])
    await db["ppv_logs"].create_index([("payment.link_token", 1)], unique=True, sparse=True)

    await db["conversation_daily"].create_index([("tenant_id", 1), ("muse_id", 1), ("day", 1)], unique=True)
    await db["revenue_daily"].create_index([("tenant_id", 1), ("muse_id", 1), ("day", 1)], unique=True)

    await db["ppv_daily"].create_index([("tenant_id", 1), ("muse_id", 1), ("day", 1)], unique=True)

@app.on_event("startup")
async def ensure_scheduler_indexes():
    """Créer les index nécessaires pour le Scheduler."""
    db = databases.db
    # Drafts programmés & jobs
    await db["scheduled_drafts"].create_index([("tenant_id", 1), ("muse_id", 1), ("status", 1), ("scheduled_at", 1)])
    await db["scheduled_drafts"].create_index([("job_id", 1)], unique=True, sparse=True)
    await db["scheduled_jobs"].create_index([("tenant_id", 1), ("status", 1), ("next_run_at", 1)])

    # Historique publications
    await db["publish_logs"].create_index([("tenant_id", 1), ("muse_id", 1), ("platform", 1), ("status", 1), ("ts", 1)])

    # AB tests
    await db["ab_tests"].create_index([("tenant_id", 1), ("muse_id", 1), ("platform", 1), ("variant", 1), ("campaign_id", 1)])

    # Recyclage
    await db["recycle_policies"].create_index([("tenant_id", 1), ("muse_id", 1), ("active", 1)])

@app.on_event("startup")
async def ensure_ai_assistant_indexes():
    """Créer les index nécessaires pour l'Assistant IA Stratégique."""
    db = databases.db
    # Plans d'action IA (versions mensuelles, horodatées)
    await db["ai_action_plans"].create_index([("tenant_id", 1), ("muse_id", 1), ("month", 1)], unique=True)
    await db["ai_action_plans"].create_index([("created_at", 1)])

    # Alertes stratégiques
    await db["ai_alerts"].create_index([("tenant_id", 1), ("muse_id", 1), ("status", 1), ("ts", 1)])
    await db["ai_alerts"].create_index([("kind", 1), ("ts", 1)])

    # Collaboration suggestions
    await db["ai_collab_suggestions"].create_index([("tenant_id", 1), ("muse_id", 1), ("ts", 1)])
    await db["ai_collab_suggestions"].create_index([("score", -1)])

    # Historique recommandations & feedback
    await db["ai_reco_history"].create_index([("tenant_id", 1), ("muse_id", 1), ("ts", 1)])
    await db["ai_reco_history"].create_index([("applied", 1)])

    # Cache tendances (RAG)
    await db["trends_cache"].create_index([("tenant_id", 1), ("source", 1), ("topic", 1), ("ts", 1)])
    await db["trends_cache"].create_index([("embedding_id", 1)], sparse=True)

@app.on_event("startup")
async def ensure_talent_indexes():
    """Créer les index nécessaires pour la Gestion Centralisée des Talents."""
    db = databases.db

    # Conversations / Inbox
    await db["chat_messages"].create_index([("tenant_id", 1), ("muse_id", 1), ("platform", 1), ("timestamp", -1)])
    await db["chat_threads"].create_index([("tenant_id", 1), ("muse_id", 1), ("user_hash", 1)], unique=True)
    await db["chat_threads"].create_index([("last_ts", -1), ("priority", -1)])

    # Tags & notes fans
    await db["fan_tags"].create_index([("tenant_id", 1), ("muse_id", 1), ("user_hash", 1), ("tag", 1)], unique=True)
    await db["fan_notes"].create_index([("tenant_id", 1), ("muse_id", 1), ("user_hash", 1), ("ts", -1)])

    # Assignments & roles
    await db["operator_roles"].create_index([("tenant_id", 1), ("user_id", 1), ("role", 1)])
    await db["muse_assignments"].create_index([("tenant_id", 1), ("muse_id", 1), ("platform", 1), ("operator_id", 1)], unique=True)

    # Audit trail
    await db["audit_events"].create_index([("tenant_id", 1), ("ts", -1)])
    await db["audit_events"].create_index([("actor_id", 1), ("ts", -1)])
    await db["audit_events"].create_index([("muse_id", 1), ("user_hash", 1), ("ts", -1)])

    # Intégrations
    await db["integration_hooks"].create_index([("tenant_id", 1), ("provider", 1)], unique=True)

    # Agrégations dashboard
    await db["muse_metrics_daily"].create_index([("tenant_id", 1), ("muse_id", 1), ("day", 1)], unique=True)

# --- Scheduler (désactivé en test) ---
if os.getenv("TESTING", "false").lower() != "true":
    from api.services.scheduler.job_runner import start_scheduler, resync_jobs, schedule_weekly_cleanup, schedule_analytics_job
    from api.services.assistant.jobs import schedule_assistant_jobs

    @app.on_event("startup")
    async def start_jobs():
        await start_scheduler()
        await resync_jobs()
        await schedule_weekly_cleanup()
        await schedule_analytics_job()
        await schedule_assistant_jobs()
# api/main.py
"""
Point d'entrée principal de l'application musAI Platform.
- Configure FastAPI, logging, settings
- Initialise les connexions Mongo (CORE + BI) et crée les index (lifespan)
- Monte les routeurs en respectant les feature flags
- Expose des routes Health & DB Info
"""

import os
import logging
import traceback
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, Request, status, Query
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv

# Chargement .env et logging
load_dotenv()
from api.core.logging import setup_logging, get_logger  # doit être initialisé tôt
setup_logging()
logger = get_logger(__name__)

# Settings et DB
from api.core.settings import settings
from api.databases.databases import (
    init_clients,
    close_clients,
    ensure_all_indexes,
    get_core_db,
    get_bi_db,
    get_db_for_collection,
)

# -----------------------------------------------------------------------------
# Lifespan (remplace les anciens @app.on_event('startup'/'shutdown'))
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Bootstrapping musAI Platform...")
    init_clients()
    await ensure_all_indexes()
    logger.info("Mongo CORE/BI ready and indexes ensured.")
    yield
    # Shutdown
    close_clients()
    logger.info("Mongo clients closed. Bye.")

app = FastAPI(
    title="SparkMetrics",
    version=settings.app_version,
    description="API multitenant pour la gestion des influenceuses, chat omnicanal, analytics et monétisation.",
    lifespan=lifespan,
)

# -----------------------------------------------------------------------------
# Handlers d'erreurs
# -----------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error", extra={"errors": exc.errors(), "path": str(request.url)})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=True, extra={"path": request.url.path, "method": request.method})
    if settings.environment == "production":
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()},
    )

# -----------------------------------------------------------------------------
# Root
# -----------------------------------------------------------------------------
@app.get("/", tags=["Root"])
def root():
    return {"message": "Bienvenue sur l'API musAI Platform", "version": settings.app_version}

# -----------------------------------------------------------------------------
# Health & DB Info
# -----------------------------------------------------------------------------
from fastapi import APIRouter
health_router = APIRouter(prefix="/health", tags=["Health"])

@health_router.get("/mongo")
async def health_mongo():
    core = get_core_db()
    bi = get_bi_db()
    # Pings légers (comptage sur collection technique)
    await core["__ping__"].count_documents({})
    await bi["__ping__"].count_documents({})
    return {"status": "ok", "core": "up", "bi": "up"}

@health_router.get("/db-info")
async def db_info(
    collections: List[str] = Query(default=[], description="Liste de collections à inspecter (optionnel)")
):
    """
    Retourne un résumé des bases CORE/BI (quelques collections, tailles, et
    résolution de base par collection via get_db_for_collection).
    """
    core = get_core_db()
    bi = get_bi_db()

    async def _coll_stats(db, coll_name: str) -> Dict[str, Any]:
        try:
            count = await db[coll_name].count_documents({})
            return {"collection": coll_name, "count": count}
        except Exception as e:
            return {"collection": coll_name, "error": str(e)}

    # Quelques collections "phares" par défaut si aucune n'est fournie
    default_core = ["users", "chat_messages", "muses", "scheduled_posts", "activity_logs"]
    default_bi = ["events_funnel", "conversation_daily", "revenue_daily", "ppv_daily", "publish_logs"]

    core_list = collections or default_core
    bi_list = collections or default_bi

    core_stats = [await _coll_stats(core, c) for c in core_list]
    bi_stats = [await _coll_stats(bi, c) for c in bi_list]

    # Résolution de base par collection (exemple)
    resolution = {}
    for c in set(core_list + bi_list):
        db_resolved = get_db_for_collection(c)
        resolution[c] = "BI" if db_resolved.name == bi.name else "CORE"

    return {
        "status": "ok",
        "core": {"db": core.name, "collections": core_stats},
        "bi": {"db": bi.name, "collections": bi_stats},
        "resolution": resolution,
    }

app.include_router(health_router)

# -----------------------------------------------------------------------------
# Import des routeurs applicatifs (tous les prefix DOIVENT commencer par '/')
# -----------------------------------------------------------------------------
from api.routes.auth import router as auth_router
from api.routes.auth_google import router as auth_google_router
from api.routes.users import router as users_router
from api.routes.payments import router as payments_router
from api.routes.webhooks.payments_webhook import router as payments_webhook_router
from api.routes.ppv import router as ppv_router
from api.routes.public_contents import router as public_router
from api.routes.dispatcher import router as dispatcher_router
from api.routes.tunnels_test import router as tunnels_router
from api.routes.instagram_test import router as instagram_test_router
from api.routes.threads_test import router as threads_test_router
from api.routes.snapchat_test import router as snapchat_test_router
from api.routes.scheduler import router as scheduler_router
from api.routes.stats import router as stats_router
from api.routes.stats_tunnels import router as stats_tunnels_router
from api.routes.stats.timeline import router as timeline_router
from api.routes.chats import router as chats_router
from api.routes.analysis.filters import router as filters_router
from api.routes.analysis.tunnel import router as tunnel_analysis_router
from api.routes.webhooks.telegram import router as telegram_webhook_router
from api.routes.webhooks.instagram import router as instagram_webhook_router
from api.routes.webhooks.whatsapp import router as whatsapp_webhook_router
from api.routes.webhooks.tiktok import router as tiktok_webhook_router
from api.routes.webhooks.fanvue import router as fanvue_webhook_router
from api.routes.webhooks.mymfans import router as mymfans_webhook_router
from api.routes.webhooks.manyvids import router as manyvids_webhook_router
from api.routes.platforms import router as platforms_router
from api.routes.ai_marketing import router as ai_marketing_router
from api.routes.analytics_conversations import router as analytics_conv_router
from api.routes.analytics_bi import router as analytics_bi_router
from api.routes.ppv_tracking import router as ppv_tracking_router
from api.routes.assistant import router as assistant_router
from api.routes.talent import router as talent_router
from api.routes.orgs import router as orgs_router

# Routes de base (préfixes corrigés)
app.include_router(auth_router,              prefix="/api/auth",            tags=["Auth"])
app.include_router(auth_google_router,       prefix="/api",                 tags=["Auth Google"])
app.include_router(users_router,             prefix="/api/users",           tags=["Users"])
app.include_router(payments_router,          prefix="/api/payments",        tags=["Payments"])
app.include_router(payments_webhook_router,  prefix="/api/payments/webhook",tags=["Payments Webhook"])
app.include_router(ppv_router,               prefix="/api/ppv",             tags=["PPV Contents"])
app.include_router(public_router,            prefix="/api/contents",        tags=["Public Contents"])
app.include_router(dispatcher_router,        prefix="/api/dispatch",        tags=["Dispatcher"])
app.include_router(tunnels_router,           prefix="/api/tunnels",         tags=["Tunnels"])
app.include_router(instagram_test_router,    prefix="/api/instagram",       tags=["Instagram Test"])
app.include_router(threads_test_router,      prefix="/api/threads",         tags=["Threads Test"])
app.include_router(snapchat_test_router,     prefix="/api/test",            tags=["Snapchat Test"])
app.include_router(stats_router,             prefix="/api/stats",           tags=["Stats"])
app.include_router(stats_tunnels_router,     prefix="/api/stats/tunnels",   tags=["Tunnel Stats"])
app.include_router(timeline_router,          prefix="/api/stats/timeline",  tags=["Timeline Stats"])
app.include_router(chats_router,             prefix="/api",                 tags=["Chat"])            # -> /api/chat/...
app.include_router(filters_router,           prefix="/analysis/filters",    tags=["Filters"])
app.include_router(tunnel_analysis_router,   prefix="/analysis/tunnel",     tags=["Tunnel Analysis"])
app.include_router(telegram_webhook_router,  prefix="/webhook/telegram",    tags=["Telegram Webhook"])
app.include_router(instagram_webhook_router, prefix="/webhook/instagram",   tags=["Instagram Webhook"])
app.include_router(whatsapp_webhook_router,  prefix="/webhook/whatsapp",    tags=["WhatsApp Webhook"])
app.include_router(tiktok_webhook_router,    prefix="/webhook/tiktok",      tags=["TikTok Webhook"])
app.include_router(fanvue_webhook_router,    prefix="/webhook/fanvue",      tags=["Fanvue Webhook"])
app.include_router(mymfans_webhook_router,   prefix="/webhook/mymfans",     tags=["MYM.fans Webhook"])
app.include_router(manyvids_webhook_router,  prefix="/webhook/manyvids",    tags=["ManyVids Webhook"])
app.include_router(platforms_router,         prefix="/api/platforms",       tags=["Platforms"])
app.include_router(ai_marketing_router,      prefix="/api/ai-marketing",    tags=["AI Marketing"])
app.include_router(analytics_conv_router,    prefix="/api",                 tags=["Analytics"])
app.include_router(analytics_bi_router,      prefix="/api",                 tags=["Analytics"])
app.include_router(ppv_tracking_router,      prefix="/api",                 tags=["Monetization"])
app.include_router(assistant_router,         prefix="/api",                 tags=["Assistant"])
app.include_router(talent_router,            prefix="/api",                 tags=["Talent"])
app.include_router(orgs_router,              prefix="/api",                 tags=["Organizations"])

# -----------------------------------------------------------------------------
# Feature flags optionnels (sans casser le boot)
# -----------------------------------------------------------------------------
# CloudPhone
if settings.feature_cloudphone_enabled:
    try:
        from api.routes.cloudphone import router as cloudphone_router
        app.include_router(cloudphone_router, prefix="/api/mobile-cloud", tags=["CloudPhone"])
        logger.info("CloudPhone routes mounted")
    except Exception as e:
        logger.warning(f"CloudPhone routes not mounted: {e}")
else:
    logger.info("CloudPhone feature disabled (FEATURE_CLOUDPHONE_ENABLED=false)")

# OTP
if settings.feature_otp_enabled:
    try:
        from api.routes.otp import router as otp_router
        app.include_router(otp_router, prefix="/api/otp", tags=["OTP"])
        logger.info("OTP routes mounted")
    except Exception as e:
        logger.warning(f"OTP routes not mounted: {e}")
else:
    logger.info("OTP feature disabled (FEATURE_OTP_ENABLED=false)")

# Translator
if settings.feature_translator_enabled:
    try:
        from api.routes.translator import router as translator_router
        app.include_router(translator_router, prefix="/api", tags=["Translator"])
        logger.info("Translator routes mounted")
    except Exception as e:
        logger.warning(f"Translator routes not mounted: {e}")
else:
    logger.info("Translator feature disabled (FEATURE_TRANSLATOR_ENABLED=false)")

# Conversation Recap
if settings.feature_convo_recap_enabled:
    try:
        from api.routes.recap import router as recap_router
        app.include_router(recap_router, prefix="/api", tags=["Recap"])
        logger.info("Conversation Recap routes mounted")
    except Exception as e:
        logger.warning(f"Conversation Recap routes not mounted: {e}")
else:
    logger.info("Conversation Recap feature disabled (FEATURE_CONVO_RECAP_ENABLED=false)")

# Message Builder
if settings.feature_message_builder_enabled:
    try:
        from api.routes.message_builder import router as message_builder_router
        app.include_router(message_builder_router, prefix="/api", tags=["Message Builder"])
        logger.info("Message Builder routes mounted")
    except Exception as e:
        logger.warning(f"Message Builder routes not mounted: {e}")
else:
    logger.info("Message Builder feature disabled (FEATURE_MESSAGE_BUILDER_ENABLED=false)")

# Link Tracking
if settings.feature_link_tracking_enabled:
    try:
        from api.routes.tracking import router as tracking_router
        from api.routes.redirect import router as redirect_router
        app.include_router(tracking_router, prefix="/api", tags=["Tracking"])
        app.include_router(redirect_router)  # /r/{code}
        logger.info("Link Tracking routes mounted")
    except Exception as e:
        logger.warning(f"Link Tracking routes not mounted: {e}")
else:
    logger.info("Link Tracking feature disabled (FEATURE_LINK_TRACKING_ENABLED=false)")

# Collaboration
if settings.feature_collab_enabled:
    try:
        from api.routes.collab import router as collab_router
        from api.services.collab.ws import hub
        from fastapi import WebSocket, WebSocketDisconnect

        app.include_router(collab_router, prefix="/api", tags=["Collaboration"])
        logger.info("Collaboration routes mounted")

        @app.websocket(f"{settings.collab_ws_path}/{{org_id}}")
        async def collab_ws(org_id: str, websocket: WebSocket):
            await hub.connect(org_id, websocket)
            try:
                while True:
                    await websocket.receive_text()  # MVP: no-op
            except WebSocketDisconnect:
                hub.disconnect(org_id, websocket)

        logger.info(f"Collab WebSocket mounted at {settings.collab_ws_path}/{{org_id}}")
    except Exception as e:
        logger.warning(f"Collaboration routes not mounted: {e}")
else:
    logger.info("Collaboration feature disabled (FEATURE_COLLAB_ENABLED=false)")

# -----------------------------------------------------------------------------
# Scheduler (désactivé en test)
# -----------------------------------------------------------------------------
if os.getenv("TESTING", "false").lower() != "true" and settings.enable_scheduler:
    try:
        from api.services.scheduler.job_runner import start_scheduler, resync_jobs, schedule_weekly_cleanup, schedule_analytics_job
        from api.services.assistant.jobs import schedule_assistant_jobs

        @app.on_event("startup")
        async def start_jobs():
            await start_scheduler()
            await resync_jobs()
            await schedule_weekly_cleanup()
            await schedule_analytics_job()
            await schedule_assistant_jobs()
        logger.info("Scheduler jobs registered")
    except Exception as e:
        logger.warning(f"Scheduler not started: {e}")
