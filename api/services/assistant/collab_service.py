# api/services/assistant/collab_service.py
"""
Service de suggestions de collaborations créateur IA.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
from api.databases.databases import db
from api.services.assistant.trends_service import VectorStore
from api.services.chat_omnichannel.deepseek_service import DeepSeekService

OUTREACH_PROMPT = """
Write a short friendly outreach DM (max 500 chars) to propose a cross-promo/collab between two adult-content creators.

Context:
- Both creators are in the adult content space (OnlyFans-like)
- Focus on mutual benefit and professional collaboration
- Keep warm, friendly, and respectful tone
- Mention specific collaboration ideas (cross-promo, joint content, etc.)
- Include a clear call-to-action

Guidelines:
- No explicit wording
- Professional and respectful
- Focus on business benefits
- Keep it concise and engaging

Return plain text only, no quotes or formatting.
"""

async def suggest_collabs(tenant_id: str, muse_id: str, niche_keywords: List[str], top_k: int = 5) -> Dict[str, Any]:
    """Suggère des collaborations basées sur la niche et les similarités."""
    # Recherche sémantique de profils similaires
    query = " ".join(niche_keywords[:6]) if niche_keywords else "onlyfans cosplay niche collab"
    
    # Rechercher dans le vector store (simulé pour V1)
    hits = await VectorStore.semantic_search(
        query=query, 
        top_k=top_k, 
        filters={"type": "creator_profile"}
    )
    
    profiles = []
    for h in hits:
        profiles.append({
            "handle": h.get("handle", "unknown"),
            "platform": h.get("platform", "instagram"),
            "audience_size": h.get("audience_size", None),
            "niche": h.get("niche", None),
            "similarity": float(h.get("score", 0.0)),
            "sample_overlap": h.get("overlap", None),
        })

    # Si pas assez de résultats, générer des suggestions simulées
    if len(profiles) < top_k:
        profiles.extend(_generate_mock_profiles(niche_keywords, top_k - len(profiles)))

    # Générer un template de DM via IA
    try:
        deepseek = DeepSeekService(
            api_key="your-api-key",
            model="deepseek-chat",
            temperature=0.7
        )
        
        response = await deepseek.generate([
            {"role": "user", "content": OUTREACH_PROMPT}
        ])
        
        dm_template = response.text.strip()
    except Exception as e:
        print(f"Erreur lors de la génération du DM: {e}")
        dm_template = _generate_fallback_dm(niche_keywords)

    return {
        "profiles": profiles,
        "outreach_template": dm_template
    }

def _generate_mock_profiles(niche_keywords: List[str], count: int) -> List[Dict[str, Any]]:
    """Génère des profils simulés pour les tests."""
    mock_profiles = []
    
    base_profiles = [
        {
            "handle": "cosplay_queen_23",
            "platform": "instagram",
            "audience_size": 45000,
            "niche": "cosplay",
            "similarity": 0.85,
            "sample_overlap": 1200
        },
        {
            "handle": "fantasy_creator",
            "platform": "reddit",
            "audience_size": 25000,
            "niche": "cosplay",
            "similarity": 0.78,
            "sample_overlap": 800
        },
        {
            "handle": "fitness_motivation",
            "platform": "tiktok",
            "audience_size": 120000,
            "niche": "fitness",
            "similarity": 0.72,
            "sample_overlap": 2000
        },
        {
            "handle": "lifestyle_vibes",
            "platform": "instagram",
            "audience_size": 35000,
            "niche": "lifestyle",
            "similarity": 0.68,
            "sample_overlap": 600
        },
        {
            "handle": "creative_content",
            "platform": "twitter",
            "audience_size": 18000,
            "niche": "art",
            "similarity": 0.65,
            "sample_overlap": 400
        }
    ]
    
    # Filtrer selon les niches
    filtered_profiles = []
    for profile in base_profiles:
        if not niche_keywords or any(niche in profile["niche"].lower() for niche in niche_keywords):
            filtered_profiles.append(profile)
    
    return filtered_profiles[:count]

def _generate_fallback_dm(niche_keywords: List[str]) -> str:
    """Génère un DM de fallback."""
    niche = niche_keywords[0] if niche_keywords else "content"
    
    templates = {
        "cosplay": "Hey! I love your cosplay content! Would you be interested in doing a cross-promo? I think our audiences would really enjoy each other's content. Let me know if you're interested! 😊",
        "fitness": "Hi! Your fitness content is amazing! I'd love to collaborate on some motivational content. Cross-promo could benefit both of us. What do you think? 💪",
        "lifestyle": "Hello! Your lifestyle content is so inspiring! I'd love to explore a collaboration opportunity. Cross-promo could be great for both of us. Interested? ✨",
        "default": "Hey! I love your content! Would you be interested in doing a cross-promo? I think our audiences would really enjoy each other's content. Let me know if you're interested! 😊"
    }
    
    return templates.get(niche, templates["default"])

async def analyze_collab_potential(tenant_id: str, muse_id: str, target_handle: str, target_platform: str) -> Dict[str, Any]:
    """Analyse le potentiel de collaboration avec un créateur spécifique."""
    # Pour V1, on simule l'analyse
    # Dans une version future, cela pourrait analyser les données réelles
    
    analysis = {
        "compatibility_score": 0.75,  # Score de compatibilité (0-1)
        "audience_overlap": 0.15,     # Chevauchement d'audience estimé
        "collab_ideas": [
            "Cross-promotion sur les réseaux sociaux",
            "Contenu collaboratif (photos/vidéos ensemble)",
            "Live stream conjoint",
            "Bundle d'offres spéciales"
        ],
        "risks": [
            "Audience overlap potentiel",
            "Différences de style de contenu"
        ],
        "recommendations": [
            "Commencez par une cross-promo simple",
            "Testez avec du contenu non-exclusif d'abord",
            "Communiquez clairement sur les attentes"
        ]
    }
    
    return analysis

async def track_collab_performance(tenant_id: str, muse_id: str, collab_id: str, metrics: Dict[str, Any]) -> bool:
    """Suit les performances d'une collaboration."""
    try:
        await db["ai_collab_suggestions"].update_one(
            {
                "_id": collab_id,
                "tenant_id": tenant_id,
                "muse_id": muse_id
            },
            {
                "$set": {
                    "performance_metrics": metrics,
                    "tracked_at": datetime.now(timezone.utc)
                }
            }
        )
        return True
    except Exception as e:
        print(f"Erreur lors du suivi des performances: {e}")
        return False

