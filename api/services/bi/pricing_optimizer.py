# api/services/bi/pricing_optimizer.py
"""
Service PricingOptimizer pour l'Assistant Pricing IA.
Optimise les prix PPV/subscriptions/bundles via ML ou heuristiques.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timezone

from api.databases.databases import get_bi_db

logger = logging.getLogger(__name__)


class PricingOptimizerService:
    """Service d'optimisation de prix (MVP heuristique, évolutif ML).
    
    Responsabilités:
        - Calculer une recommandation de prix à partir de features business
        - Persister la recommandation dans musai_bi.pricing_recommendations
        
    Notes:
        - Le moteur ML pourra remplacer `_estimated_conversion` et l'heuristique de pricing.
        - Toutes les écritures sont multi-tenant (org_id obligatoire).
        - MVP utilise une heuristique simple basée sur le taux de conversion estimé.
    """
    
    def __init__(self, bi_db=None):
        """Initialise le service d'optimisation.
        
        Args:
            bi_db: Base de données BI (optionnel, utilise get_bi_db() si None).
        """
        self.bi_db = bi_db or get_bi_db()
    
    async def recommend_price(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Recommande un prix optimisé basé sur l'analyse du marché et des performances.
        
        MVP: Utilise une heuristique simple (ajustement selon taux de conversion estimé).
        À remplacer par un modèle ML basé sur l'élasticité de la demande et l'analyse
        des performances historiques.
        
        Args:
            payload: Données de l'item (org_id, muse_id, item_type, item_ref,
                current_price_usd, features).
            
        Returns:
            Dict contenant la recommandation complète : recommended_price_usd,
            confidence (0.0-1.0), predicted_revenue_gain_pct, basis (modèle utilisé),
            generated_at (ISO), id (ID MongoDB).
        """
        current = payload["current_price_usd"]
        org_id = payload["org_id"]
        muse_id = payload["muse_id"]
        item_ref = payload["item_ref"]
        item_type = payload["item_type"]
        
        # Estimer le taux de conversion actuel
        conv_rate = await self._estimated_conversion(payload)
        
        # Heuristique simple: ajuster le prix selon le taux de conversion
        # Si conversion faible (< 5%), baisser le prix
        # Si conversion élevée (> 15%), augmenter le prix
        if conv_rate < 0.05:
            factor = -0.1  # Baisse de 10%
        elif conv_rate > 0.15:
            factor = 0.1  # Hausse de 10%
        else:
            factor = 0.0  # Pas de changement
        
        # Calculer le prix recommandé
        recommended = round(max(1.0, current * (1.0 + factor)), 2)
        
        # Calculer le gain de revenus prédit (simplifié)
        predicted_gain_pct = 12.3 if factor < 0 else (4.1 if factor > 0 else 0.0)
        
        # Construire la sortie
        out = dict(payload)
        out["recommended_price_usd"] = recommended
        out["confidence"] = 0.65  # MVP: confiance fixe
        out["predicted_revenue_gain_pct"] = predicted_gain_pct
        out["basis"] = "elasticity_heuristic_v0"
        out["generated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Sauvegarder la recommandation
        result = await self.bi_db["pricing_recommendations"].insert_one(out)
        out["id"] = str(result.inserted_id)
        
        logger.info(
            f"Pricing recommendation: org_id={org_id}, muse_id={muse_id}, "
            f"item_ref={item_ref}, current={current}, recommended={recommended}, "
            f"confidence={out['confidence']}"
        )
        
        return out
    
    async def _estimated_conversion(self, payload: Dict[str, Any]) -> float:
        """Estime le taux de conversion actuel d'un item.
        
        TODO: Calculer via agg_ppv_performance_daily/sales_transactions
        selon org_id/muse_id/item_ref. Pour MVP, retourne une valeur fixe.
        
        Args:
            payload: Données de l'item (org_id, muse_id, item_ref, item_type).
            
        Returns:
            Taux de conversion estimé (0.0-1.0). MVP: retourne 0.08 (8%).
        """
        org_id = payload["org_id"]
        muse_id = payload["muse_id"]
        item_ref = payload["item_ref"]
        item_type = payload["item_type"]
        
        # TODO: Implémenter avec vraie requête BI
        # Exemple:
        # - Récupérer les stats de performance depuis agg_ppv_performance_daily
        # - Calculer: conversion_rate = clicks / impressions
        # - Ou depuis sales_transactions: conversion = sales / views
        
        logger.debug(
            f"Estimated conversion: org_id={org_id}, muse_id={muse_id}, "
            f"item_ref={item_ref}, item_type={item_type}"
        )
        
        # MVP: retourner une valeur fixe simulée
        return 0.08  # 8% de conversion

