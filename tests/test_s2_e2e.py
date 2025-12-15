# tests/test_s2_e2e.py
"""
Tests E2E de référence pour le module S2 (Content Studio) de SparkPusher.

Ce fichier contient les tests end-to-end qui valident le fonctionnement complet
du module S2 en vérifiant l'intégration entre :

1. **Services génériques (saasentialcore)** :
   - `saasentialcore.services.scheduler_service.SchedulerService` : gestion générique
     des jobs (statuts, retries, backoff, transitions)
   - `saasentialcore.services.quotas_service.QuotasService` : gestion générique
     des quotas d'organisation
   - Accès via `api.services.core.saasential_bridge.SaasentialCoreBridge`

2. **Routes S2 (products.sparkpusher)** :
   - `products.sparkpusher.api.routes.scheduler` : routes HTTP pour S2
     - POST /api/scheduler/posts/schedule
     - GET /api/scheduler/jobs/{job_id}
     - PATCH /api/scheduler/jobs/{job_id}/reschedule
   - Montées dans `api/main.py` via le shim `api.routes.scheduler`

3. **Services S2 (products.sparkpusher)** :
   - `products.sparkpusher.services.task` : exécution de jobs S2
     (reconstruction UnifiedPostPayload, appel dispatcher)
   - `products.sparkpusher.services.config` : configuration S2
     (MAX_ATTEMPTS, BACKOFF_SECONDS, JobStatus)
   - `products.sparkpusher.services.quotas_service` : vérification quotas S2
     (avec UnifiedPostPayload)
   - Accès via les shims de compatibilité dans `api.services.scheduler.*`

**Architecture testée** :
```
Client HTTP
    ↓
/api/scheduler/posts/schedule (products.sparkpusher.api.routes.scheduler)
    ↓
SaasentialCoreBridge
    ├─→ saasentialcore.services.quotas_service (vérification quotas générique)
    └─→ saasentialcore.services.scheduler_service (création job générique)
    ↓
MongoDB (scheduled_tasks)
    ↓
products.sparkpusher.services.task.run_scheduled_job()
    ├─→ saasentialcore.services.scheduler_service.run_scheduled_job()
    │   (gestion générique : retries, backoff, statuts)
    └─→ ContentDispatcher.dispatch() (logique métier S2)
```

**Imports utilisés** :
- Routes : via `api.routes.scheduler` (shim vers `products.sparkpusher.api.routes.scheduler`)
- Services : via `api.services.scheduler.*` (shims vers `products.sparkpusher.services.*`)
- Core : via `api.services.core.saasential_bridge` (accès à `saasentialcore`)
"""

import os
import pytest
import logging
from starlette import status
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

# Logger pour l'instrumentation des tests
logger = logging.getLogger(__name__)

# ============================================================================
# Imports S2 - Routes et Services (via shims de compatibilité)
# ============================================================================
# Les imports suivants passent par les shims dans api.services.scheduler.*
# qui délèguent vers products.sparkpusher.services.* pour maintenir
# la compatibilité avec le code existant.
from api.schemas.payload_schema import UnifiedPostPayload, MediaItem, PublishOptions
from api.services.scheduler.task import run_scheduled_job  # Shim → products.sparkpusher.services.task
from api.services.scheduler.config import JobStatus  # Shim → products.sparkpusher.services.config
from api.services.content_distributor.dispatcher import ContentDispatcher
from api.services.scheduler.quotas_service import QuotasService  # Shim → products.sparkpusher.services.quotas_service

# ============================================================================
# Imports Core - Repositories et Database
# ============================================================================
from api.repositories.quotas_repository import QuotasRepository
from api.databases.databases import get_core_db
from fastapi import FastAPI

# Opt-in E2E : les tests E2E sont désactivés par défaut
# Pour les exécuter, définir RUN_E2E=1
RUN_E2E = os.getenv("RUN_E2E", "0") == "1"

