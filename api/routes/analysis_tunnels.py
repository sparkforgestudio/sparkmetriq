from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from api.core.auths import get_current_user
from api.schemas.users import UserResponse
from services.analytics.tunnels import get_dynamic_tunnel_overview

router = APIRouter()

# Définition des seuils attendus pour la génération de recommandations
THRESHOLDS = {
    "source": 60.0,         # taux de conversion minimum attendu pour la phase "source"
    "intermediate": 50.0,   # taux de conversion minimum attendu pour la phase "intermediate"
    # Vous pouvez ajouter d’autres seuils pour "closing" ou d’autres étapes si nécessaire.
}

@router.get("/analysis/tunnels", response_model=List[Dict[str, Any]])
async def analysis_tunnels(
    agency_id: Optional[str] = Query(None, description="Identifiant de l'agence"),
    muse_id: Optional[str] = Query(None, description="Identifiant de la muse"),
    days: int = Query(30, description="Plage de jours pour l'analyse"),
    granularity: str = Query("daily", description="Granularité d'agrégation (daily, weekly, monthly)"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Retourne l'analyse dynamique du tunnel de vente avec recommandations par muse.
    
    L'endpoint interroge le service d'analytics qui utilise le champ dynamique 'funnel_stage'
    et regroupe les logs par date (selon la granularité) ainsi que par étape. Les résultats sont 
    ensuite organisés par muse et des recommandations métier sont générées en fonction de seuils prédéfinis.
    """
    # Définir la période d'analyse
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Appeler le service pour récupérer l'agrégation dynamique des logs
    aggregated_data = await get_dynamic_tunnel_overview(
        agency_id=agency_id,
        muse_id=muse_id,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity
    )

    # Organiser les données par muse
    result_by_muse: Dict[str, Dict[str, Any]] = {}
    for record in aggregated_data:
        # Supposons que vos logs contiennent bien le champ "muse_id"
        muse = record.get("muse_id") or "N/A"
        if muse not in result_by_muse:
            result_by_muse[muse] = {
                "muse_id": muse,
                "funnel": [],
                "recommendations": []
            }
        result_by_muse[muse]["funnel"].append({
            "stage": record.get("funnel_stage", "non spécifié"),
            "date": record.get("date"),
            "posts": record.get("posts", 0),
            "conversions": record.get("conversions", 0),
            "conversion_rate": record.get("conversion_rate", 0.0)
        })

    # Générer les recommandations pour chaque muse en comparant les taux obtenus aux seuils
    analyses: List[Dict[str, Any]] = []
    for muse, data in result_by_muse.items():
        recommendations: List[str] = []
        for stage_data in data["funnel"]:
            stage = stage_data["stage"]
            conversion_rate = stage_data["conversion_rate"]
            if stage in THRESHOLDS and conversion_rate < THRESHOLDS[stage]:
                if stage == "source":
                    recommendations.append(
                        "Améliorer la qualité des contenus de la phase 'source' pour augmenter l'engagement initial."
                    )
                elif stage == "intermediate":
                    recommendations.append(
                        "Optimiser la transition entre la phase 'intermediate' et le closing pour améliorer les conversions."
                    )
                # Vous pouvez ajouter des recommandations spécifiques pour d'autres étapes
        if not recommendations:
            recommendations.append("Tunnel de vente performant, continuez la stratégie actuelle.")
        data["recommendations"] = recommendations
        analyses.append(data)

    return analyses
