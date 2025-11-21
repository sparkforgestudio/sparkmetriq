# api/services/bi/insight_engine.py
"""
Service InsightEngine pour l'Assistant Stratégique IA.
Gère les alertes, détections et candidats collaboration.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from api.databases.databases import get_bi_db

logger = logging.getLogger(__name__)


class InsightEngine:
    """Moteur d'insights stratégiques pour l'Assistant IA.
    
    Responsabilités:
        - Enregistrer et lister les alertes stratégiques
        - Détecter des anomalies (baisse de portée, etc.)
        - Proposer des candidats pour collaboration
        
    Notes:
        - Toutes les opérations sont multi-tenant (org_id obligatoire)
        - Les méthodes de détection sont des stubs MVP à remplacer par des algorithmes ML
    """
    
    def __init__(self, bi_db=None):
        """Initialise le moteur d'insights.
        
        Args:
            bi_db: Base de données BI (optionnel, utilise get_bi_db() si None).
        """
        self.bi_db = bi_db or get_bi_db()
    
    async def record_alert(self, payload: Dict[str, Any]) -> str:
        """
        Enregistre une alerte insight.
        
        Args:
            payload: Données de l'alerte
            
        Returns:
            ID de l'alerte créée
        """
        doc = dict(payload)
        doc["created_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.bi_db["insights_alerts"].insert_one(doc)
        alert_id = str(result.inserted_id)
        
        logger.info(
            f"Insight alert recorded: id={alert_id}, org_id={payload.get('org_id')}, "
            f"type={payload.get('type')}, severity={payload.get('severity')}"
        )
        
        return alert_id
    
    async def list_alerts(self, q: Dict[str, Any]) -> Dict[str, Any]:
        """
        Liste les alertes selon les filtres.
        
        Args:
            q: Paramètres de requête
            
        Returns:
            Dictionnaire avec items et next_page
        """
        # Construire le filtre
        filt = {"org_id": q["org_id"]}
        
        if q.get("muse_id"):
            filt["muse_id"] = q["muse_id"]
        
        if q.get("types"):
            filt["type"] = {"$in": q["types"]}
        
        if q.get("severity"):
            filt["severity"] = {"$in": q["severity"]}
        
        if q.get("from_utc") and q.get("to_utc"):
            filt["created_at"] = {
                "$gte": q["from_utc"],
                "$lte": q["to_utc"]
            }
        
        # Pagination
        skip = (q["page"] - 1) * q["limit"]
        
        cursor = (
            self.bi_db["insights_alerts"]
            .find(filt)
            .sort("created_at", -1)
            .skip(skip)
            .limit(q["limit"] + 1)  # +1 pour détecter page suivante
        )
        
        rows = await cursor.to_list(length=q["limit"] + 1)
        
        # Détecter s'il y a une page suivante
        has_next = len(rows) > q["limit"]
        if has_next:
            rows = rows[:q["limit"]]
        
        # Convertir _id en string
        for r in rows:
            r["id"] = str(r.pop("_id"))
        
        return {
            "items": rows,
            "next_page": q["page"] + 1 if has_next else None,
            "count": len(rows)
        }
    
    async def detect_reach_drop(
        self,
        org_id: str,
        muse_id: str,
        platform: str,
        window_days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        Détecte une baisse de portée (reach).
        
        MVP: placeholder; à remplacer par un vrai calcul (z-score/Prophet)
        sur agg_creator_stats_daily.
        
        Args:
            org_id: ID de l'organisation
            muse_id: ID de la muse
            platform: Plateforme
            window_days: Fenêtre d'analyse en jours
            
        Returns:
            Alerte de baisse si détectée, None sinon
        """
        # TODO: Implémenter avec calcul réel sur agg_creator_stats_daily
        # Exemple: comparer moyenne des 7 derniers jours vs moyenne précédente
        # Si baisse > seuil (ex: -20%), créer une alerte
        
        logger.debug(
            f"Reach drop detection: org_id={org_id}, muse_id={muse_id}, "
            f"platform={platform}, window={window_days}d"
        )
        
        # Stub pour MVP
        return None
    
    async def collab_candidates(
        self,
        org_id: str,
        muse_id: str,
        min_score: float,
        page: int,
        limit: int
    ) -> Dict[str, Any]:
        """
        Liste les candidats pour collaboration.
        
        Args:
            org_id: ID de l'organisation
            muse_id: ID de la muse
            min_score: Score minimum requis
            page: Numéro de page
            limit: Nombre d'éléments par page
            
        Returns:
            Dictionnaire avec items et next_page
        """
        filt = {
            "org_id": org_id,
            "muse_id": muse_id,
            "similarity_score": {"$gte": min_score}
        }
        
        skip = (page - 1) * limit
        
        cursor = (
            self.bi_db["collab_candidates"]
            .find(filt)
            .sort("similarity_score", -1)
            .skip(skip)
            .limit(limit + 1)  # +1 pour détecter page suivante
        )
        
        rows = await cursor.to_list(length=limit + 1)
        
        # Détecter s'il y a une page suivante
        has_next = len(rows) > limit
        if has_next:
            rows = rows[:limit]
        
        # Convertir _id en string
        for r in rows:
            r["id"] = str(r.pop("_id"))
        
        logger.debug(
            f"Collab candidates: org_id={org_id}, muse_id={muse_id}, "
            f"found={len(rows)}, min_score={min_score}"
        )
        
        return {
            "items": rows,
            "next_page": page + 1 if has_next else None,
            "count": len(rows)
        }

