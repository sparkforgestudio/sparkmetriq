# api/services/assistant/jobs.py
"""
Jobs d'orchestration pour l'Assistant IA Stratégique.
"""

from datetime import datetime, timezone
from api.services.scheduler.job_runner import scheduler
from api.services.assistant.alerts_service import compute_basic_alerts, persist_alerts
from api.services.assistant.trends_service import ingest_external_trends
from api.databases.databases import db

async def schedule_assistant_jobs():
    """Programme les jobs périodiques de l'assistant."""
    
    # Job d'alertes toutes les 6h
    async def run_alerts_all():
        """Lance les alertes pour tous les créateurs actifs."""
        try:
            print("🔔 Début du job d'alertes assistant...")
            
            # Récupérer tous les tenants actifs
            tenants = await db["muses"].distinct("tenant_id")
            
            total_alerts = 0
            for tenant_id in tenants:
                # Récupérer les muses de ce tenant
                muses = await db["muses"].distinct("muse_id", {"tenant_id": tenant_id})
                
                for muse_id in muses:
                    try:
                        alerts = await compute_basic_alerts(tenant_id, muse_id)
                        await persist_alerts(tenant_id, muse_id, alerts)
                        total_alerts += len(alerts)
                    except Exception as e:
                        print(f"❌ Erreur alertes pour {tenant_id}/{muse_id}: {e}")
            
            print(f"✅ Job d'alertes terminé: {total_alerts} alertes créées")
            
        except Exception as e:
            print(f"❌ Erreur lors du job d'alertes: {e}")

    # Job d'ingestion des tendances quotidien
    async def ingest_trends_daily():
        """Ingère les tendances externes quotidiennement."""
        try:
            print("📈 Début de l'ingestion des tendances...")
            
            ingested_count = await ingest_external_trends()
            print(f"✅ Ingestion terminée: {ingested_count} tendances ingérées")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'ingestion des tendances: {e}")

    # Job de nettoyage hebdomadaire
    async def cleanup_assistant_data():
        """Nettoie les données anciennes de l'assistant."""
        try:
            print("🧹 Début du nettoyage des données assistant...")
            
            from datetime import timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(days=90)
            
            # Nettoyer les anciennes alertes fermées
            deleted_alerts = await db["ai_alerts"].delete_many({
                "status": "closed",
                "ts": {"$lt": cutoff}
            })
            
            # Nettoyer les anciennes suggestions de collaboration
            deleted_collabs = await db["ai_collab_suggestions"].delete_many({
                "ts": {"$lt": cutoff}
            })
            
            # Nettoyer les anciennes recommandations
            deleted_recos = await db["ai_reco_history"].delete_many({
                "ts": {"$lt": cutoff}
            })
            
            print(f"✅ Nettoyage terminé:")
            print(f"   - Alertes supprimées: {deleted_alerts.deleted_count}")
            print(f"   - Collaborations supprimées: {deleted_collabs.deleted_count}")
            print(f"   - Recommandations supprimées: {deleted_recos.deleted_count}")
            
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage: {e}")

    # Job d'analyse des performances mensuelles
    async def analyze_monthly_performance():
        """Analyse les performances mensuelles et génère des insights."""
        try:
            print("📊 Début de l'analyse des performances mensuelles...")
            
            # Récupérer tous les créateurs actifs
            tenants = await db["muses"].distinct("tenant_id")
            
            for tenant_id in tenants:
                muses = await db["muses"].distinct("muse_id", {"tenant_id": tenant_id})
                
                for muse_id in muses:
                    try:
                        # Analyser les performances du mois précédent
                        from datetime import timedelta
                        now = datetime.now(timezone.utc)
                        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                        prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
                        
                        # Calculer les KPIs du mois précédent
                        from api.services.assistant.context_service import load_creator_context
                        context = await load_creator_context(
                            tenant_id, muse_id, prev_month_start, month_start
                        )
                        
                        # Générer des insights automatiques
                        insights = []
                        kpis = context.get("kpIs", {})
                        
                        if kpis.get("revenue_growth", 0) > 20:
                            insights.append("Excellente croissance des revenus ce mois-ci!")
                        elif kpis.get("revenue_growth", 0) < -20:
                            insights.append("Baisse des revenus détectée - analysez les causes")
                        
                        if kpis.get("ppv_conversion", 0) > 0.15:
                            insights.append("Conversion PPV excellente - maintenez cette stratégie")
                        elif kpis.get("ppv_conversion", 0) < 0.05:
                            insights.append("Conversion PPV faible - optimisez les offres")
                        
                        # Enregistrer les insights
                        if insights:
                            await db["ai_monthly_insights"].insert_one({
                                "tenant_id": tenant_id,
                                "muse_id": muse_id,
                                "month": prev_month_start.strftime("%Y-%m"),
                                "insights": insights,
                                "kpis": kpis,
                                "generated_at": datetime.now(timezone.utc)
                            })
                        
                    except Exception as e:
                        print(f"❌ Erreur analyse pour {tenant_id}/{muse_id}: {e}")
            
            print("✅ Analyse des performances mensuelles terminée")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse des performances: {e}")

    # Programmer les jobs
    try:
        # Alertes toutes les 6h
        scheduler.add_job(
            run_alerts_all,
            "interval",
            hours=6,
            id="assistant_alerts_job",
            replace_existing=True
        )
        
        # Ingestion des tendances quotidienne à 2h du matin
        scheduler.add_job(
            ingest_trends_daily,
            "cron",
            hour=2,
            minute=0,
            id="assistant_trends_job",
            replace_existing=True
        )
        
        # Nettoyage hebdomadaire le dimanche à 3h du matin
        scheduler.add_job(
            cleanup_assistant_data,
            "cron",
            day_of_week="sun",
            hour=3,
            minute=0,
            id="assistant_cleanup_job",
            replace_existing=True
        )
        
        # Analyse des performances mensuelle le 1er de chaque mois à 4h du matin
        scheduler.add_job(
            analyze_monthly_performance,
            "cron",
            day=1,
            hour=4,
            minute=0,
            id="assistant_performance_job",
            replace_existing=True
        )
        
        print("✅ Jobs de l'assistant IA programmés avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de la programmation des jobs: {e}")

async def run_manual_alerts(tenant_id: str, muse_id: str) -> int:
    """Lance manuellement les alertes pour un créateur spécifique."""
    try:
        alerts = await compute_basic_alerts(tenant_id, muse_id)
        await persist_alerts(tenant_id, muse_id, alerts)
        return len(alerts)
    except Exception as e:
        print(f"❌ Erreur lors des alertes manuelles: {e}")
        return 0

async def get_assistant_job_status() -> dict:
    """Récupère le statut des jobs de l'assistant."""
    jobs = scheduler.get_jobs()
    assistant_jobs = [job for job in jobs if job.id.startswith("assistant_")]
    
    return {
        "total_jobs": len(assistant_jobs),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in assistant_jobs
        ]
    }




