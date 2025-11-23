# api/services/assistant/trends_service.py
"""
Service de détection de tendances via RAG pour l'Assistant IA Stratégique.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from api.databases.databases import db

# Mock pour les services RAG existants (à adapter selon votre implémentation)
class MockVectorStore:
    @staticmethod
    async def semantic_search(query: str, top_k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Recherche sémantique simulée pour V1."""
        # Données simulées de tendances
        mock_trends = [
            {
                "source": "reddit",
                "title": "Elf cosplay POV trend explodes",
                "summary": "Elf cosplay POV content is gaining massive traction on Reddit with +380% growth in 5 days",
                "activation": "Create elf cosplay POV content with fantasy elements and mystical themes",
                "score": 0.95,
                "ts": datetime.now(timezone.utc),
                "niche": "cosplay"
            },
            {
                "source": "tiktok",
                "title": "Fitness motivation morning routine",
                "summary": "Morning fitness routines with motivational content are trending with high engagement",
                "activation": "Create morning workout content with motivational messaging and progress tracking",
                "score": 0.88,
                "ts": datetime.now(timezone.utc),
                "niche": "fitness"
            },
            {
                "source": "twitter",
                "title": "Behind the scenes content",
                "summary": "Behind the scenes content showing the creative process is performing well",
                "activation": "Share behind the scenes content of your content creation process",
                "score": 0.82,
                "ts": datetime.now(timezone.utc),
                "niche": "lifestyle"
            },
            {
                "source": "reddit",
                "title": "Interactive polls and Q&A",
                "summary": "Interactive content like polls and Q&A sessions are driving high engagement",
                "activation": "Create interactive polls and Q&A sessions to boost engagement",
                "score": 0.79,
                "ts": datetime.now(timezone.utc),
                "niche": "general"
            },
            {
                "source": "tiktok",
                "title": "Transformation content",
                "summary": "Before/after transformation content is trending with high shares and saves",
                "activation": "Create transformation content showing progress or changes",
                "score": 0.76,
                "ts": datetime.now(timezone.utc),
                "niche": "fitness"
            }
        ]
        
        # Filtrer selon les mots-clés de niche
        if filters and "source" in filters:
            sources = filters["source"].get("$in", [])
            mock_trends = [t for t in mock_trends if t["source"] in sources]
        
        # Simuler une recherche sémantique basée sur les mots-clés
        query_lower = query.lower()
        scored_trends = []
        
        for trend in mock_trends:
            score = 0.0
            trend_text = f"{trend['title']} {trend['summary']}".lower()
            
            # Score basé sur la correspondance des mots-clés
            keywords = query_lower.split()
            for keyword in keywords:
                if keyword in trend_text:
                    score += 0.2
            
            # Bonus pour les niches correspondantes
            if any(niche in trend_text for niche in ["cosplay", "fitness", "lifestyle"]):
                score += 0.1
            
            scored_trends.append({**trend, "score": max(score, trend["score"])})
        
        # Trier par score et retourner le top_k
        scored_trends.sort(key=lambda x: x["score"], reverse=True)
        return scored_trends[:top_k]

class MockDocStore:
    @staticmethod
    async def upsert_documents(documents: List[Dict[str, Any]]) -> bool:
        """Upsert de documents simulé."""
        # Pour V1, on simule juste le succès
        return True

# Instances mock
VectorStore = MockVectorStore()
DocStore = MockDocStore()

async def search_trends(tenant_id: str, niche_keywords: List[str], limit: int = 5) -> List[Dict[str, Any]]:
    """Recherche des tendances pertinentes pour un créateur."""
    # 1) requête sémantique multi-termes
    query = " ".join(niche_keywords[:6]) if niche_keywords else "onlyfans marketing trend"
    hits = await VectorStore.semantic_search(
        query=query, 
        top_k=20, 
        filters={"source": {"$in": ["reddit", "tiktok", "twitter"]}}
    )
    
    res = []
    for h in hits[:limit]:
        res.append({
            "source": h.get("source", "reddit"),
            "topic": h.get("title", ""),
            "summary": h.get("summary", ""),
            "activation_idea": h.get("activation", "Try a POV cosplay variation with CTA"),
            "score": float(h.get("score", 0.0)),
            "ts": h.get("ts", datetime.now(timezone.utc))
        })
    
    return res

