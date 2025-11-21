from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from api.services.scheduler.task import dispatch_scheduled_posts  # Utilisez "task" au lieu de "tasks"

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.add_job(
        dispatch_scheduled_posts,
        trigger=IntervalTrigger(minutes=1),  # Vérifie les contenus chaque minute
        name="Dispatch Scheduled Posts"
    )
    scheduler.start()
