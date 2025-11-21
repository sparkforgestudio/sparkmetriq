# api/services/calendar/service.py
"""
Service Calendar pour la gestion des posts programmés.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from bson import ObjectId

from api.databases.databases import get_core_db
from api.schemas.calendar import (
    ScheduledPostIn, RescheduleIn, DuplicateIn, ScheduledPostOut
)

logger = logging.getLogger(__name__)

# Import du hub WS (lazy import pour éviter les dépendances circulaires)
_hub = None


def _get_hub():
    """Récupère le hub WebSocket (lazy import)."""
    global _hub
    if _hub is None:
        from api.services.calendar.ws_hub import hub
        _hub = hub
    return _hub


class PlatformRules:
    """Règles de validation par plateforme."""
    
    # Longueurs max de caption par plateforme
    MAX_CAPTION_LENGTH = {
        "instagram": 2200,
        "tiktok": 2200,
        "x": 280,
        "reddit": 40000,
        "telegram": 4096,
        "onlyfans": 1000
    }
    
    @staticmethod
    def validate(platform: str, payload: Dict[str, Any]) -> None:
        """
        Valide les contraintes spécifiques à une plateforme.
        
        Args:
            platform: Plateforme cible
            payload: Données du post
            
        Raises:
            ValueError: Si les contraintes ne sont pas respectées
        """
        content_ref = payload.get("content_ref", {})
        text = content_ref.get("text", "") if isinstance(content_ref, dict) else ""
        
        max_length = PlatformRules.MAX_CAPTION_LENGTH.get(platform, 1000)
        
        if text and len(text) > max_length:
            raise ValueError(
                f"Caption too long for {platform}: {len(text)} > {max_length} characters"
            )
        
        # Autres validations spécifiques peuvent être ajoutées ici
        # (ratio média, hashtags, etc.)
        logger.debug(f"Platform validation passed for {platform}")


class CalendarService:
    """Service de gestion du calendrier."""
    
    async def query_calendar(self, q: Dict[str, Any]) -> Dict[str, Any]:
        """
        Requête les posts du calendrier selon les filtres.
        
        Args:
            q: Paramètres de requête
            
        Returns:
            Dictionnaire avec items et next_page
        """
        db = get_core_db()
        
        # Construire le filtre MongoDB
        filt = {
            "org_id": q["org_id"],
            "schedule.start_at_utc": {
                "$gte": q["from_utc"],
                "$lte": q["to_utc"]
            }
        }
        
        # Appliquer les filtres optionnels
        if q.get("muse_ids"):
            filt["muse_id"] = {"$in": q["muse_ids"]}
        
        if q.get("platforms"):
            filt["platform"] = {"$in": q["platforms"]}
        
        if q.get("statuses"):
            filt["status"] = {"$in": q["statuses"]}
        
        if q.get("labels"):
            filt["labels"] = {"$in": q["labels"]}
        
        # Filtre par catégorie (si category_id fourni, mapper vers muses)
        if q.get("category_id"):
            # TODO: Implémenter le mapping catégorie -> muses si nécessaire
            # Pour l'instant, on filtre directement sur category
            filt["category"] = q["category_id"]
        
        # Pagination
        skip = (q["page"] - 1) * q["limit"]
        
        # Projection pour optimiser la requête
        projection = {
            "_id": 1,
            "org_id": 1,
            "muse_id": 1,
            "platform": 1,
            "status": 1,
            "labels": 1,
            "category": 1,
            "schedule": 1,
            "content_ref.text": 1,
            "content_ref.media_ids": 1
        }
        
        # Exécuter la requête
        cursor = (
            db["scheduled_posts"]
            .find(filt, projection=projection)
            .sort("schedule.start_at_utc", 1)
            .skip(skip)
            .limit(q["limit"] + 1)  # +1 pour détecter s'il y a une page suivante
        )
        
        rows = await cursor.to_list(length=q["limit"] + 1)
        
        # Détecter s'il y a une page suivante
        has_next = len(rows) > q["limit"]
        if has_next:
            rows = rows[:q["limit"]]
        
        # Transformer les résultats
        items: List[Dict[str, Any]] = []
        for r in rows:
            schedule = r.get("schedule", {})
            content_ref = r.get("content_ref", {}) or {}
            text = content_ref.get("text", "")
            
            items.append({
                "id": str(r["_id"]),
                "org_id": r["org_id"],
                "muse_id": r["muse_id"],
                "platform": r["platform"],
                "status": r["status"],
                "title": text[:64] if text else None,
                "start_at_utc": schedule.get("start_at_utc"),
                "end_at_utc": schedule.get("end_at_utc"),
                "tz": schedule.get("tz"),
                "labels": r.get("labels", []),
                "category": r.get("category"),
                "media_preview_url": None  # TODO: Générer URL presignée si stocké
            })
        
        return {
            "items": items,
            "next_page": q["page"] + 1 if has_next else None,
            "count": len(items)
        }
    
    async def create(self, payload: ScheduledPostIn) -> str:
        """
        Crée un nouveau post programmé.
        
        Args:
            payload: Données du post
            
        Returns:
            ID du post créé
        """
        db = get_core_db()
        
        doc = payload.model_dump()
        
        # Valider les contraintes de plateforme
        PlatformRules.validate(doc["platform"], doc)
        
        # Ajouter les métadonnées d'audit
        doc["audit"] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = await db["scheduled_posts"].insert_one(doc)
        post_id = str(result.inserted_id)
        
        logger.info(
            f"Created scheduled post: id={post_id}, org_id={doc['org_id']}, "
            f"muse_id={doc['muse_id']}, platform={doc['platform']}"
        )
        
        # Notifier via WS
        await self._notify_ws(
            doc["org_id"],
            "calendar.created",
            {"id": post_id}
        )
        
        return post_id
    
    async def update(self, post_id: str, org_id: str, patch: Dict[str, Any]) -> None:
        """
        Met à jour un post programmé.
        
        Args:
            post_id: ID du post
            org_id: ID de l'organisation (pour sécurité)
            patch: Champs à mettre à jour
        """
        db = get_core_db()
        
        # Sécurité: filtrer les champs modifiables
        allowed = {
            "content_ref", "schedule", "labels", "status",
            "constraints", "category", "visibility"
        }
        
        update = {k: v for k, v in patch.items() if k in allowed}
        
        # Si changement de plateforme, revalider
        if "platform" in patch:
            # Charger le post existant pour la validation complète
            existing = await db["scheduled_posts"].find_one({
                "_id": ObjectId(post_id),
                "org_id": org_id
            })
            
            if not existing:
                raise ValueError("Post not found")
            
            merged = {**existing, **update, "platform": patch["platform"]}
            PlatformRules.validate(patch["platform"], merged)
            update["platform"] = patch["platform"]
        
        if not update:
            logger.warning(f"No valid fields to update for post_id={post_id}")
            return
        
        # Ajouter timestamp de mise à jour
        update["audit.updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db["scheduled_posts"].update_one(
            {"_id": ObjectId(post_id), "org_id": org_id},
            {"$set": update}
        )
        
        if result.matched_count == 0:
            raise ValueError("Post not found")
        
        logger.info(f"Updated scheduled post: id={post_id}")
        
        # Notifier via WS
        await self._notify_ws(org_id, "calendar.updated", {"id": post_id})
    
    async def reschedule(self, body: RescheduleIn, org_id: str) -> None:
        """
        Reprogramme un post.
        
        Args:
            body: Données de reprogrammation
            org_id: ID de l'organisation (pour sécurité)
        """
        db = get_core_db()
        
        post = await db["scheduled_posts"].find_one({
            "_id": ObjectId(body.id),
            "org_id": org_id
        })
        
        if not post:
            raise ValueError("Post not found")
        
        new_tz = body.new_tz or post["schedule"]["tz"]
        
        # TODO: Vérifier les conflits/limitations (ex: pas de posts trop proches)
        
        await db["scheduled_posts"].update_one(
            {"_id": ObjectId(body.id)},
            {
                "$set": {
                    "schedule.start_at_utc": body.new_start_at_utc,
                    "schedule.tz": new_tz,
                    "audit.updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        logger.info(
            f"Rescheduled post: id={body.id}, new_start_at_utc={body.new_start_at_utc}"
        )
        
        # Notifier via WS
        await self._notify_ws(
            org_id,
            "calendar.rescheduled",
            {
                "id": body.id,
                "new_start_at_utc": body.new_start_at_utc,
                "tz": new_tz
            }
        )
    
    async def duplicate(self, body: DuplicateIn, org_id: str) -> List[str]:
        """
        Duplique un post sur une ou plusieurs plateformes.
        
        Args:
            body: Données de duplication
            org_id: ID de l'organisation (pour sécurité)
            
        Returns:
            Liste des IDs des nouveaux posts créés
        """
        db = get_core_db()
        
        src = await db["scheduled_posts"].find_one({
            "_id": ObjectId(body.id),
            "org_id": org_id
        })
        
        if not src:
            raise ValueError("Post not found")
        
        targets = body.target_platforms or [src["platform"]]
        new_ids = []
        
        for pf in targets:
            doc = dict(src)
            doc.pop("_id", None)
            doc["platform"] = pf
            doc["schedule"]["start_at_utc"] = body.target_start_at_utc
            doc["schedule"]["tz"] = body.tz
            doc["status"] = "scheduled"
            
            # Si variation IA demandée, modifier le contenu
            if body.with_ai_variation:
                # TODO: Appeler service IA pour varier le texte/hashtags
                content_ref = doc.get("content_ref", {}) or {}
                if content_ref.get("text"):
                    # Pour MVP, on peut simplement ajouter un suffixe
                    content_ref["text"] = content_ref["text"] + " [Variation]"
                    doc["content_ref"] = content_ref
            
            # Réinitialiser l'audit
            doc["audit"] = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = await db["scheduled_posts"].insert_one(doc)
            new_ids.append(str(result.inserted_id))
        
        logger.info(
            f"Duplicated post: source_id={body.id}, new_ids={new_ids}, "
            f"platforms={targets}"
        )
        
        # Notifier via WS
        await self._notify_ws(
            org_id,
            "calendar.duplicated",
            {"source": body.id, "ids": new_ids}
        )
        
        return new_ids
    
    async def _notify_ws(self, org_id: str, event: str, payload: Dict[str, Any]) -> None:
        """
        Notifie les clients WebSocket d'un événement.
        
        Args:
            org_id: ID de l'organisation
            event: Type d'événement
            payload: Données de l'événement
        """
        try:
            hub = _get_hub()
            await hub.broadcast(org_id, event, payload)
        except Exception as e:
            logger.warning(f"Error broadcasting WS event: {e}")
