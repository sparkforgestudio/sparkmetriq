# api/services/assistant/alerts_service.py
"""
Service d'alertes stratégiques automatisées.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from api.databases.databases import db
from api.services.chat_omnichannel.deepseek_service import DeepSeekService

async def compute_basic_alerts(tenant_id: str, muse_id: str) -> List[Dict[str, Any]]:
    """Calcule les alertes basiques pour un créateur."""
    now = datetime.now(timezone.utc)
    d7, d14 = now - timedelta(days=7), now - timedelta(days=14)
    d30, d60 = now - timedelta(days=30), now - timedelta(days=60)

    alerts = []

    # 1. Croissance des messages 7j vs 7-14j
    cur1 = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id, 
        "muse_id": muse_id, 
        "timestamp": {"$gte": d7, "$lt": now}
    })
    cur2 = await db["chat_messages"].count_documents({
        "tenant_id": tenant_id, 
        "muse_id": muse_id, 
        "timestamp": {"$gte": d14, "$lt": d7}
    })
    
    growth = ((cur1 - cur2) / cur2) * 100 if cur2 > 0 else (100.0 if cur1 > 0 else 0.0)

    if growth < -20:
        alerts.append({
            "kind": "growth_drop",
            "message": f"📉 Baisse de croissance des interactions {growth:.1f}% (7j). Considérez de nouveaux formats de contenu.",
            "severity": "high"
        })
    elif growth > 40:
        alerts.append({
            "kind": "over_perform",
            "message": f"📈 Surperformance d'interactions +{growth:.1f}% (7j). Capitalisez sur ce momentum!",
            "severity": "medium"
        })

    # 2. Churn des payeurs (approximation)
    p30 = set(await db["payments"].distinct("user_hash", {
        "tenant_id": tenant_id, 
        "muse_id": muse_id, 
        "status": "confirmed",
        "ts": {"$gte": d30, "$lt": now}
    }))
    p60 = set(await db["payments"].distinct("user_hash", {
        "tenant_id": tenant_id, 
        "muse_id": muse_id, 
        "status": "confirmed",
        "ts": {"$gte": d60, "$lt": d30}
    }))
    
    if p60 and len(p30) < int(0.7 * len(p60)):
        alerts.append({
            "kind": "churn_high",
            "message": "🔁 Churn élevé des payeurs récents. Envisagez un bundle/relance ou une offre de fidélisation.",
            "severity": "high"
        })

    # 3. Performance PPV
    ppv_stats = await db["ppv_logs"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "ts": {"$gte": d7, "$lt": now}
            }
        },
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        }
    ]).to_list(None)
    
    ppv_data = {item["_id"]: item["count"] for item in ppv_stats}
    ppv_sent = ppv_data.get("sent", 0)
    ppv_paid = ppv_data.get("paid", 0)
    ppv_conversion = (ppv_paid / ppv_sent) if ppv_sent > 0 else 0.0

    if ppv_sent > 10 and ppv_conversion < 0.05:  # Moins de 5% de conversion
        alerts.append({
            "kind": "pricing_issue",
            "message": f"💰 Conversion PPV faible ({ppv_conversion:.1%}). Considérez ajuster les prix ou améliorer les teasers.",
            "severity": "medium"
        })

    # 4. Performance par plateforme
    platform_stats = await db["publish_logs"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "ts": {"$gte": d7, "$lt": now},
                "status": "published"
            }
        },
        {
            "$group": {
                "_id": "$platform",
                "count": {"$sum": 1}
            }
        }
    ]).to_list(None)

    if platform_stats:
        platform_counts = {item["_id"]: item["count"] for item in platform_stats}
        total_posts = sum(platform_counts.values())
        
        # Détecter si une plateforme est sous-utilisée
        for platform, count in platform_counts.items():
            if total_posts > 5 and count < total_posts * 0.2:  # Moins de 20% des posts
                alerts.append({
                    "kind": "trend_opportunity",
                    "message": f"📱 Plateforme {platform} sous-utilisée ({count}/{total_posts} posts). Opportunité d'expansion.",
                    "severity": "low"
                })

    # 5. Alertes basées sur les revenus
    revenue_stats = await db["payments"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "status": "confirmed",
                "ts": {"$gte": d7, "$lt": now}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_revenue": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1}
            }
        }
    ]).to_list(1)

    if revenue_stats:
        current_revenue = revenue_stats[0]["total_revenue"]
        current_transactions = revenue_stats[0]["transaction_count"]
        
        # Comparer avec la semaine précédente
        prev_revenue_stats = await db["payments"].aggregate([
            {
                "$match": {
                    "tenant_id": tenant_id,
                    "muse_id": muse_id,
                    "status": "confirmed",
                    "ts": {"$gte": d14, "$lt": d7}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$amount"}
                }
            }
        ]).to_list(1)
        
        if prev_revenue_stats:
            prev_revenue = prev_revenue_stats[0]["total_revenue"]
            revenue_growth = ((current_revenue - prev_revenue) / prev_revenue) * 100 if prev_revenue > 0 else 0.0
            
            if revenue_growth < -30:
                alerts.append({
                    "kind": "growth_drop",
                    "message": f"💸 Baisse significative des revenus ({revenue_growth:.1f}%). Analysez les causes et ajustez la stratégie.",
                    "severity": "high"
                })
            elif revenue_growth > 50:
                alerts.append({
                    "kind": "over_perform",
                    "message": f"🚀 Excellente croissance des revenus (+{revenue_growth:.1f}%)! Maintenez cette dynamique.",
                    "severity": "medium"
                })

    return alerts

async def compute_advanced_alerts(tenant_id: str, muse_id: str) -> List[Dict[str, Any]]:
    """Calcule des alertes avancées basées sur l'IA."""
    try:
        # Charger le contexte récent
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        
        context_prompt = f"""
        Analysez les performances récentes de ce créateur et générez des alertes stratégiques.
        
        Créateur: {muse_id}
        Période: dernière semaine
        
        Génère 2-3 alertes stratégiques basées sur:
        - Patterns de performance
        - Opportunités de croissance
        - Risques identifiés
        
        Format JSON: [{{"kind": "type", "message": "description", "severity": "level"}}]
        
        Types d'alertes possibles:
        - growth_drop: baisse de performance
        - over_perform: surperformance
        - churn_high: churn élevé
        - trend_opportunity: opportunité de tendance
        - pricing_issue: problème de pricing
        """
        
        deepseek = DeepSeekService(
            api_key="your-api-key",
            model="deepseek-chat",
            temperature=0.3
        )
        
        response = await deepseek.generate([
            {"role": "user", "content": context_prompt}
        ])
        
        # Parser la réponse JSON
        import json
        try:
            ai_alerts = json.loads(response.text)
            return ai_alerts if isinstance(ai_alerts, list) else []
        except json.JSONDecodeError:
            return []
            
    except Exception as e:
        print(f"Erreur lors du calcul des alertes avancées: {e}")
        return []

