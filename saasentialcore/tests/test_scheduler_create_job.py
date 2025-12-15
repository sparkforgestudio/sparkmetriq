from __future__ import annotations

import pytest
from datetime import datetime, timezone

from saasentialcore.services.scheduler_service import SchedulerService, JobStatus
from .utils_fake_db import FakeDB


@pytest.mark.asyncio
async def test_create_job_applies_defaults():
    db = FakeDB()
    service = SchedulerService(db=db, collection_name="scheduled_tasks")

    scheduled_at = datetime.now(timezone.utc)
    job_data = {
        "job_id": "job-create-1",
        "org_id": "org-1",
        "payload": {"foo": "bar"},
        "scheduled_at": scheduled_at,
    }

    created = await service.create_job(job_data)

    assert created["job_id"] == "job-create-1"
    assert created["org_id"] == "org-1"
    assert created["status"] == JobStatus.PENDING
    assert created["attempt"] == 0
    assert "created_at" in created
    assert "updated_at" in created
    assert created["next_run_at"] == scheduled_at
