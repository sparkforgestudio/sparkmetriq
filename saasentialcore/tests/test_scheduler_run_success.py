from __future__ import annotations

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List

from saasentialcore.services.scheduler_service import SchedulerService, JobStatus
from .utils_fake_db import FakeDB


@pytest.mark.asyncio
async def test_run_scheduled_job_success_updates_status_and_calls_callbacks():
    db = FakeDB()
    metrics_events: List[Dict[str, Any]] = []
    success_calls: List[Dict[str, Any]] = []

    def metrics_callback(org_id: str, status: str, metadata: Dict[str, Any]) -> None:
        metrics_events.append(
            {"org_id": org_id, "status": status, "metadata": metadata}
        )

    async def on_success_callback(org_id: str, job_data: Dict[str, Any]) -> None:
        success_calls.append({"org_id": org_id, "job_data": job_data})

    service = SchedulerService(
        db=db,
        collection_name="scheduled_tasks",
        metrics_callback=metrics_callback,
        on_success_callback=on_success_callback,
    )

    scheduled_at = datetime.now(timezone.utc)
    job_data = {
        "job_id": "job-success-1",
        "org_id": "org-1",
        "payload": {"x": 1},
        "scheduled_at": scheduled_at,
    }

    created = await service.create_job(job_data)
    job_id = created["job_id"]

    async def executor(job_doc: Dict[str, Any]) -> Dict[str, Any]:
        # Logique métier simulée
        return {"status": "ok", "value": 42}

    await service.run_scheduled_job(job_id=job_id, executor_callback=executor)

    # Recharger le job
    updated = await service.get_job_by_id(job_id)
    assert updated is not None
    assert updated["status"] == JobStatus.SUCCESS
    assert updated["attempt"] == 1
    assert updated["last_error"] is None
    assert updated["next_run_at"] is None
    assert updated["result"]["status"] == "ok"
    assert updated["result"]["value"] == 42

    # Vérifie que metrics_callback a été appelé au moins pour RUNNING et SUCCESS
    statuses = {m["status"] for m in metrics_events}
    assert JobStatus.RUNNING in statuses
    assert JobStatus.SUCCESS in statuses

    # Vérifie que on_success_callback a bien été appelé
    assert len(success_calls) == 1
    assert success_calls[0]["org_id"] == "org-1"
    assert success_calls[0]["job_data"]["job_id"] == job_id
    assert success_calls[0]["job_data"]["result"]["value"] == 42