async def persist_alerts(tenant_id: str, muse_id: str, alerts: List[Dict[str, Any]]):
    """Persiste les alertes en base de données."""
    if not alerts:
        return
    
    now = datetime.now(timezone.utc)
    docs = []
    
    for alert in alerts:
        # Vérifier si l'alerte existe déjà (éviter les doublons)
        existing = await db["ai_alerts"].find_one({
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "kind": alert["kind"],
            "message": alert["message"],
            "status": "open"
        })
        
        if not existing:
            docs.append({
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "kind": alert["kind"],
                "message": alert["message"],
                "severity": alert.get("severity", "medium"),
                "status": "open",
                "ts": now
            })
    
    if docs:
        await db["ai_alerts"].insert_many(docs)

async def acknowledge_alert(tenant_id: str, alert_id: str) -> bool:
    """Marque une alerte comme acquittée."""
    try:
        result = await db["ai_alerts"].update_one(
            {
                "_id": alert_id,
                "tenant_id": tenant_id
            },
            {
                "$set": {
                    "status": "ack",
                    "acknowledged_at": datetime.now(timezone.utc)
                }
            }
        )
        return result.modified_count == 1
    except Exception as e:
        print(f"Erreur lors de l'acquittement de l'alerte: {e}")
        return False

async def close_alert(tenant_id: str, alert_id: str) -> bool:
    """Ferme une alerte."""
    try:
        result = await db["ai_alerts"].update_one(
            {
                "_id": alert_id,
                "tenant_id": tenant_id
            },
            {
                "$set": {
                    "status": "closed",
                    "closed_at": datetime.now(timezone.utc)
                }
            }
        )
        return result.modified_count == 1
    except Exception as e:
        print(f"Erreur lors de la fermeture de l'alerte: {e}")
        return False

async def get_alert_summary(tenant_id: str, muse_id: str) -> Dict[str, Any]:
    """Récupère un résumé des alertes."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    
    # Compter les alertes par statut
    status_counts = await db["ai_alerts"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "ts": {"$gte": week_ago}
            }
        },
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        }
    ]).to_list(None)
    
    status_summary = {item["_id"]: item["count"] for item in status_counts}
    
    # Compter par sévérité
    severity_counts = await db["ai_alerts"].aggregate([
        {
            "$match": {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "ts": {"$gte": week_ago}
            }
        },
        {
            "$group": {
                "_id": "$severity",
                "count": {"$sum": 1}
            }
        }
    ]).to_list(None)
    
    severity_summary = {item["_id"]: item["count"] for item in severity_counts}
    
    return {
        "total_alerts": sum(status_summary.values()),
        "open_alerts": status_summary.get("open", 0),
        "acknowledged_alerts": status_summary.get("ack", 0),
        "closed_alerts": status_summary.get("closed", 0),
        "high_severity": severity_summary.get("high", 0),
        "medium_severity": severity_summary.get("medium", 0),
        "low_severity": severity_summary.get("low", 0),
        "period": "7_days"
    }



