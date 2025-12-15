"""
Service de scheduler générique pour saasentialcore.

Ce module gère la logique métier générique du scheduler :
- Exécution de jobs avec retries et backoff
- Gestion des transitions de statut (PENDING → RUNNING → SUCCESS / FAILED)
- Persistance MongoDB dans une collection générique (scheduled_tasks)
- Logs structurés (console + handler optionnel, ex. Telegram)
- Publication de métriques via un callback
- Callback de succès pour les services consommateurs (ex: mise à jour des quotas)

Cette implémentation est agnostique du produit et se base uniquement sur la structure
générique des jobs dans la collection `scheduled_tasks`.

NOTE :
- Les applications consommatrices l'utilisent via un bridge (SaasentialCoreBridge),
  jamais directement.
"""

from __future__ import annotations

from typing import (
    Optional,
    Callable,
    Any,
    Dict,
    Awaitable,
    Mapping,
    List,
)
from datetime import datetime, timedelta, timezone
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from pydantic import BaseModel


# Configuration par défaut (peut être surchargée par produit)
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_SECONDS = [60, 300, 1800]  # 1 min, 5 min, 30 min


class JobStatus:
    """Statuts possibles d'un job."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# Logger structuré pour le scheduler (centralisé)
scheduler_logger = logging.getLogger("scheduler")
scheduler_logger.setLevel(logging.INFO)

if not scheduler_logger.handlers:
    # Handler console par défaut
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [scheduler] %(message)s"
    )
    handler.setFormatter(formatter)
    scheduler_logger.addHandler(handler)

    # Handler Telegram optionnel (si disponible)
    try:
        from logs.telegram_handler import TelegramLogHandler  # type: ignore

        telegram_handler = TelegramLogHandler()
        telegram_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        telegram_handler.setFormatter(telegram_formatter)
        scheduler_logger.addHandler(telegram_handler)
    except Exception:
        # Le handler Telegram est optionnel : on ignore s'il n'existe pas
        pass


class SchedulerService:
    """
    Service générique de gestion des jobs planifiés.

    Responsabilités :
    - Exécuter un job en appliquant les règles de retries / backoff
    - Gérer les statuts (PENDING, RUNNING, SUCCESS, FAILED)
    - Enregistrer les erreurs et résultats
    - Publier des logs structurés
    - Publier des métriques via metrics_callback
    - Appeler un callback de succès (on_success_callback) pour le produit

    Cette implémentation est agnostique du produit et repose sur la collection
    MongoDB `scheduled_tasks` ou une collection équivalente.
    """

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        collection_name: str = "scheduled_tasks",
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff_seconds: Optional[List[int]] = None,
        metrics_callback: Optional[
            Callable[[str, str, Dict[str, Any]], None]
        ] = None,
        on_success_callback: Optional[
            Callable[[str, Dict[str, Any]], Awaitable[None]]
        ] = None,
    ) -> None:
        """
        Initialise le service de scheduler.

        Args:
            db: Base de données MongoDB (AsyncIOMotorDatabase)
            collection_name: Nom de la collection MongoDB pour les jobs
            max_attempts: Nombre maximum de tentatives avant échec définitif
            backoff_seconds:
                Liste des délais de backoff en secondes. Si None, utilise
                DEFAULT_BACKOFF_SECONDS. La longueur de la liste peut être
                >= max_attempts, sinon le dernier délai est réutilisé.
            metrics_callback:
                Callback optionnel pour publier des métriques.
                Signature: (org_id: str, status: str, metadata: Dict[str, Any]) -> None
            on_success_callback:
                Callback optionnel appelé après un succès (async).
                Signature: async (org_id: str, job_data: Dict[str, Any]) -> None
        """
        self.db: AsyncIOMotorDatabase = db
        self.collection = db[collection_name]
        self.max_attempts = max_attempts
        self.backoff_seconds: List[int] = (
            backoff_seconds if backoff_seconds is not None else DEFAULT_BACKOFF_SECONDS
        )
        if len(self.backoff_seconds) == 0:
            self.backoff_seconds = DEFAULT_BACKOFF_SECONDS

        self.metrics_callback = metrics_callback
        self.on_success_callback = on_success_callback

    # ==================================================================
    # ===============           CRUD DE BASE             ================
    # ==================================================================

    async def create_job(self, job_data: Mapping[str, Any]) -> Dict[str, Any]:
        """
        Crée un job dans la collection `scheduled_tasks`.

        Cette méthode applique les valeurs par défaut :
        - status = PENDING
        - attempt = 0
        - created_at / updated_at / next_run_at

        Args:
            job_data: Dictionnaire décrivant le job.

        Returns:
            Le document inséré, tel que récupéré depuis la collection.
        """
        now = datetime.now(timezone.utc)

        data: Dict[str, Any] = dict(job_data)
        data.setdefault("status", JobStatus.PENDING)
        data.setdefault("attempt", 0)
        data.setdefault("created_at", now)
        data.setdefault("updated_at", now)

        # next_run_at = scheduled_at par défaut si présent
        if "next_run_at" not in data:
            scheduled_at = data.get("scheduled_at", now)
            data["next_run_at"] = scheduled_at

        safe_data = self._to_mongo_safe(data)
        result = await self.collection.insert_one(safe_data)
        inserted = await self.collection.find_one({"_id": result.inserted_id})
        return inserted or safe_data

    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un job par son ID.

        Supporte plusieurs formats d'ID :
        - ObjectId MongoDB (_id)
        - job_id (string UUID ou autre)
        - _id stocké sous forme de string (fallback)
        """
        # Essayer d'abord avec _id (ObjectId)
        try:
            oid = ObjectId(job_id)
            job = await self.collection.find_one({"_id": oid})
            if job:
                return job
        except Exception:
            pass

        # Essayer avec job_id (string)
        job = await self.collection.find_one({"job_id": job_id})
        if job:
            return job

        # Essayer avec _id comme string (fallback)
        return await self.collection.find_one({"_id": job_id})

    async def get_pending_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les jobs en attente d'exécution.

        Un job est considéré "prêt" si :
        - status = PENDING
        - next_run_at <= maintenant

        Args:
            limit: Nombre maximum de jobs à retourner.

        Returns:
            Liste de documents de jobs.
        """
        now = datetime.now(timezone.utc)
        query = {
            "status": JobStatus.PENDING,
            "next_run_at": {"$lte": now},
        }
        cursor = (
            self.collection.find(query)
            .sort("next_run_at", 1)
            .limit(limit)
        )
        jobs = await cursor.to_list(length=limit)
        return jobs

    # ==================================================================
    # ===============          LOGIQUE D'EXÉCUTION       ================
    # ==================================================================

    async def run_scheduled_job(
        self,
        job_id: str,
        executor_callback: Callable[[Dict[str, Any]], Awaitable[Any]],
        job_doc: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Exécute un job planifié en appliquant retries / backoff.

        Args:
            job_id: Identifiant du job (job_id ou _id string)
            executor_callback:
                Fonction async qui exécute la logique métier du job.
                Signature: async (job_doc: Dict[str, Any]) -> Any
            job_doc:
                Document du job si déjà connu (pour éviter un fetch initial).
        """
        # Récupération du job si non fourni
        job = job_doc or await self.get_job_by_id(job_id)
        if job is None:
            scheduler_logger.warning(
                "Job %s not found, skipping execution", job_id,
                extra={"event": "scheduler.job.not_found", "job_id": job_id},
            )
            return

        org_id = job.get("org_id", "")

        # Si le job est déjà en succès, on ne le relance pas
        if job.get("status") == JobStatus.SUCCESS:
            scheduler_logger.info(
                "Job %s already in SUCCESS status, skipping", job_id,
                extra={
                    "event": "scheduler.job.already_success",
                    "job_id": job_id,
                    "org_id": org_id,
                },
            )
            return

        # Déterminer le numéro de tentative
        attempt = int(job.get("attempt", 0))

        # Passer à RUNNING
        now = datetime.now(timezone.utc)
        running_fields = {
            "status": JobStatus.RUNNING,
            "updated_at": now,
        }
        await self._update_job_fields(job_id=job_id, fields=running_fields, job_doc=job)

        # Logs + métriques RUNNING
        metadata = {
            "job_id": job_id,
            "attempt": attempt,
            "status": JobStatus.RUNNING,
            "platforms": self._extract_platforms_from_job(job),
        }
        scheduler_logger.info(
            "Job %s started (attempt=%s)", job_id, attempt,
            extra={"event": "scheduler.job.running", **metadata},
        )
        if self.metrics_callback:
            self.metrics_callback(org_id, JobStatus.RUNNING, metadata)

        # Exécution métier
        try:
            result = await executor_callback(job)

            # Succès
            attempt += 1
            success_fields = {
                "status": JobStatus.SUCCESS,
                "attempt": attempt,
                "last_error": None,
                "updated_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc),
                "result": self._to_mongo_safe(result),
                "next_run_at": None,
            }
            await self._update_job_fields(
                job_id=job_id,
                fields=success_fields,
                job_doc=job,
            )

            success_metadata = {
                "job_id": job_id,
                "attempt": attempt,
                "status": JobStatus.SUCCESS,
                "platforms": self._extract_platforms_from_job(job),
            }
            scheduler_logger.info(
                "Job %s completed successfully", job_id,
                extra={"event": "scheduler.job.success", **success_metadata},
            )
            if self.metrics_callback:
                self.metrics_callback(org_id, JobStatus.SUCCESS, success_metadata)

            # Callback produit (ex: quotas, logs détaillés, historique)
            if self.on_success_callback:
                # On reconstruit un job_data consolidé
                job_data = dict(job)
                job_data["job_id"] = job_data.get("job_id", job_id)
                job_data["result"] = result
                await self.on_success_callback(org_id, job_data)

        except Exception as exc:
            # Echec de tentative : décider si on retente ou si l'on passe en FAILED
            attempt += 1
            error_str = str(exc)

            if attempt >= self.max_attempts:
                # Echec définitif
                fail_fields = {
                    "status": JobStatus.FAILED,
                    "attempt": attempt,
                    "last_error": error_str,
                    "updated_at": datetime.now(timezone.utc),
                    "next_run_at": None,
                }
                await self._update_job_fields(
                    job_id=job_id,
                    fields=fail_fields,
                    job_doc=job,
                )

                fail_metadata = {
                    "job_id": job_id,
                    "attempt": attempt,
                    "status": JobStatus.FAILED,
                    "platforms": self._extract_platforms_from_job(job),
                }
                scheduler_logger.error(
                    "Job %s failed permanently after %s attempts: %s",
                    job_id,
                    attempt,
                    error_str,
                    extra={"event": "scheduler.job.failed", **fail_metadata},
                )
                if self.metrics_callback:
                    self.metrics_callback(org_id, JobStatus.FAILED, fail_metadata)
            else:
                # Echec mais retry planifié
                delay = self._get_backoff_delay(attempt)
                next_run_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
                retry_fields = {
                    "status": JobStatus.PENDING,
                    "attempt": attempt,
                    "last_error": error_str,
                    "updated_at": datetime.now(timezone.utc),
                    "next_run_at": next_run_at,
                }
                await self._update_job_fields(
                    job_id=job_id,
                    fields=retry_fields,
                    job_doc=job,
                )

                retry_metadata = {
                    "job_id": job_id,
                    "attempt": attempt,
                    "status": JobStatus.PENDING,
                    "platforms": self._extract_platforms_from_job(job),
                    "next_run_at": next_run_at.isoformat(),
                }
                scheduler_logger.warning(
                    "Job %s failed on attempt %s, scheduled retry in %s seconds: %s",
                    job_id,
                    attempt,
                    delay,
                    error_str,
                    extra={"event": "scheduler.job.retry_scheduled", **retry_metadata},
                )
                # On peut publier une métrique d'échec temporaire si besoin
                if self.metrics_callback:
                    self.metrics_callback(org_id, JobStatus.PENDING, retry_metadata)

    # ==================================================================
    # ===============      INTÉGRATION APSCHEDULER      ================
    # ==================================================================

    async def schedule_with_apscheduler(
        self,
        job_id: str,
        scheduled_at: datetime,
        apscheduler: Any,  # AsyncIOScheduler
        executor_callback: Callable[[Dict[str, Any]], Awaitable[Any]],
        misfire_grace_time: int = 300,
    ) -> str:
        """
        Programme un job dans APScheduler en s’appuyant sur la persistance générique.

        - Vérifie que le job existe (via get_job_by_id)
        - Planifie son exécution dans APScheduler à 'scheduled_at'
        - L’exécution réelle se fait via run_scheduled_job() avec executor_callback

        Args:
            job_id: ID du job dans scheduled_tasks
            scheduled_at: Date/heure de planification
            apscheduler: Instance AsyncIOScheduler (APScheduler)
            executor_callback: Callback métier async
            misfire_grace_time: Délai de grâce en secondes

        Returns:
            ID du job APScheduler.
        """
        job = await self.get_job_by_id(job_id)
        if job is None:
            raise ValueError(f"Cannot schedule job {job_id}: not found.")

        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if scheduled_at < now:
            # Si la date est passée : exécution dès que possible
            scheduled_at = now

        async def _apscheduler_wrapper(job_id_inner: str) -> None:
            job_doc_inner = await self.get_job_by_id(job_id_inner)
            await self.run_scheduled_job(
                job_id=job_id_inner,
                executor_callback=executor_callback,
                job_doc=job_doc_inner,
            )

        # APScheduler peut accepter des coroutines avec AsyncIOScheduler
        aps_job = apscheduler.add_job(
            _apscheduler_wrapper,
            trigger="date",
            run_date=scheduled_at,
            kwargs={"job_id_inner": job_id},
            id=str(job.get("job_id", job_id)),
            replace_existing=True,
            misfire_grace_time=misfire_grace_time,
        )

        scheduler_logger.info(
            "APScheduler job %s scheduled for %s",
            aps_job.id,
            scheduled_at.isoformat(),
            extra={
                "event": "scheduler.apscheduler.job_scheduled",
                "job_id": job_id,
                "aps_job_id": aps_job.id,
                "run_date": scheduled_at.isoformat(),
            },
        )
        return aps_job.id

    async def resync_jobs_for_apscheduler(
        self,
        apscheduler: Any,  # AsyncIOScheduler
        executor_callback: Callable[[Dict[str, Any]], Awaitable[Any]],
        filter_query: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Parcourt les jobs PENDING dans la collection `scheduled_tasks` et les
        reprogramme dans APScheduler en utilisant schedule_with_apscheduler.

        Args:
            apscheduler: Instance AsyncIOScheduler
            executor_callback: Callback métier async
            filter_query: Filtre MongoDB optionnel

        Returns:
            Nombre de jobs resynchronisés.
        """
        base_query: Dict[str, Any] = {
            "status": JobStatus.PENDING,
        }
        if filter_query:
            base_query.update(filter_query)

        cursor = self.collection.find(base_query)
        jobs = await cursor.to_list(length=None)
        count = 0

        for job in jobs:
            job_id = str(job.get("job_id") or job.get("_id"))
            scheduled_at = job.get("next_run_at") or job.get("scheduled_at")
            if not scheduled_at:
                continue

            try:
                await self.schedule_with_apscheduler(
                    job_id=job_id,
                    scheduled_at=scheduled_at,
                    apscheduler=apscheduler,
                    executor_callback=executor_callback,
                )
                count += 1
            except Exception as exc:
                scheduler_logger.error(
                    "Failed to reschedule job %s in APScheduler: %s",
                    job_id,
                    str(exc),
                    extra={
                        "event": "scheduler.apscheduler.resync_failed",
                        "job_id": job_id,
                    },
                )

        scheduler_logger.info(
            "Resynchronised %s jobs into APScheduler",
            count,
            extra={"event": "scheduler.apscheduler.resync_completed", "count": count},
        )
        return count

    # ==================================================================
    # ===============         FONCTIONS INTERNES        ================
    # ==================================================================

    async def _update_job_fields(
        self,
        job_id: str,
        fields: Dict[str, Any],
        job_doc: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Met à jour des champs arbitraires sur un job.

        Cette méthode :
        - gère la construction du filtre MongoDB (_id ou job_id),
        - applique la conversion Mongo-safe,
        - exécute l'opération $set.

        Args:
            job_id: Identifiant du job (job_id ou _id)
            fields: Champs à mettre à jour
            job_doc: Document du job si déjà connu (facilite la construction du filtre)
        """
        filter_query: Dict[str, Any] = {}

        # Si on dispose du job_doc avec un _id, on l'utilise en priorité
        if job_doc and job_doc.get("_id") is not None:
            filter_query["_id"] = job_doc["_id"]
        else:
            # Essayer ObjectId
            try:
                oid = ObjectId(job_id)
                filter_query["_id"] = oid
            except Exception:
                # Fallback sur job_id
                filter_query["job_id"] = job_id

        safe_fields = self._to_mongo_safe(fields)
        await self.collection.update_one(filter_query, {"$set": safe_fields})

    def _get_backoff_delay(self, attempt: int) -> int:
        """
        Retourne le délai de backoff pour une tentative donnée.

        Args:
            attempt: Numéro de tentative (>= 1)

        Returns:
            Délai en secondes.
        """
        index = attempt - 1
        if index < 0:
            index = 0
        if index < len(self.backoff_seconds):
            return self.backoff_seconds[index]
        return self.backoff_seconds[-1]

    @staticmethod
    def _to_mongo_safe(value: Any) -> Any:
        """
        Convertit une valeur dans un format compatible MongoDB.

        Règles :
        - Enum -> Enum.value
        - BaseModel -> model_dump()
        - dict/list/tuple/set -> conversion récursive
        - datetime naive -> datetime en UTC
        - Exception -> str(message)
        - Autres types simples -> inchangés
        """

        # Enum
        try:
            from enum import Enum

            if isinstance(value, Enum):
                return value.value
        except Exception:
            pass

        # Pydantic BaseModel
        if isinstance(value, BaseModel):
            return SchedulerService._to_mongo_safe(value.model_dump())

        # dict
        if isinstance(value, dict):
            return {
                str(k): SchedulerService._to_mongo_safe(v) for k, v in value.items()
            }

        # list / tuple / set
        if isinstance(value, (list, tuple, set)):
            return [SchedulerService._to_mongo_safe(v) for v in value]

        # datetime
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value

        # Exception
        if isinstance(value, Exception):
            return str(value)

        return value

    @staticmethod
    def _extract_platforms_from_job(job: Dict[str, Any]) -> List[str]:
        """
        Extrait la liste des plateformes visées par un job à partir du payload
        ou de champs legacy.

        - Si payload.targets existe : utilise targets[].platform.
        - Sinon, si job["platform"] existe (legacy) : retourne [platform].
        - Sinon : liste vide.
        """
        platforms: List[str] = []

        payload = job.get("payload") or {}
        if isinstance(payload, dict):
            targets = payload.get("targets") or []
            for t in targets:
                if isinstance(t, dict):
                    platform = t.get("platform")
                    if platform:
                        platforms.append(platform)

        if not platforms and job.get("platform"):
            platforms.append(job["platform"])

        return platforms
