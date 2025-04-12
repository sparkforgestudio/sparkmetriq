from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from api.services.scheduler.tasks import dispatch_scheduled_posts

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.add_job(
        dispatch_scheduled_posts,
        trigger=IntervalTrigger(minutes=1),  # vérifie les contenus chaque minute
        name="Dispatch Scheduled Posts"
    )
    scheduler.start()
