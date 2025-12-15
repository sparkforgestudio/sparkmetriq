from __future__ import annotations

import pytest
from datetime import datetime, timezone
from bson import ObjectId

from saasentialcore.services.scheduler_service import SchedulerService
from .utils_fake_db import FakeDB


@pytest.mark.asyncio
async def test_get_job_by_id_supports_objectid_and_job_id():
    db = FakeDB()
    service = SchedulerService(db=db, collection_name="scheduled_tasks")

    # Job 1 : avec _id ObjectId + job_id standard
    base_job = {
        "job_id": "job-1",
        "org_id": "org-1",
        "payload": {"a": 1},
        "scheduled_at": datetime.now(timezone.utc),
    }
    created = await service.create_job(base_job)
    job1_id = created["job_id"]
    job1_oid = created["_id"]

    # Job 2 : job_id non convertible en ObjectId
    base_job2 = {
        "job_id": "job-custom-xyz",
        "org_id": "org-2",
        "payload": {"b": 2},
        "scheduled_at": datetime.now(timezone.utc),
    }
    created2 = await service.create_job(base_job2)
    job2_id = created2["job_id"]

    # 1) Recherche par _id (ObjectId)
    job_by_oid = await service.get_job_by_id(str(job1_oid))
    assert job_by_oid is not None
    assert job_by_oid["job_id"] == job1_id

    # 2) Recherche par job_id classique
    job_by_job_id = await service.get_job_by_id(job2_id)
    assert job_by_job_id is not None
    assert job_by_job_id["job_id"] == job2_id

    # 3) Fallback _id stocké en string
    # On simule un document avec _id string
    coll = db["scheduled_tasks"]
    doc = {
        "_id": "string-id-123",
        "job_id": "job-3",
        "org_id": "org-3",
        "payload": {"c": 3},
        "scheduled_at": datetime.now(timezone.utc),
    }
    await coll.insert_one(doc)
    job3 = await service.get_job_by_id("string-id-123")
    assert job3 is not None
    assert job3["job_id"] == "job-3"
