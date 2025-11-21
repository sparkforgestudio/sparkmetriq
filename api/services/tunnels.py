# api/services/tunnels.py
from typing import List
from api.schemas.tunnel_analysis import TunnelAnalysisResponse

async def analyze_tunnel(days: int, granularity: str) -> List[TunnelAnalysisResponse]:
    """
    Calcule les stats du tunnel et génère des recommandations.
    Pour l'instant stub : retourne une liste vide, à implémenter plus tard.
    """
    # TODO: remplacer par la vraie logique d'analyse / requêtes en base
    return []
