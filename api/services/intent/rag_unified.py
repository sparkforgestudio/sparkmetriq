# api/services/intent/rag_unified.py
"""
RAG unifié pour le Moteur d'Intentions.
Retourne des passages pertinents depuis diverses sources de connaissance.
"""

import logging
from typing import List, Dict, Any
from api.databases.databases import get_core_db

logger = logging.getLogger(__name__)


class UnifiedRetriever:
    """
    RAG unifié : retourne des passages courts pertinents depuis :
    - dm_history, captions, prompt_history, brand_doc
    avec boosting branding (poids supérieur).
    
    NOTE: Version simplifiée avec scoring heuristique.
    Pour production, remplacer par vector search (embeddings).
    """
    
    def __init__(self, booster_weight: float = 2.0):
        """
        Initialise le retriever.
        
        Args:
            booster_weight: Multiplicateur de poids pour brand_doc
        """
        self.booster_weight = booster_weight
    
    async def retrieve(
        self,
        org_id: str,
        muse_id: str,
        query: str,
        k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Récupère les chunks de connaissance pertinents.
        
        Args:
            org_id: ID de l'organisation
            muse_id: ID de la muse
            query: Requête de recherche (texte du message)
            k: Nombre de résultats à retourner
            
        Returns:
            Liste de dictionnaires avec text, kind, weight
        """
        db = get_core_db()
        
        try:
            # Récupérer tous les chunks pour cette muse
            cursor = (
                db["knowledge_chunks"]
                .find({"org_id": org_id, "muse_id": muse_id})
                .sort("ts", -1)  # Plus récents en premier
                .limit(256)  # Limite pour éviter de tout charger
            )
            rows = await cursor.to_list(length=256)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des chunks: {e}")
            return []
        
        if not rows:
            logger.debug(f"Aucun chunk trouvé pour org_id={org_id}, muse_id={muse_id}")
            return []
        
        # Scoring heuristique
        scored = []
        query_lower = query.lower() if query else ""
        query_tokens = set(query_lower.split()) if query_lower else set()
        
        for r in rows:
            base_weight = r.get("weight", 1.0)
            text = r.get("text", "").lower()
            kind = r.get("kind", "")
            
            # Booster pour brand_doc
            if kind == "brand_doc":
                base_weight *= self.booster_weight
            
            # Scoring basé sur la présence de tokens
            score = base_weight
            if query_tokens:
                matches = sum(1 for token in query_tokens if token in text)
                if matches > 0:
                    score += 0.1 * matches
                    # Bonus si plusieurs tokens matchent
                    if matches >= 2:
                        score += 0.2
            
            # Bonus pour brand_doc même sans match direct
            if kind == "brand_doc" and not query_tokens:
                score += 0.5
            
            scored.append((score, r))
        
        # Trier par score décroissant
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Retourner les k meilleurs
        results = []
        for score, r in scored[:k]:
            results.append({
                "text": r.get("text", ""),
                "kind": r.get("kind", ""),
                "weight": r.get("weight", 1.0),
                "score": score
            })
        
        logger.debug(
            f"Retrieved {len(results)} chunks for org_id={org_id}, "
            f"muse_id={muse_id}, query_length={len(query)}"
        )
        
        return results