async def get_collab_history(tenant_id: str, muse_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Récupère l'historique des suggestions de collaboration."""
    cursor = db["ai_collab_suggestions"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id
    }).sort("ts", -1).limit(limit)
    
    collabs = []
    for collab in await cursor.to_list(None):
        collab["id"] = str(collab["_id"])
        del collab["_id"]
        collabs.append(collab)
    
    return collabs

async def generate_collab_content_ideas(tenant_id: str, muse_id: str, target_niche: str) -> List[str]:
    """Génère des idées de contenu collaboratif."""
    try:
        content_prompt = f"""
        Generate 5 creative collaboration content ideas for adult content creators in the {target_niche} niche.
        
        Focus on:
        - Cross-promotion strategies
        - Joint content creation
        - Audience engagement
        - Mutual benefit
        
        Keep ideas respectful and platform-compliant.
        Return as a simple list, one idea per line.
        """
        
        deepseek = DeepSeekService(
            api_key="your-api-key",
            model="deepseek-chat",
            temperature=0.8
        )
        
        response = await deepseek.generate([
            {"role": "user", "content": content_prompt}
        ])
        
        # Parser les idées (une par ligne)
        ideas = [line.strip() for line in response.text.split('\n') if line.strip()]
        return ideas[:5]  # Limiter à 5 idées
        
    except Exception as e:
        print(f"Erreur lors de la génération d'idées: {e}")
        return _generate_fallback_content_ideas(target_niche)

def _generate_fallback_content_ideas(niche: str) -> List[str]:
    """Génère des idées de contenu de fallback."""
    ideas_by_niche = {
        "cosplay": [
            "Créer un cosplay duo avec des personnages complémentaires",
            "Organiser un concours de cosplay collaboratif",
            "Partager des tutoriels de maquillage cosplay",
            "Faire un live stream de création de costume",
            "Créer un bundle de photos cosplay exclusives"
        ],
        "fitness": [
            "Organiser un défi fitness collaboratif",
            "Créer des routines d'entraînement en duo",
            "Partager des conseils nutritionnels",
            "Faire un live stream d'entraînement",
            "Créer un programme fitness exclusif"
        ],
        "lifestyle": [
            "Partager des routines quotidiennes",
            "Créer du contenu lifestyle collaboratif",
            "Organiser un Q&A en duo",
            "Partager des conseils de bien-être",
            "Créer un bundle de contenu lifestyle"
        ]
    }
    
    return ideas_by_niche.get(niche, ideas_by_niche["lifestyle"])




