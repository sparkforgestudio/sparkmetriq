from fastapi import FastAPI

# Routeurs API
from api.routes.auths import router as auths_router
from api.routes.users import router as users_router
from api.routes.payments import router as payments_router
from api.routes.webhooks.payments_webhook import router as webhook_router
from api.routes.ppv import router as ppv_router
from api.routes.public_contents import router as public_router
from api.routes.dispatcher import router as dispatcher_router
from api.routes.tunnels_test import router as tunnels_router
from api.routes.instagram_test import router as instagram_router
from api.routes.threads_test import router as threads_router
from api.routes.snapchat_test import router as snapchat_test_router
from api.routes.scheduler import router as scheduler_router
from api.routes.stats import router as stats_router
from api.routes.stats_tunnels import router as stats_tunnels_router
from api.routes.stats.timeline import router as timeline_router

# Application FastAPI
app = FastAPI(title="MuseMGM API")

# ✅ Route simple
@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API MuseMGM"}

# ✅ Enregistrement des routeurs
app.include_router(auths_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])
app.include_router(webhook_router, prefix="/api/payments/webhook", tags=["Payments Webhook"])
app.include_router(ppv_router, prefix="/api/ppv", tags=["PPV Contents"])
app.include_router(public_router, prefix="/api/contents", tags=["Public Contents"])
app.include_router(dispatcher_router, prefix="/api/dispatch", tags=["Dispatcher"])
app.include_router(tunnels_router, prefix="/api/tunnels", tags=["Tunnels"])
app.include_router(instagram_router, prefix="/api/instagram", tags=["Instagram"])
app.include_router(threads_router, prefix="/api/threads", tags=["Threads"])
app.include_router(scheduler_router, prefix="/api/scheduler", tags=["Scheduler"])
app.include_router(snapchat_test_router, prefix="/api/test", tags=["Tests"])
app.include_router(stats_router, prefix="/api/stats", tags=["Stats"])
app.include_router(stats_tunnels_router, prefix="/api/stats", tags=["Tunnels"])
app.include_router(timeline_router, prefix="/api/stats", tags=["Statistics"])

# ✅ Démarrage du scheduler au lancement
from services.scheduler.manager import start_scheduler

@app.on_event("startup")
async def startup_event():
    start_scheduler()
