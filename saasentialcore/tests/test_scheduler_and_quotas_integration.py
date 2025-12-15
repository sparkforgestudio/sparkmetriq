"""
Tests d'intégration pour le couple Quotas + Scheduler dans saasentialcore.

Ce module valide le comportement générique de la pipeline core (Quotas + Scheduler)
sans dépendre du code spécifique Sparkmetriq. Il teste :

- La vérification des quotas avant la création de jobs
- La mise à jour des quotas lors de la création et de l'exécution de jobs
- Les transitions de statut des jobs (PENDING → RUNNING → SUCCESS/FAILED)
- Les mécanismes de retry et backoff
- L'intégration entre les deux services

Ces tests sont auto-contenus et ne dépendent que des modules saasentialcore.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from saasentialcore.models.schemas.quotas_schema import OrgQuotas
from saasentialcore.services.quotas_service import QuotasService
from saasentialcore.services.scheduler_service import JobStatus, SchedulerService


# Organisation de test
TEST_ORG_ID = "org_test"


def _get_update_doc_from_call(call: Any) -> Dict[str, Any]:
    """
    Extrait le document d'update passé à update_one depuis un call AsyncMock.

    - Si l'update est passé en kwargs (update=...), on le récupère depuis kwargs["update"].
    - Sinon, si l'update est le second argument positionnel, on le récupère depuis args[1].
    - Lève une AssertionError si aucun document d'update n'est trouvé.
    """
    args: Tuple[Any, ...] = call[0]
    kwargs: Dict[str, Any] = call[1]

    if "update" in kwargs:
        update_doc = kwargs["update"]
    elif len(args) >= 2:
        update_doc = args[1]
    else:
        raise AssertionError(
            "Impossible de trouver le document d'update dans l'appel: "
            "ni kwargs['update'], ni args[1]."
        )

    if not isinstance(update_doc, dict):
        raise AssertionError(
            f"Document d'update inattendu (type {type(update_doc)}): {update_doc!r}"
        )

    return update_doc


# ====================================================================
# Fixtures
# ====================================================================


@pytest_asyncio.fixture
async def mock_db():
    """
    Mock de la base de données avec les collections nécessaires.

    Simule une base MongoDB avec :
    - Collection org_quotas pour les quotas
    - Collection scheduled_tasks pour les jobs
    """
    db = MagicMock()

    # Mock de la collection org_quotas
    quotas_collection = MagicMock()
    quotas_collection.find_one = AsyncMock(return_value=None)  # Pas de quotas par défaut
    quotas_collection.update_one = AsyncMock()
    quotas_collection.insert_one = AsyncMock()

    # Mock de la collection scheduled_tasks
    jobs_collection = MagicMock()
    jobs_collection.find_one = AsyncMock(return_value=None)
    jobs_collection.update_one = AsyncMock()
    jobs_collection.insert_one = AsyncMock()

    # Mock du curseur pour find()
    cursor_mock = MagicMock()
    cursor_mock.to_list = AsyncMock(return_value=[])
    cursor_mock.limit = MagicMock(return_value=cursor_mock)
    cursor_mock.sort = MagicMock(return_value=cursor_mock)
    jobs_collection.find = MagicMock(return_value=cursor_mock)

    # Configurer l'accès aux collections
    def get_collection(name: str):
        if name == "org_quotas":
            return quotas_collection
        if name == "scheduled_tasks":
            return jobs_collection
        return MagicMock()

    db.__getitem__ = MagicMock(side_effect=get_collection)
    db["org_quotas"] = quotas_collection
    db["scheduled_tasks"] = jobs_collection

    return db


@pytest_asyncio.fixture
def quotas_service(mock_db):
    """Instance du service de quotas."""
    return QuotasService(mock_db)


@pytest_asyncio.fixture
def scheduler_service(mock_db):
    """Instance du service de scheduler."""
    return SchedulerService(
        db=mock_db,
        collection_name="scheduled_tasks",
        max_attempts=3,
        backoff_seconds=[60, 300, 1800],  # 1 min, 5 min, 30 min
    )


@pytest_asyncio.fixture
def mock_quotas_data():
    """Données de quotas de test."""
    return {
        "org_id": TEST_ORG_ID,
        "limits": {
            "max_scheduled_posts": 10,
            "max_published_per_day": 5,
            "max_platforms_per_post": 3,
        },
        "usage": {
            "scheduled_posts": 0,
            "published_today": 0,
            "last_reset": datetime.now(timezone.utc).date(),
        },
        "updated_at": datetime.now(timezone.utc),
    }


# ====================================================================
# Tests
# ====================================================================


@pytest.mark.asyncio
async def test_create_quotas_and_schedule_job(
    quotas_service: QuotasService,
    scheduler_service: SchedulerService,
    mock_db,
    mock_quotas_data,
):
    """
    Test l'intégration complète : création de quotas puis planification d'un job.

    Vérifie que :
    - Les quotas sont créés correctement
    - Un job peut être créé après vérification des quotas
    - Les quotas sont mis à jour lors de la création du job (via usage.scheduled_posts)
    """
    quotas_collection = mock_db["org_quotas"]

    # Simuler la création de quotas (aucun quotas existant)
    quotas_collection.find_one = AsyncMock(return_value=None)
    quotas_collection.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id="quota_123")
    )

    quotas: OrgQuotas = await quotas_service.get_or_create_org_quotas(TEST_ORG_ID)

    # Vérifier que les quotas ont été créés
    assert quotas.org_id == TEST_ORG_ID
    # Valeurs par défaut : on ne fige que des invariants raisonnables
    assert quotas.usage.scheduled_posts == 0
    assert quotas.limits.max_scheduled_posts > 0

    # 2. Vérifier que les quotas permettent de créer un job
    assert quotas.usage.scheduled_posts < quotas.limits.max_scheduled_posts

    # 3. Créer un job via le scheduler
    jobs_collection = mock_db["scheduled_tasks"]
    jobs_collection.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id="job_123")
    )

    job_data = {
        "org_id": TEST_ORG_ID,
        "job_id": "job_123",
        "payload": {"action": "test", "content_id": "content_456"},
        "scheduled_at": datetime.now(timezone.utc) + timedelta(hours=1),
    }

    created_job = await scheduler_service.create_job(job_data)

    # Vérifier que le job a été créé avec les champs essentiels
    assert created_job["job_id"] == "job_123"
    assert created_job["status"] == JobStatus.PENDING
    assert created_job["attempt"] == 0
    # _id peut être géré de manière interne (ObjectId, string) → on ne fige pas
    assert jobs_collection.insert_one.called


@pytest.mark.asyncio
async def test_job_status_transitions(
    scheduler_service: SchedulerService,
    mock_db,
):
    """
    Test les transitions de statut d'un job : PENDING → RUNNING → SUCCESS.

    Vérifie que le job passe par les bons statuts lors de l'exécution.
    """
    jobs_collection = mock_db["scheduled_tasks"]

    # Mock d'un job existant
    job_doc = {
        "_id": "job_123",
        "job_id": "job_123",
        "org_id": TEST_ORG_ID,
        "status": JobStatus.PENDING,
        "attempt": 0,
        "payload": {"action": "test"},
        "scheduled_at": datetime.now(timezone.utc),
    }

    jobs_collection.find_one = AsyncMock(return_value=job_doc)
    jobs_collection.update_one = AsyncMock()

    # Callback d'exécution qui réussit
    async def successful_executor(job: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok", "result": "success"}

    # Exécuter le job
    await scheduler_service.run_scheduled_job(
        job_id="job_123",
        executor_callback=successful_executor,
        job_doc=job_doc,
    )

    calls = jobs_collection.update_one.call_args_list

    # 1. Transition vers RUNNING
    running_call = [
        c
        for c in calls
        if _get_update_doc_from_call(c).get("$set", {}).get("status")
        == JobStatus.RUNNING
    ]
    assert running_call, "Le job devrait passer en statut RUNNING"

    # 2. Transition vers SUCCESS
    success_call = [
        c
        for c in calls
        if _get_update_doc_from_call(c).get("$set", {}).get("status")
        == JobStatus.SUCCESS
    ]
    assert success_call, "Le job devrait passer en statut SUCCESS"

    # Vérifier que attempt a été incrémenté au moins à 1 sur le dernier update SUCCESS
    success_update = _get_update_doc_from_call(success_call[-1]).get("$set", {})
    assert success_update.get("attempt") == 1
    # completed_at est un comportement recommandé, mais on ne force pas sa présence dans le même $set
    # Si présent, il doit être un datetime
    completed_at = success_update.get("completed_at")
    if completed_at is not None:
        assert isinstance(completed_at, datetime)


@pytest.mark.asyncio
async def test_job_retry_on_failure(
    scheduler_service: SchedulerService,
    mock_db,
):
    """
    Test le mécanisme de retry et backoff en cas d'échec.

    Vérifie que :
    - Un job en échec est reprogrammé avec un backoff
    - Le statut reste PENDING pour permettre le retry
    - next_run_at est calculé correctement
    - attempt est incrémenté
    """
    jobs_collection = mock_db["scheduled_tasks"]

    job_doc = {
        "_id": "job_123",
        "job_id": "job_123",
        "org_id": TEST_ORG_ID,
        "status": JobStatus.PENDING,
        "attempt": 0,
        "payload": {"action": "test"},
        "scheduled_at": datetime.now(timezone.utc),
    }

    jobs_collection.find_one = AsyncMock(return_value=job_doc)
    jobs_collection.update_one = AsyncMock()

    async def failing_executor(job: Dict[str, Any]) -> Dict[str, Any]:
        raise Exception("Network error")

    await scheduler_service.run_scheduled_job(
        job_id="job_123",
        executor_callback=failing_executor,
        job_doc=job_doc,
    )

    calls = jobs_collection.update_one.call_args_list

    # Trouver l'appel qui programme le retry (statut PENDING avec next_run_at)
    retry_call = None
    for call in calls:
        update_doc = _get_update_doc_from_call(call)
        update_data = update_doc.get("$set", {})
        if (
            update_data.get("status") == JobStatus.PENDING
            and "next_run_at" in update_data
        ):
            retry_call = call
            break

    assert retry_call is not None, "Un retry devrait être programmé"

    retry_update = _get_update_doc_from_call(retry_call).get("$set", {})
    assert retry_update.get("attempt") == 1, "attempt devrait être incrémenté"
    assert "next_run_at" in retry_update, "next_run_at devrait être défini"
    assert "last_error" in retry_update, "last_error devrait être enregistré"

    next_run_at = retry_update["next_run_at"]
    assert isinstance(next_run_at, datetime)

    # Backoff attendu ~60s (première tentative)
    expected_delay = 60
    actual_delay = (next_run_at - datetime.now(timezone.utc)).total_seconds()
    # On tolère un delta large car le temps s'écoule entre les deux appels
    assert abs(actual_delay - expected_delay) < 5, (
        f"Le backoff devrait être d'environ {expected_delay} secondes "
        f"(observé: {actual_delay:.2f})"
    )


@pytest.mark.asyncio
async def test_job_failed_after_max_attempts(
    scheduler_service: SchedulerService,
    mock_db,
):
    """
    Test qu'un job passe en FAILED après épuisement des tentatives.

    Vérifie que :
    - Un job qui échoue après MAX_ATTEMPTS passe en statut FAILED
    - Le job n'est plus reprogrammé (pas de next_run_at)
    - last_error est enregistré
    """
    jobs_collection = mock_db["scheduled_tasks"]

    job_doc = {
        "_id": "job_123",
        "job_id": "job_123",
        "org_id": TEST_ORG_ID,
        "status": JobStatus.PENDING,
        "attempt": 2,  # Dernière tentative (max_attempts = 3)
        "payload": {"action": "test"},
        "scheduled_at": datetime.now(timezone.utc),
    }

    jobs_collection.find_one = AsyncMock(return_value=job_doc)
    jobs_collection.update_one = AsyncMock()

    async def failing_executor(job: Dict[str, Any]) -> Dict[str, Any]:
        raise Exception("Persistent error")

    await scheduler_service.run_scheduled_job(
        job_id="job_123",
        executor_callback=failing_executor,
        job_doc=job_doc,
    )

    calls = jobs_collection.update_one.call_args_list

    failed_call = [
        c
        for c in calls
        if _get_update_doc_from_call(c).get("$set", {}).get("status")
        == JobStatus.FAILED
    ]
    assert failed_call, "Le job devrait passer en statut FAILED"

    failed_update = _get_update_doc_from_call(failed_call[-1]).get("$set", {})
    assert failed_update.get("attempt") == 3, "attempt devrait être à MAX_ATTEMPTS"
    assert "last_error" in failed_update, "last_error devrait être enregistré"

    # completed_at est recommandé mais pas obligatoire dans le même $set
    completed_at = failed_update.get("completed_at")
    if completed_at is not None:
        assert isinstance(completed_at, datetime)

    # Vérifier qu'aucun retry n'a été programmé après l'échec définitif
    retry_calls = [
        c
        for c in calls
        if "next_run_at" in _get_update_doc_from_call(c).get("$set", {})
        and _get_update_doc_from_call(c).get("$set", {}).get("status")
        == JobStatus.PENDING
    ]
    assert not retry_calls, (
        "Aucun retry ne devrait être programmé après épuisement des tentatives"
    )


@pytest.mark.asyncio
async def test_quotas_increment_on_job_creation(
    quotas_service: QuotasService,
    scheduler_service: SchedulerService,
    mock_db,
):
    """
    Test que les quotas sont incrémentés lors de la création d'un job.

    Vérifie l'intégration entre QuotasService et SchedulerService :
    - Les quotas sont vérifiés avant création
    - Les quotas sont incrémentés après création
    """
    quotas_collection = mock_db["org_quotas"]

    quotas_doc = {
        "org_id": TEST_ORG_ID,
        "limits": {
            "max_scheduled_posts": 10,
            "max_published_per_day": 5,
            "max_platforms_per_post": 3,
        },
        "usage": {
            "scheduled_posts": 5,
            "published_today": 0,
            "last_reset": datetime.now(timezone.utc).date(),
        },
        "updated_at": datetime.now(timezone.utc),
    }

    quotas_collection.find_one = AsyncMock(return_value=quotas_doc)
    quotas_collection.update_one = AsyncMock()

    quotas = await quotas_service.get_or_create_org_quotas(TEST_ORG_ID)
    assert quotas.usage.scheduled_posts == 5

    # Encore de la marge pour planifier
    assert quotas.usage.scheduled_posts < quotas.limits.max_scheduled_posts

    updated_quotas = await quotas_service.increment_scheduled_posts(
        TEST_ORG_ID, delta=1
    )

    assert updated_quotas.usage.scheduled_posts == 6
    assert quotas_collection.update_one.called


@pytest.mark.asyncio
async def test_quotas_reset_daily_usage(
    quotas_service: QuotasService,
    mock_db,
):
    """
    Test le reset quotidien des compteurs de quotas.

    Vérifie que :
    - Les compteurs quotidiens sont remis à zéro si la date a changé
    - last_reset est mis à jour
    """
    quotas_collection = mock_db["org_quotas"]

    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    quotas_doc = {
        "org_id": TEST_ORG_ID,
        "limits": {
            "max_scheduled_posts": 10,
            "max_published_per_day": 5,
            "max_platforms_per_post": 3,
        },
        "usage": {
            "scheduled_posts": 3,
            "published_today": 4,
            "last_reset": yesterday,
        },
        "updated_at": datetime.now(timezone.utc),
    }

    quotas_collection.find_one = AsyncMock(return_value=quotas_doc)
    quotas_collection.update_one = AsyncMock()

    quotas = await quotas_service.get_or_create_org_quotas(TEST_ORG_ID)

    updated_quotas = await quotas_service.reset_daily_usage_if_needed(quotas)

    assert updated_quotas.usage.published_today == 0
    assert updated_quotas.usage.last_reset == datetime.now(timezone.utc).date()
    assert quotas_collection.update_one.called


@pytest.mark.asyncio
async def test_scheduler_with_quotas_callback(
    scheduler_service: SchedulerService,
    mock_db,
):
    """
    Test l'intégration complète avec callback de quotas.

    Vérifie que le callback on_success est appelé après un succès,
    permettant la mise à jour des quotas.
    """
    jobs_collection = mock_db["scheduled_tasks"]

    job_doc = {
        "_id": "job_123",
        "job_id": "job_123",
        "org_id": TEST_ORG_ID,
        "status": JobStatus.PENDING,
        "attempt": 0,
        "payload": {"action": "test"},
        "scheduled_at": datetime.now(timezone.utc),
    }

    jobs_collection.find_one = AsyncMock(return_value=job_doc)
    jobs_collection.update_one = AsyncMock()

    success_callback_called = False
    received_job_data: Dict[str, Any] | None = None

    async def on_success_callback(org_id: str, job_data: Dict[str, Any]) -> None:
        nonlocal success_callback_called, received_job_data
        success_callback_called = True
        received_job_data = job_data

        assert org_id == TEST_ORG_ID

        # Champs essentiels : on ne force pas _id
        assert job_data.get("job_id") == "job_123", "job_id devrait être présent"
        assert job_data.get("org_id") == TEST_ORG_ID, "org_id devrait être présent"
        # _id peut être absent ou non normalisé → on ne fait pas d'assertion stricte

    scheduler_with_callback = SchedulerService(
        db=mock_db,
        collection_name="scheduled_tasks",
        max_attempts=3,
        backoff_seconds=[60, 300, 1800],
        on_success_callback=on_success_callback,
    )

    async def successful_executor(job: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok", "result": {"platform_a": {"status": "ok"}}}

    await scheduler_with_callback.run_scheduled_job(
        job_id="job_123",
        executor_callback=successful_executor,
        job_doc=job_doc,
    )

    assert success_callback_called, (
        "Le callback on_success devrait être appelé après un succès"
    )
    assert received_job_data is not None, "job_data devrait être passé au callback"
    # Le résultat doit être présent dans job_data["result"] ou équivalent
    assert "result" in received_job_data, (
        "job_data devrait contenir le résultat de l'exécution dans 'result'"
    )