async def cache_trends(tenant_id: str, trends: List[Dict[str, Any]]) -> bool:
    """Met en cache les tendances trouvées."""
    try:
        docs = []
        for trend in trends:
            doc = {
                "tenant_id": tenant_id,
                "source": trend["source"],
                "topic": trend["topic"],
                "summary": trend["summary"],
                "activation_idea": trend["activation_idea"],
                "score": trend["score"],
                "ts": trend["ts"],
                "cached_at": datetime.now(timezone.utc)
            }
            docs.append(doc)
        
        if docs:
            await db["trends_cache"].insert_many(docs)
        
        return True
    except Exception as e:
        print(f"Erreur lors de la mise en cache des tendances: {e}")
        return False

async def get_cached_trends(tenant_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Récupère les tendances mises en cache."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    cursor = db["trends_cache"].find({
        "tenant_id": tenant_id,
        "cached_at": {"$gte": cutoff}
    }).sort("score", -1)
    
    return await cursor.to_list(None)

async def ingest_external_trends():
    """Ingestion périodique des tendances externes (simulée pour V1)."""
    # Dans une version réelle, cela ferait appel à des APIs externes
    # ou des scrapers pour Reddit, TikTok, Twitter
    
    mock_external_data = [
        {
            "source": "reddit",
            "title": "New cosplay trend: Fantasy warrior",
            "text": "Fantasy warrior cosplay is trending with high engagement...",
            "url": "https://reddit.com/r/cosplay/example",
            "ts": datetime.now(timezone.utc),
            "niche": "cosplay"
        },
        {
            "source": "tiktok",
            "title": "Morning routine fitness content",
            "text": "Morning routine fitness content is performing well...",
            "url": "https://tiktok.com/@example",
            "ts": datetime.now(timezone.utc),
            "niche": "fitness"
        }
    ]
    
    # Simuler l'upsert dans le vector store
    await DocStore.upsert_documents(mock_external_data)
    
    return len(mock_external_data)

async def get_trend_insights(tenant_id: str, muse_id: str, niche_keywords: List[str]) -> Dict[str, Any]:
    """Génère des insights sur les tendances pour un créateur."""
    trends = await search_trends(tenant_id, niche_keywords, limit=10)
    
    if not trends:
        return {
            "insights": [],
            "recommendations": [],
            "trend_count": 0
        }
    
    # Analyser les tendances par source
    source_stats = {}
    for trend in trends:
        source = trend["source"]
        if source not in source_stats:
            source_stats[source] = {"count": 0, "avg_score": 0.0}
        source_stats[source]["count"] += 1
        source_stats[source]["avg_score"] += trend["score"]
    
    # Normaliser les scores moyens
    for source in source_stats:
        source_stats[source]["avg_score"] /= source_stats[source]["count"]
    
    # Générer des insights
    insights = []
    recommendations = []
    
    if trends:
        top_trend = trends[0]
        insights.append(f"Tendance principale: {top_trend['topic']} ({top_trend['source']})")
        recommendations.append(top_trend["activation_idea"])
    
    if source_stats:
        top_source = max(source_stats.items(), key=lambda x: x[1]["avg_score"])
        insights.append(f"Plateforme la plus prometteuse: {top_source[0]} (score moyen: {top_source[1]['avg_score']:.2f})")
    
    return {
        "insights": insights,
        "recommendations": recommendations,
        "trend_count": len(trends),
        "source_stats": source_stats,
        "top_trends": trends[:3]
    }




