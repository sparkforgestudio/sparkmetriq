# api/services/assistant/plan_service.py
"""
Service de génération du plan d'action mensuel IA.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from api.services.chat_omnichannel.deepseek_service import DeepSeekService
from api.services.assistant.context_service import load_creator_context, get_creator_performance_summary, get_creator_benchmarks
from api.services.assistant.trends_service import search_trends, get_trend_insights
from api.schemas.assistant import ActionPlanIn, ActionItem
from api.databases.databases import db

PLAN_PROMPT = """
You are a senior growth strategist for adult-content creators (OnlyFans-like). 
Using the context (KPIs, persona, niches) and external trends, propose a monthly action plan.

Context provided:
- Creator KPIs: messages, payers, GMV, PPV stats, platform performance
- Persona: tone, bio, niches
- Performance summary: growth trends, engagement levels
- Benchmarks: industry averages for the niche
- Trends: current trending topics and activation ideas

Return JSON with fields: goals[], actions[], insights[].

Goals format:
- name: specific goal name
- target_value: numerical target
- unit: unit of measurement (subs, revenue, engagement_rate, etc.)
- rationale: why this goal matters

Actions format:
- title: action title
- description: detailed description
- channel: platform (onlyfans, instagram, tiktok, reddit, twitter, telegram)
- cta: call-to-action
- kpi: key performance indicator to track
- owner: who executes (creator, assistant, both)
- due_day: day of month (1-31)
- effort: low/medium/high

Insights format:
- Bullet points explaining rationale and risks
- Strategic recommendations
- Platform-specific advice

Keep respectful, policy-safe wording (platform compliant, NSFW-adjacent tone if needed).
Focus on actionable, measurable strategies.
"""

async def build_monthly_plan(tenant_id: str, payload: ActionPlanIn) -> Dict[str, Any]:
    """Construit un plan d'action mensuel personnalisé."""
    # 1) Charger le contexte
    df, dt = None, None
    if payload.kpi_window:
        df, dt = payload.kpi_window.date_from, payload.kpi_window.date_to
    else:
        now = datetime.now(timezone.utc)
        df = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        dt = now

    ctx = await load_creator_context(tenant_id, payload.muse_id, df, dt)
    performance = await get_creator_performance_summary(tenant_id, payload.muse_id, 30)
    
    # Récupérer les benchmarks pour la niche principale
    primary_niche = ctx.get("niches", ["lifestyle"])[0] if ctx.get("niches") else "lifestyle"
    benchmarks = await get_creator_benchmarks(tenant_id, payload.muse_id, primary_niche)
    
    # Récupérer les tendances
    trends = await search_trends(tenant_id, ctx.get("niches", []), limit=5)
    trend_insights = await get_trend_insights(tenant_id, payload.muse_id, ctx.get("niches", []))

    # 2) Préparer l'input pour le LLM
    llm_input = {
        "month": payload.month,
        "preferences": payload.preferences,
        "context": ctx,
        "performance": performance,
        "benchmarks": benchmarks,
        "trends": trends,
        "trend_insights": trend_insights,
        "existing_goals": [goal.model_dump() for goal in payload.goals]
    }

    # 3) Appel au LLM
    prompt = PLAN_PROMPT + "\nCONTEXT:\n" + json.dumps(llm_input, indent=2) + "\n\nReturn valid JSON only."
    
    try:
        deepseek = DeepSeekService(
            api_key="your-api-key",  # À configurer via env
            model="deepseek-chat",
            temperature=0.7
        )
        
        response = await deepseek.generate([
            {"role": "user", "content": prompt}
        ])
        
        # Parser le JSON de réponse
        try:
            out = json.loads(response.text)
        except json.JSONDecodeError:
            # Fallback si le JSON n'est pas valide
            out = _generate_fallback_plan(ctx, performance, trends)
        
    except Exception as e:
        print(f"Erreur lors de la génération du plan IA: {e}")
        out = _generate_fallback_plan(ctx, performance, trends)

    # 4) Valider et formater les actions
    actions = []
    for action_data in out.get("actions", []):
        try:
            action = ActionItem(**action_data)
            actions.append(action.model_dump())
        except Exception as e:
            print(f"Erreur lors de la validation de l'action: {e}")
            # Ajouter une action par défaut
            actions.append({
                "title": action_data.get("title", "Action par défaut"),
                "description": action_data.get("description", "Description par défaut"),
                "channel": action_data.get("channel", "instagram"),
                "cta": action_data.get("cta", "Engage with content"),
                "kpi": action_data.get("kpi", "engagement"),
                "owner": "creator",
                "due_day": 15,
                "effort": "medium"
            })

    return {
        "goals": out.get("goals", []),
        "actions": actions,
        "insights": out.get("insights", [])
    }