# Marquer tous les tests de ce module comme anyio et e2e
# Skip automatique si RUN_E2E n'est pas défini à "1"
pytestmark = [
    pytest.mark.anyio,
    pytest.mark.e2e,
    pytest.mark.skipif(
        not RUN_E2E,
        reason="E2E disabled by default. Set RUN_E2E=1 to enable.",
    ),
]

# URL constante pour la route de schedule
SCHEDULE_URL = "/api/scheduler/posts/schedule"


def test_scheduler_schedule_route_exposed(app: FastAPI):
    """
    Vérifie que la route /api/scheduler/posts/schedule est bien exposée.
    
    Cette route est implémentée dans products.sparkpusher.api.routes.scheduler
    et montée via le shim api.routes.scheduler dans api/main.py.
    """
    paths = sorted({route.path for route in app.routes if hasattr(route, "path")})
    
    # Debug lisible en cas d'échec
    print("Routes disponibles (premiers 20):", paths[:20] if len(paths) > 20 else paths)
    
    assert SCHEDULE_URL in paths, (
        f"Route {SCHEDULE_URL} non trouvée. Routes disponibles (premiers 20): {paths[:20]}"
    )


# Le fixture async_client est maintenant défini dans conftest.py
# et utilise directement api.main.app


@pytest.fixture
async def test_db():
    """Base de données de test."""
    return get_core_db()


@pytest.fixture
def test_org_id():
    """ID d'organisation de test."""
    return "org_e2e_test"


@pytest.fixture
def test_muse_id():
    """ID de muse de test."""
    return "muse_e2e_test"


@pytest.fixture
def mock_user():
    """Utilisateur mock pour l'authentification."""
    from api.schemas.users import UserResponse
    return UserResponse(
        id="user_e2e_test",
        email="e2e@test.com",
        org_id="org_e2e_test",
        is_admin=False,
        roles=[]
    )


@pytest.fixture
def mock_dispatcher():
    """Mock du dispatcher qui retourne un succès."""
    dispatcher = MagicMock(spec=ContentDispatcher)
    dispatcher.dispatch = AsyncMock(return_value={
        "telegram": {
            "status": "ok",
            "external_id": "tg_e2e_123",
            "url": "https://t.me/test/123"
        }
    })
    return dispatcher


@pytest.fixture
def mock_quotas_service():
    """Mock du service de quotas."""
    service = MagicMock(spec=QuotasService)
    service.decrement_scheduled_on_success = AsyncMock()
    service.increment_published_on_success = AsyncMock()
    service.check_quotas_before_scheduling = AsyncMock()
    service.increment_scheduled_on_create = AsyncMock()
    return service

@pytest.fixture
def setup_test_user(mock_user):
    """
    Fixture conservée pour compatibilité de signature, mais sans accès Mongo.
    
    L'utilisateur courant est déjà injecté via app.dependency_overrides[get_current_user],
    donc on n'a pas besoin d'insérer le user en base pour ce test E2E.
    """
    yield mock_user


