from __future__ import annotations

import pytest
from datetime import datetime, timezone

from saasentialcore.services.scheduler_service import SchedulerService, JobStatus
from .utils_fake_db import FakeDB


@pytest.mark.asyncio
async def test_run_scheduled_job_retries_then_fails():
    db = FakeDB()
    service = SchedulerService(
        db=db,
        collection_name="scheduled_tasks",
        max_attempts=3,
    )

    scheduled_at = datetime.now(timezone.utc)
    job_data = {
        "job_id": "job-retry-1",
        "org_id": "org-1",
        "payload": {"x": 1},
        "scheduled_at": scheduled_at,
    }

    created = await service.create_job(job_data)
    job_id = created["job_id"]

    async def executor(job_doc):
        # Provoque systématiquement une erreur
        raise RuntimeError("boom")

    # Tentative 1
    await service.run_scheduled_job(job_id=job_id, executor_callback=executor)
    job = await service.get_job_by_id(job_id)
    assert job is not None
    assert job["status"] == JobStatus.PENDING  # reprogrammé
    assert job["attempt"] == 1
    assert job["last_error"] == "boom"
    assert job["next_run_at"] is not None

    # Tentative 2
    await service.run_scheduled_job(job_id=job_id, executor_callback=executor)
    job = await service.get_job_by_id(job_id)
    assert job["status"] == JobStatus.PENDING
    assert job["attempt"] == 2
    assert job["last_error"] == "boom"
    assert job["next_run_at"] is not None

    # Tentative 3 → échec définitif
    await service.run_scheduled_job(job_id=job_id, executor_callback=executor)
    job = await service.get_job_by_id(job_id)
    assert job["status"] == JobStatus.FAILED
    assert job["attempt"] == 3
    assert job["last_error"] == "boom"
    assert job["next_run_at"] is None