def _generate_fallback_plan(ctx: Dict[str, Any], performance: Dict[str, Any], trends: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Génère un plan de fallback si l'IA échoue."""
    kpis = ctx.get("kpIs", {})
    niches = ctx.get("niches", ["lifestyle"])
    primary_niche = niches[0] if niches else "lifestyle"
    
    # Objectifs basés sur les performances actuelles
    goals = []
    if kpis.get("payers", 0) < 20:
        goals.append({
            "name": "Augmenter les abonnés payants",
            "target_value": 25,
            "unit": "payers",
            "rationale": "Augmenter la base de clients payants pour stabiliser les revenus"
        })
    
    if kpis.get("ppv_conversion", 0) < 0.1:
        goals.append({
            "name": "Améliorer la conversion PPV",
            "target_value": 0.12,
            "unit": "conversion_rate",
            "rationale": "Optimiser les offres PPV pour augmenter les revenus par utilisateur"
        })
    
    # Actions basées sur la niche
    actions = []
    if primary_niche == "cosplay":
        actions.extend([
            {
                "title": "Créer du contenu cosplay POV",
                "description": "Développer du contenu cosplay avec des angles POV pour augmenter l'engagement",
                "channel": "reddit",
                "cta": "Votez pour le prochain cosplay",
                "kpi": "engagement_rate",
                "owner": "creator",
                "due_day": 5,
                "effort": "medium"
            },
            {
                "title": "Teaser Instagram quotidien",
                "description": "Publier un teaser quotidien sur Instagram pour maintenir l'engagement",
                "channel": "instagram",
                "cta": "Lien en bio pour plus de contenu",
                "kpi": "click_through_rate",
                "owner": "creator",
                "due_day": 10,
                "effort": "low"
            }
        ])
    elif primary_niche == "fitness":
        actions.extend([
            {
                "title": "Routine matinale fitness",
                "description": "Créer du contenu de routine matinale fitness pour TikTok",
                "channel": "tiktok",
                "cta": "Suivez-moi pour plus de routines",
                "kpi": "followers_growth",
                "owner": "creator",
                "due_day": 8,
                "effort": "medium"
            },
            {
                "title": "Transformation avant/après",
                "description": "Partager du contenu de transformation pour motiver l'audience",
                "channel": "instagram",
                "cta": "DM pour des conseils personnalisés",
                "kpi": "dm_requests",
                "owner": "creator",
                "due_day": 15,
                "effort": "low"
            }
        ])
    else:
        # Actions génériques
        actions.extend([
            {
                "title": "Contenu quotidien Instagram",
                "description": "Maintenir une présence quotidienne sur Instagram",
                "channel": "instagram",
                "cta": "Double-tap si vous aimez",
                "kpi": "engagement_rate",
                "owner": "creator",
                "due_day": 12,
                "effort": "low"
            },
            {
                "title": "Interaction avec l'audience",
                "description": "Répondre aux commentaires et DMs pour fidéliser",
                "channel": "telegram",
                "cta": "Répondez à mes messages",
                "kpi": "response_rate",
                "owner": "creator",
                "due_day": 20,
                "effort": "medium"
            }
        ])
    
    # Insights basés sur les performances
    insights = []
    if performance.get("growth_trend") == "negative":
        insights.append("Les revenus sont en baisse - concentrez-vous sur la rétention des clients existants")
    
    if performance.get("engagement_level") == "low":
        insights.append("L'engagement est faible - testez de nouveaux formats de contenu")
    
    if trends:
        top_trend = trends[0]
        insights.append(f"Tendance actuelle: {top_trend['topic']} - considérez cette opportunité")
    
    return {
        "goals": goals,
        "actions": actions,
        "insights": insights
    }

async def update_plan_version(tenant_id: str, muse_id: str, month: str, updates: Dict[str, Any]) -> bool:
    """Met à jour une version d'un plan."""
    try:
        # Récupérer le plan existant
        existing_plan = await db["ai_action_plans"].find_one({
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "month": month
        })
        
        if not existing_plan:
            return False
        
        # Incrémenter la version
        new_version = existing_plan.get("version", 1) + 1
        
        # Mettre à jour
        await db["ai_action_plans"].update_one(
            {"_id": existing_plan["_id"]},
            {
                "$set": {
                    **updates,
                    "version": new_version,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour du plan: {e}")
        return False

async def get_plan_history(tenant_id: str, muse_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Récupère l'historique des plans d'un créateur."""
    cursor = db["ai_action_plans"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id
    }).sort("created_at", -1).limit(limit)
    
    plans = []
    for plan in await cursor.to_list(None):
        plan["id"] = str(plan["_id"])
        del plan["_id"]
        plans.append(plan)
    
    return plans