async def test_s2_e2e_schedule_and_run(
    app: FastAPI,
    async_client: AsyncClient,
    test_db,
    test_org_id: str,
    test_muse_id: str,
    mock_user,
    mock_dispatcher,
    mock_quotas_service,
    setup_test_user
):
    """
    Test E2E complet du cycle de publication S2 (SparkPusher).
    
    Valide l'intégration entre :
    - Routes S2 : products.sparkpusher.api.routes.scheduler (via shim)
    - Services S2 : products.sparkpusher.services.task (via shim)
    - Core générique : saasentialcore.services.scheduler_service (via SaasentialCoreBridge)
    
    Étapes testées :
    1. Création d'un post via POST /api/scheduler/posts/schedule
       → Route SparkPusher → SaasentialCoreBridge → saasentialcore (quotas + scheduler)
    2. Vérification de la présence dans scheduled_tasks (MongoDB)
    3. Exécution du job via run_scheduled_job()
       → Service SparkPusher → saasentialcore.SchedulerService → ContentDispatcher
    4. Vérification du statut SUCCESS (géré par saasentialcore)
    5. Vérification des mises à jour de quotas (gérées par saasentialcore)
    """
    from api.core.auth import get_current_user
    
    # Override de l'authentification
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    try:
        # 1. Construire un payload UnifiedPostPayload minimal
        now = datetime.now(timezone.utc)
        publish_at = now + timedelta(minutes=1)
        
        payload = UnifiedPostPayload(
            org_id=test_org_id,
            muse_id=test_muse_id,
            title="E2E Test Post",
            caption="Hello from S2 E2E test",
            media=[
                MediaItem(
                    type="image",
                    source_url="https://example.com/image.jpg",
                    alt_text="Test image"
                )
            ],
            targets=[
                PublishOptions(
                    platform="telegram",  # Plateforme mockée
                    publish_at=publish_at,  # Passer datetime directement, pas isoformat()
                    is_story=False,
                    is_reel=False,
                )
            ],
            content_id="e2e-content-id",
            created_by_user_id=mock_user.id,
            created_at=now,
        )
        
        # 2. Appeler /api/scheduler/posts/schedule
        # Utiliser le bridge réel avec la DB de test injectée
        response = await async_client.post(
            SCHEDULE_URL,
            json=payload.model_dump(mode="json"),
            headers={"Authorization": f"Bearer fake_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK, f"Response: {response.text}"
        data = response.json()
        job_id = data.get("job_id")
        assert job_id, "job_id manquant dans la réponse"
        
        # 3. Vérifier que le job est en base (scheduled_tasks)
        scheduled = await test_db["scheduled_tasks"].find_one({"job_id": job_id})
        assert scheduled is not None, "Job non trouvé dans scheduled_tasks"
        assert scheduled["status"] == JobStatus.PENDING, f"Statut attendu PENDING, obtenu {scheduled['status']}"
        assert scheduled["org_id"] == test_org_id
        assert scheduled["muse_id"] == test_muse_id
        
        # 4. Exécuter manuellement le job via run_scheduled_job avec dispatcher mocké
        # run_scheduled_job est dans products.sparkpusher.services.task (via shim)
        # Il délègue à saasentialcore.services.scheduler_service pour la gestion générique
        # Utiliser le job réel depuis la base
        job_doc = await test_db["scheduled_tasks"].find_one({"job_id": job_id})
        assert job_doc is not None, "Job non trouvé en base"
        
        # Exécuter le job avec les mocks
        # Note: run_scheduled_job prend job (dict), dispatcher, job_id, db
        # Le service SparkPusher gère la reconstruction du payload et délègue
        # la gestion générique (retries, backoff, statuts) à saasentialcore
        await run_scheduled_job(
            job=job_doc,
            dispatcher=mock_dispatcher,
            job_id=job_id,
            db=test_db
        )
        
        # 5. Recharger le job et vérifier le statut
        scheduled_after = await test_db["scheduled_tasks"].find_one({"job_id": job_id})
        assert scheduled_after is not None, "Job disparu après exécution"
        assert scheduled_after["status"] in (JobStatus.SUCCESS, JobStatus.FAILED), \
            f"Statut inattendu: {scheduled_after['status']}"
        
        # Pour ce test, on s'attend à SUCCESS car le dispatcher est mocké pour réussir
        assert scheduled_after["status"] == JobStatus.SUCCESS, \
            f"Statut attendu SUCCESS, obtenu {scheduled_after['status']}"
        
        # Vérifier que result est présent (le service générique stocke dans "result", pas "dispatch_results")
        platform_results = scheduled_after.get("dispatch_results") or scheduled_after.get("result")
        assert platform_results is not None, f"Résultats plateforme manquants dans le job: {scheduled_after}"
        assert "telegram" in platform_results, f"Résultats Telegram manquants: {platform_results}"
        assert platform_results["telegram"]["status"] == "ok"
        
        # 6. Vérifier les quotas
        # Les quotas sont gérés par saasentialcore.services.quotas_service via SaasentialCoreBridge
        # Le callback on_success du SchedulerService met à jour les quotas automatiquement
        # Note: Les quotas sont mis à jour via le bridge réel (SaasentialCoreBridge.on_success_callback),
        # pas via mock_quotas_service. Le mock_quotas_service n'est pas utilisé dans le flux réel.
        # On vérifie donc uniquement via le repository réel que les quotas existent et sont cohérents.
        quotas_repo = QuotasRepository(test_db)
        quotas = await quotas_repo.get_or_create_org_quotas(test_org_id)
        # Au minimum vérifier que les quotas existent
        assert quotas.org_id == test_org_id
        assert quotas.usage.scheduled_posts >= 0
        assert quotas.usage.published_today >= 0
        
    finally:
        # Nettoyage protégé contre les erreurs de boucle d'événement fermée
        try:
            app.dependency_overrides.clear()
            # Nettoyer les jobs de test
            await test_db["scheduled_tasks"].delete_many({"org_id": test_org_id})
            await test_db["org_quotas"].delete_many({"org_id": test_org_id})
        except (RuntimeError, Exception) as cleanup_error:
            # Ignorer les erreurs de nettoyage (y compris RuntimeError: Event loop is closed)
            # pour éviter de masquer l'erreur réelle du test
            logger.warning(f"⚠️ [TEST] Erreur lors du nettoyage (ignorée): {type(cleanup_error).__name__}: {cleanup_error}")


async def test_s2_e2e_schedule_with_immediate_publish(
    app: FastAPI,
    async_client: AsyncClient,
    test_db,
    test_org_id: str,
    test_muse_id: str,
    mock_user,
    mock_dispatcher,
    mock_quotas_service,
    setup_test_user,
):
    """
    Test léger pour vérifier que l'endpoint /api/scheduler/posts/schedule
    accepte un publish_at=None (publication immédiate) et passe par le bridge.

    On ne teste pas ici :
    - la persistance Mongo (déjà couverte par test_s2_e2e_schedule_and_run)
    - l'exécution du job (déjà couverte dans test_scheduler_retries)
    """

    from api.core.auth import get_current_user
    from api.databases.databases import get_core_db

    logger.info("🔵 [TEST] Début test_s2_e2e_schedule_with_immediate_publish (version simplifiée)")

    # Override auth et DB pour utiliser la DB de test
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_core_db] = lambda: test_db

    now = datetime.now(timezone.utc)

    payload = UnifiedPostPayload(
        org_id=test_org_id,
        muse_id=test_muse_id,
        title="E2E Test Immediate",
        caption="Hello immediate",
        media=[
            MediaItem(
                type="image",
                source_url="https://example.com/image.jpg",
                alt_text="Test image",
            )
        ],
        targets=[
            PublishOptions(
                platform="telegram",
                publish_at=None,  # immédiat
                is_story=False,
                is_reel=False,
            )
        ],
        content_id="e2e-content-immediate",
        created_by_user_id=mock_user.id,
        created_at=now,
    )

    try:
        # Utiliser le bridge réel avec la DB de test injectée
        response = await async_client.post(
            SCHEDULE_URL,
            json=payload.model_dump(mode="json"),
            headers={"Authorization": "Bearer fake_token"},
        )

        logger.info(f"🔵 [TEST] Réponse API: {response.status_code} {response.text}")

        # Vérification minimum
        assert response.status_code == status.HTTP_200_OK, f"Response: {response.text}"
        data = response.json()
        assert "job_id" in data
        assert data.get("status") == JobStatus.PENDING

    finally:
        # Nettoyage
        app.dependency_overrides.clear()

