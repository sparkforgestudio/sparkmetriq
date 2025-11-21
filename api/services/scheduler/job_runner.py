# api/services/scheduler/job_runner.py
"""
Gestionnaire des jobs APScheduler pour le Scheduler.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from api.databases.databases import db
from api.services.scheduler.publish_service import execute_publish

scheduler = AsyncIOScheduler()

async def start_scheduler():
    """Démarre le scheduler APScheduler."""
    if not scheduler.running:
        scheduler.start()
        print("🚀 APScheduler démarré")

async def stop_scheduler():
    """Arrête le scheduler APScheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("⏹️ APScheduler arrêté")

async def schedule_draft(draft: Dict[str, Any]) -> str:
    """Programme un draft pour publication."""
    run_at = draft["scheduled_at"]
    
    # Vérifier que la date n'est pas dans le passé
    if run_at <= datetime.now(timezone.utc):
        return "past_date"
    
    trigger = DateTrigger(run_date=run_at)
    
    try:
        job = scheduler.add_job(
            lambda: _run_job(draft["_id"], draft["tenant_id"]),
            trigger=trigger,
            id=str(draft["_id"]),
            replace_existing=True,
            misfire_grace_time=300  # 5 minutes de grâce
        )
        return job.id
    except Exception as e:
        print(f"❌ Erreur lors de la programmation du job: {e}")
        return "error"

async def schedule_recurring_job(job_id: str, func, trigger: str, **kwargs):
    """Programme un job récurrent."""
    try:
        job = scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            **kwargs
        )
        return job.id
    except Exception as e:
        print(f"❌ Erreur lors de la programmation du job récurrent: {e}")
        return "error"

async def cancel_job(job_id: str) -> bool:
    """Annule un job programmé."""
    try:
        scheduler.remove_job(job_id)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'annulation du job: {e}")
        return False

async def reschedule_job(job_id: str, new_time: datetime) -> bool:
    """Reprogramme un job à une nouvelle heure."""
    try:
        scheduler.reschedule_job(
            job_id,
            trigger=DateTrigger(run_date=new_time)
        )
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la reprogrammation du job: {e}")
        return False

async def _run_job(draft_id, tenant_id):
    """Exécute un job de publication."""
    try:
        print(f"🔄 Exécution du job pour le draft {draft_id}")
        result = await execute_publish(str(draft_id), str(tenant_id))
        
        if result.get("ok"):
            print(f"✅ Publication réussie pour le draft {draft_id}")
        else:
            print(f"❌ Échec de publication pour le draft {draft_id}: {result.get('reason')}")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution du job: {e}")

async def resync_jobs():
    """Resynchronise les jobs au démarrage."""
    print("🔄 Resynchronisation des jobs...")
    
    now = datetime.now(timezone.utc)
    cur = db["scheduled_drafts"].find({
        "status": {"$in": ["scheduled","queued"]},
        "scheduled_at": {"$gte": now}
    })
    
    synced_count = 0
    for doc in await cur.to_list(None):
        job_id = await schedule_draft(doc)
        if job_id not in ["past_date", "error"]:
            # Mettre à jour le job_id dans la base
            await db["scheduled_drafts"].update_one(
                {"_id": doc["_id"]},
                {"$set": {"job_id": job_id}}
            )
            synced_count += 1
    
    print(f"✅ {synced_count} jobs resynchronisés")

async def schedule_weekly_cleanup():
    """Programme le nettoyage hebdomadaire."""
    # Nettoyer les anciens logs et drafts
    cleanup_func = lambda: _weekly_cleanup()
    
    # Programmer tous les dimanches à 2h du matin
    await schedule_recurring_job(
        "weekly_cleanup",
        cleanup_func,
        "cron",
        day_of_week="sun",
        hour=2,
        minute=0
    )

async def _weekly_cleanup():
    """Nettoyage hebdomadaire des données."""
    try:
        print("🧹 Début du nettoyage hebdomadaire...")
        
        # Supprimer les logs de publication de plus de 90 jours
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
        
        deleted_logs = await db["publish_logs"].delete_many({
            "ts": {"$lt": cutoff_date}
        })
        
        # Supprimer les drafts échoués de plus de 30 jours
        deleted_drafts = await db["scheduled_drafts"].delete_many({
            "status": "failed",
            "updated_at": {"$lt": cutoff_date}
        })
        
        print(f"✅ Nettoyage terminé: {deleted_logs.deleted_count} logs et {deleted_drafts.deleted_count} drafts supprimés")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")

async def get_scheduler_status() -> Dict[str, Any]:
    """Retourne le statut du scheduler."""
    jobs = scheduler.get_jobs()
    
    return {
        "running": scheduler.running,
        "total_jobs": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]
    }

async def schedule_analytics_job():
    """Programme le job d'analytics quotidien."""
    analytics_func = lambda: _daily_analytics()
    
    # Programmer tous les jours à 1h du matin
    await schedule_recurring_job(
        "daily_analytics",
        analytics_func,
        "cron",
        hour=1,
        minute=0
    )

async def _daily_analytics():
    """Analytics quotidien pour le scheduler."""
    try:
        print("📊 Début des analytics quotidiens...")
        
        # Calculer les statistiques du jour précédent
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        start_of_day = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Statistiques des publications
        published_count = await db["publish_logs"].count_documents({
            "status": "published",
            "ts": {"$gte": start_of_day, "$lte": end_of_day}
        })
        
        failed_count = await db["publish_logs"].count_documents({
            "status": "failed",
            "ts": {"$gte": start_of_day, "$lte": end_of_day}
        })
        
        # Statistiques des drafts programmés
        scheduled_count = await db["scheduled_drafts"].count_documents({
            "status": "scheduled",
            "scheduled_at": {"$gte": start_of_day, "$lte": end_of_day}
        })
        
        print(f"📈 Analytics du {yesterday.strftime('%Y-%m-%d')}:")
        print(f"   - Publications réussies: {published_count}")
        print(f"   - Publications échouées: {failed_count}")
        print(f"   - Drafts programmés: {scheduled_count}")
        
    except Exception as e:
        print(f"❌ Erreur lors des analytics: {e}")
