# api/services/scheduler/abtest_service.py
"""
Service de tests A/B pour le contenu.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId
from api.databases.databases import db
from api.schemas.scheduler import ABTestCreate, DraftIn
from api.services.scheduler.planner_service import create_draft

async def create_ab_test(tenant_id: str, payload: ABTestCreate) -> Dict[str, Any]:
    """Crée un test A/B avec deux variantes."""
    assert len(payload.variants) == 2, "A/B requires exactly 2 variants"
    
    now = datetime.now(timezone.utc)
    doc = {
        "tenant_id": tenant_id,
        "campaign_id": payload.campaign_id,
        "platform": payload.platform,
        "muse_id": payload.muse_id,
        "hypothesis": payload.hypothesis,
        "kpi": payload.kpi,
        "start_at": payload.start_at,
        "end_at": payload.end_at,
        "created_at": now,
        "updated_at": now,
        "status": "scheduled",
        "variants": {
            "A": payload.variants[0].model_dump(),
            "B": payload.variants[1].model_dump()
        }
    }
    
    r = await db["ab_tests"].insert_one(doc)
    test_id = str(r.inserted_id)

    # Créer 2 drafts rattachés à la campagne
    draft_ids = []
    for i, var in enumerate(payload.variants):
        variant = "A" if i == 0 else "B"
        di = DraftIn(**{
            **var.model_dump(), 
            "ab_test_campaign_id": payload.campaign_id, 
            "variant": variant
        })
        draft_id = await create_draft(tenant_id, di)
        draft_ids.append(draft_id)

    return {"id": test_id, "draft_ids": draft_ids}

async def get_ab_test(tenant_id: str, campaign_id: str) -> Optional[Dict[str, Any]]:
    """Récupère un test A/B par campaign_id."""
    return await db["ab_tests"].find_one({
        "tenant_id": tenant_id,
        "campaign_id": campaign_id
    })

async def list_ab_tests(tenant_id: str, muse_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Liste les tests A/B."""
    query = {"tenant_id": tenant_id}
    if muse_id:
        query["muse_id"] = muse_id
    if status:
        query["status"] = status
    
    cursor = db["ab_tests"].find(query).sort("created_at", -1)
    return await cursor.to_list(None)

async def summarize_ab_test(tenant_id: str, campaign_id: str) -> Dict[str, Any]:
    """Résume les résultats d'un test A/B."""
    test = await get_ab_test(tenant_id, campaign_id)
    if not test:
        return {"error": "Test not found"}
    
    # Récupérer les logs de publication pour les deux variantes
    variant_a_logs = await db["publish_logs"].find({
        "tenant_id": tenant_id,
        "platform": test["platform"],
        "muse_id": test["muse_id"],
        "status": "published"
    }).to_list(None)
    
    # Filtrer par variante (via les drafts)
    variant_a_metrics = []
    variant_b_metrics = []
    
    for log in variant_a_logs:
        draft_id = log.get("draft_id")
        if draft_id:
            draft = await db["scheduled_drafts"].find_one({"_id": ObjectId(draft_id)})
            if draft and draft.get("ab_test_campaign_id") == campaign_id:
                variant = draft.get("variant")
                metrics = log.get("connector_result", {}).get("metrics", {})
                
                if variant == "A":
                    variant_a_metrics.append(metrics)
                elif variant == "B":
                    variant_b_metrics.append(metrics)
    
    # Calculer les moyennes
    def avg_metric(metrics_list, metric_name):
        if not metrics_list:
            return 0.0
        values = [float(m.get(metric_name, 0)) for m in metrics_list]
        return sum(values) / len(values)
    
    kpi = test["kpi"]
    
    variant_a_avg = avg_metric(variant_a_metrics, kpi)
    variant_b_avg = avg_metric(variant_b_metrics, kpi)
    
    # Déterminer le gagnant
    winner = "A" if variant_a_avg > variant_b_avg else "B" if variant_b_avg > variant_a_avg else "Tie"
    
    # Calculer l'amélioration
    improvement = 0.0
    if variant_a_avg > 0:
        improvement = ((variant_b_avg - variant_a_avg) / variant_a_avg) * 100
    
    return {
        "campaign_id": campaign_id,
        "platform": test["platform"],
        "kpi": kpi,
        "hypothesis": test["hypothesis"],
        "variant_a": {
            "avg_performance": variant_a_avg,
            "sample_size": len(variant_a_metrics)
        },
        "variant_b": {
            "avg_performance": variant_b_avg,
            "sample_size": len(variant_b_metrics)
        },
        "winner": winner,
        "improvement_percent": improvement,
        "status": test["status"],
        "start_at": test["start_at"],
        "end_at": test["end_at"]
    }

