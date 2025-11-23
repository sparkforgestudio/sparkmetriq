# api/services/scheduler/ai_copy_service.py
"""
Service IA pour la génération de contenu et le copywriting.
"""

import json
from typing import Dict, Any, List
from api.services.chat_omnichannel.deepseek_service import DeepSeekService

PLATFORM_HINTS = {
    "tiktok": "Courte légende, énergique, call-to-action implicite, éviter mots interdits",
    "instagram": "Hashtags pertinents, ton sexy mais subtil, emojis dosés",
    "reddit": "Adapté au subreddit, plus descriptif, sans hashtags, 1 lien autorisé si OK",
    "twitter": "Court, punchy, un hook, éventuellement lien OUT",
    "telegram": "Teasing direct, CTA explicite, peut contenir lien direct",
    "onlyfans": "Teasing explicite, CTA vers PPV/DM, respecter guidelines",
    "threads": "Ton conversationnel, hashtags limités, engagement naturel"
}

def _prompt(platform: str, muse_id: str, tone: str, objective: str, language: str, user_prompt: str) -> str:
    hint = PLATFORM_HINTS.get(platform, "")
    return f"""
You are an expert copywriter for NSFW-adjacent social posts (respect platform policies).
Platform: {platform}
Muse: {muse_id}
Tone: {tone}
Objective: {objective}
Language: {language}
Guidelines: {hint}

Write a single caption and propose 5-12 hashtags (if relevant to this platform).
Input: {user_prompt}
Output format (JSON):
{{"caption": "...", "hashtags": ["..."], "emojis": ["..."], "warnings": ["..."]}}
"""

async def generate_preview(platform: str, muse_id: str, tone: str, objective: str, language: str, user_prompt: str) -> Dict[str, Any]:
    """Génère un aperçu de contenu via IA."""
    prompt = _prompt(platform, muse_id, tone, objective, language, user_prompt)
    
    # Utiliser DeepSeek pour générer le contenu
    deepseek = DeepSeekService(
        api_key="your-api-key",  # À configurer via env
        model="deepseek-chat",
        temperature=0.7
    )
    
    # Générer le texte
    response = await deepseek.generate([
        {"role": "user", "content": prompt}
    ])
    
    # Parser le JSON de réponse
    try:
        result = json.loads(response.text)
        return result
    except json.JSONDecodeError:
        # Fallback si le JSON n'est pas valide
        return {
            "caption": response.text[:500],  # Limiter la longueur
            "hashtags": ["#teaser", "#exclusive"],
            "emojis": ["🔥", "💋"],
            "warnings": ["JSON parsing failed, using raw text"]
        }

async def generate_weekly_themes(muse_id: str, persona_tone: str, objective: str) -> List[str]:
    """Génère des thèmes pour la semaine."""
    themes_prompt = f"""
Generate 5 weekly content themes for a NSFW creator named {muse_id}.
Tone: {persona_tone}
Objective: {objective}
Format: JSON array of theme strings
Example: ["Monday Motivation", "Teaser Tuesday", "Throwback Thursday", "Fan Friday", "Weekend Vibes"]
"""
    
    deepseek = DeepSeekService(
        api_key="your-api-key",
        model="deepseek-chat", 
        temperature=0.8
    )
    
    response = await deepseek.generate([
        {"role": "user", "content": themes_prompt}
    ])
    
    try:
        themes = json.loads(response.text)
        return themes if isinstance(themes, list) else []
    except json.JSONDecodeError:
        return ["Monday Motivation", "Teaser Tuesday", "Throwback Thursday", "Fan Friday", "Weekend Vibes"]




