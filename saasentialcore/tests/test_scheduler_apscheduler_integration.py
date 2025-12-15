from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Awaitable, Callable, List

from saasentialcore.services.scheduler_service import SchedulerService, JobStatus
from .utils_fake_db import FakeDB


class FakeApsJob:
    def __init__(self, job_id: str, func: Callable[..., Awaitable[None]], kwargs: Dict[str, Any], run_date: datetime):
        self.id = job_id
        self.func = func
        self.kwargs = kwargs
        self.run_date = run_date


class FakeAsyncIOScheduler:
    def __init__(self) -> None:
        self.jobs: List[FakeApsJob] = []

    def add_job(
        self,
        func: Callable[..., Awaitable[None]],
        trigger: str,
        run_date: datetime,
        kwargs: Dict[str, Any],
        id: str,
        replace_existing: bool,
        misfire_grace_time: int,
    ) -> FakeApsJob:
        job = FakeApsJob(job_id=id, func=func, kwargs=kwargs, run_date=run_date)
        # On remplace si un job existe avec le même id
        self.jobs = [j for j in self.jobs if j.id != id]
        self.jobs.append(job)
        return job


@pytest.mark.asyncio
async def test_schedule_with_apscheduler_and_execution():
    db = FakeDB()
    scheduler = FakeAsyncIOScheduler()
    service = SchedulerService(db=db, collection_name="scheduled_tasks")

    scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=10)
    job_data = {
        "job_id": "job-aps-1",
        "org_id": "org-aps",
        "payload": {"foo": "bar"},
        "scheduled_at": scheduled_at,
    }

    created = await service.create_job(job_data)
    job_id = created["job_id"]

    exec_calls: List[Dict[str, Any]] = []

    async def executor(job_doc: Dict[str, Any]) -> Dict[str, Any]:
        exec_calls.append({"job_id": job_doc.get("job_id")})
        return {"status": "ok"}

    aps_job_id = await service.schedule_with_apscheduler(
        job_id=job_id,
        scheduled_at=scheduled_at,
        apscheduler=scheduler,
        executor_callback=executor,
        misfire_grace_time=60,
    )

    assert aps_job_id == created["job_id"]
    assert len(scheduler.jobs) == 1
    fake_job = scheduler.jobs[0]
    assert fake_job.id == aps_job_id

    # Simulation de l'exécution APScheduler
    await fake_job.func(**fake_job.kwargs)

    # Vérifier que l'exécuteur a été appelé et que le job est en SUCCESS
    assert len(exec_calls) == 1
    updated = await service.get_job_by_id(job_id)
    assert updated is not None
    assert updated["status"] == JobStatus.SUCCESS