async def update_ab_test_status(tenant_id: str, campaign_id: str, status: str) -> bool:
    """Met à jour le statut d'un test A/B."""
    valid_statuses = ["scheduled", "running", "completed", "cancelled"]
    if status not in valid_statuses:
        return False
    
    result = await db["ab_tests"].update_one(
        {"tenant_id": tenant_id, "campaign_id": campaign_id},
        {"$set": {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return result.modified_count == 1

async def get_ab_test_recommendations(tenant_id: str, muse_id: str, platform: str) -> List[Dict[str, Any]]:
    """Génère des recommandations pour les tests A/B."""
    # Analyser l'historique des tests A/B
    past_tests = await db["ab_tests"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "platform": platform,
        "status": "completed"
    }).to_list(None)
    
    recommendations = []
    
    # Recommandations basées sur les patterns
    if not past_tests:
        recommendations.append({
            "type": "first_test",
            "title": "Premier test A/B",
            "description": "Commencez par tester différents titres pour vos posts",
            "suggestion": "Testez 'Titre émotionnel' vs 'Titre factuel'"
        })
    else:
        # Analyser les KPIs les plus testés
        kpi_counts = {}
        for test in past_tests:
            kpi = test.get("kpi", "engagement")
            kpi_counts[kpi] = kpi_counts.get(kpi, 0) + 1
        
        # Recommandation basée sur les KPIs moins testés
        if kpi_counts.get("click", 0) < kpi_counts.get("engagement", 0):
            recommendations.append({
                "type": "kpi_expansion",
                "title": "Testez le CTR",
                "description": "Vous avez beaucoup testé l'engagement, essayez le CTR",
                "suggestion": "Testez différents call-to-action"
            })
    
    # Recommandations génériques
    recommendations.extend([
        {
            "type": "timing",
            "title": "Testez les heures de publication",
            "description": "Comparez les performances à différentes heures",
            "suggestion": "Matin vs Soir"
        },
        {
            "type": "content_format",
            "title": "Testez les formats",
            "description": "Comparez différents types de contenu",
            "suggestion": "Image vs Vidéo vs Carousel"
        }
    ])
    
    return recommendations[:5]  # Limiter à 5 recommandations

async def create_ab_test_from_recommendation(tenant_id: str, muse_id: str, platform: str, recommendation_type: str) -> Dict[str, Any]:
    """Crée un test A/B basé sur une recommandation."""
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    start_at = now + timedelta(hours=1)
    end_at = start_at + timedelta(days=7)
    
    if recommendation_type == "first_test":
        variants = [
            DraftIn(
                platform=platform,
                muse_id=muse_id,
                title="Titre émotionnel",
                caption="🔥 Découvrez mon nouveau contenu exclusif ! #exclusive #teaser",
                scheduled_at=start_at,
                tone="flirty",
                objective="conversion"
            ),
            DraftIn(
                platform=platform,
                muse_id=muse_id,
                title="Titre factuel",
                caption="Nouveau contenu disponible maintenant. Lien en bio. #content #new",
                scheduled_at=start_at + timedelta(hours=2),
                tone="professional",
                objective="conversion"
            )
        ]
    elif recommendation_type == "timing":
        variants = [
            DraftIn(
                platform=platform,
                muse_id=muse_id,
                title="Publication matin",
                caption="Bonjour ! Nouveau contenu pour commencer la journée 🌅 #morning #content",
                scheduled_at=start_at.replace(hour=9),
                tone="energetic",
                objective="engagement"
            ),
            DraftIn(
                platform=platform,
                muse_id=muse_id,
                title="Publication soir",
                caption="Bonsoir ! Contenu exclusif pour finir la journée 🌙 #evening #exclusive",
                scheduled_at=start_at.replace(hour=20),
                tone="intimate",
                objective="engagement"
            )
        ]
    else:
        # Format par défaut
        variants = [
            DraftIn(
                platform=platform,
                muse_id=muse_id,
                title="Format A",
                caption="Contenu test A - Version originale",
                scheduled_at=start_at,
                tone="flirty",
                objective="engagement"
            ),
            DraftIn(
                platform=platform,
                muse_id=muse_id,
                title="Format B",
                caption="Contenu test B - Version alternative",
                scheduled_at=start_at + timedelta(hours=2),
                tone="flirty",
                objective="engagement"
            )
        ]
    
    payload = ABTestCreate(
        campaign_id=f"auto_{recommendation_type}_{int(now.timestamp())}",
        platform=platform,
        muse_id=muse_id,
        hypothesis=f"Test automatique basé sur: {recommendation_type}",
        kpi="engagement",
        start_at=start_at,
        end_at=end_at,
        variants=variants
    )
    
    return await create_ab_test(tenant_id, payload)
