# scripts/optimize_mongodb_indexes.py
"""
Script pour optimiser les index MongoDB et améliorer les performances.
Crée tous les index nécessaires pour les collections de l'application.
"""

import asyncio
import logging
from datetime import datetime, timezone
from api.databases.databases import db
from api.core.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBIndexOptimizer:
    """Optimiseur d'index MongoDB."""
    
    def __init__(self):
        self.indexes_created = 0
        self.indexes_updated = 0
        self.collections_processed = 0
    
    async def create_index(self, collection_name: str, index_spec: list, options: dict = None) -> bool:
        """
        Créer un index MongoDB.
        
        Args:
            collection_name: Nom de la collection
            index_spec: Spécification de l'index
            options: Options de l'index
            
        Returns:
            True si l'index a été créé, False sinon
        """
        try:
            options = options or {}
            await db[collection_name].create_index(index_spec, **options)
            logger.info(f"✅ Index créé: {collection_name}.{index_spec}")
            self.indexes_created += 1
            return True
        except Exception as e:
            logger.error(f"❌ Erreur création index {collection_name}.{index_spec}: {e}")
            return False
    
    async def optimize_chat_indexes(self):
        """Optimiser les index pour le système de chat."""
        logger.info("🔧 Optimisation des index de chat...")
        
        chat_indexes = [
            # Index pour les requêtes par conversation
            (["conversation_id", "timestamp"], {"name": "conversation_timestamp"}),
            # Index pour les requêtes par utilisateur
            (["user_id", "timestamp"], {"name": "user_timestamp"}),
            # Index pour les requêtes par plateforme
            (["platform", "timestamp"], {"name": "platform_timestamp"}),
            # Index pour les requêtes par rôle
            (["role", "timestamp"], {"name": "role_timestamp"}),
            # Index composé pour les requêtes complexes
            (["conversation_id", "role", "timestamp"], {"name": "conversation_role_timestamp"}),
            # Index pour les requêtes de recherche textuelle
            (["text"], {"name": "text_search", "sparse": True}),
        ]
        
        for index_spec, options in chat_indexes:
            await self.create_index("chat_messages", index_spec, options)
    
    async def optimize_cloudphone_indexes(self):
        """Optimiser les index pour CloudPhone Management."""
        logger.info("🔧 Optimisation des index CloudPhone...")
        
        # Profiles
        profile_indexes = [
            (["org_id", "name"], {"unique": True, "name": "org_name_unique"}),
            (["org_id", "area"], {"name": "org_area"}),
            (["org_id", "tags"], {"name": "org_tags"}),
            (["org_id", "provider_ref"], {"sparse": True, "name": "org_provider_ref"}),
            (["org_id", "created_at"], {"name": "org_created_at"}),
            (["org_id", "updated_at"], {"name": "org_updated_at"}),
        ]
        
        for index_spec, options in profile_indexes:
            await self.create_index("cloudphone_profiles", index_spec, options)
        
        # Devices
        device_indexes = [
            (["org_id", "state"], {"name": "org_state"}),
            (["org_id", "area"], {"name": "org_area"}),
            (["org_id", "provider_ref"], {"unique": True, "sparse": True, "name": "org_provider_ref_unique"}),
            (["org_id", "created_at"], {"name": "org_created_at"}),
            (["org_id", "updated_at"], {"name": "org_updated_at"}),
        ]
        
        for index_spec, options in device_indexes:
            await self.create_index("cloudphone_devices", index_spec, options)
        
        # App Accounts
        app_account_indexes = [
            (["org_id", "app"], {"name": "org_app"}),
            (["org_id", "username"], {"name": "org_username"}),
            (["org_id", "created_at"], {"name": "org_created_at"}),
        ]
        
        for index_spec, options in app_account_indexes:
            await self.create_index("cloudphone_app_accounts", index_spec, options)
        
        # Device App Slots
        slot_indexes = [
            (["org_id", "device_id", "app"], {"name": "org_device_app"}),
            (["org_id", "device_id", "slot_index"], {"unique": True, "name": "org_device_slot_unique"}),
            (["org_id", "state"], {"name": "org_state"}),
            (["org_id", "created_at"], {"name": "org_created_at"}),
        ]
        
        for index_spec, options in slot_indexes:
            await self.create_index("cloudphone_device_app_slots", index_spec, options)
        
        # Bindings
        binding_indexes = [
            (["org_id", "slot_id"], {"unique": True, "name": "org_slot_unique"}),
            (["org_id", "app_account_id"], {"name": "org_app_account"}),
            (["org_id", "created_at"], {"name": "org_created_at"}),
        ]
        
        for index_spec, options in binding_indexes:
            await self.create_index("cloudphone_bindings_appaccount_slot", index_spec, options)
    
    async def optimize_otp_indexes(self):
        """Optimiser les index pour le système OTP."""
        logger.info("🔧 Optimisation des index OTP...")
        
        otp_indexes = [
            # Index pour les requêtes par organisation et état
            (["org_id", "state"], {"name": "org_state"}),
            # Index pour les requêtes par slot
            (["slot_id"], {"name": "slot_id"}),
            # Index pour les requêtes par device
            (["device_id"], {"name": "device_id"}),
            # Index pour les requêtes par app et pays
            (["app", "country"], {"name": "app_country"}),
            # Index pour les requêtes par provider
            (["provider"], {"name": "provider"}),
            # Index pour les requêtes temporelles
            (["created_at"], {"name": "created_at"}),
            (["updated_at"], {"name": "updated_at"}),
            # Index pour les requêtes par session provider
            (["provider_session_id"], {"unique": True, "sparse": True, "name": "provider_session_unique"}),
            # Index composé pour les requêtes complexes
            (["org_id", "app", "country"], {"name": "org_app_country"}),
            (["org_id", "state", "created_at"], {"name": "org_state_created"}),
        ]
        
        for index_spec, options in otp_indexes:
            await self.create_index("otp_sessions", index_spec, options)
    
    async def optimize_observability_indexes(self):
        """Optimiser les index pour l'observabilité."""
        logger.info("🔧 Optimisation des index d'observabilité...")
        
        # Activity Logs
        activity_indexes = [
            (["org_id", "timestamp"], {"name": "org_timestamp"}),
            (["org_id", "scope", "timestamp"], {"name": "org_scope_timestamp"}),
            (["org_id", "user_id", "timestamp"], {"name": "org_user_timestamp"}),
            (["org_id", "resource_type", "resource_id"], {"name": "org_resource"}),
            (["org_id", "action", "status"], {"name": "org_action_status"}),
        ]
        
        for index_spec, options in activity_indexes:
            await self.create_index("activity_logs", index_spec, options)
        
        # Alerts
        alert_indexes = [
            (["org_id", "created_at"], {"name": "org_created_at"}),
            (["org_id", "status"], {"name": "org_status"}),
            (["org_id", "alert_type"], {"name": "org_alert_type"}),
            (["org_id", "severity"], {"name": "org_severity"}),
            (["org_id", "resource_type", "resource_id"], {"name": "org_resource"}),
        ]
        
        for index_spec, options in alert_indexes:
            await self.create_index("alerts", index_spec, options)
    
    async def optimize_other_indexes(self):
        """Optimiser les index pour les autres collections."""
        logger.info("🔧 Optimisation des autres index...")
        
        # Users
        user_indexes = [
            (["email"], {"unique": True, "name": "email_unique"}),
            (["org_id"], {"name": "org_id"}),
            (["role"], {"name": "role"}),
            (["created_at"], {"name": "created_at"}),
        ]
        
        for index_spec, options in user_indexes:
            await self.create_index("users", index_spec, options)
        
        # Tunnels
        tunnel_indexes = [
            (["org_id", "created_at"], {"name": "org_created_at"}),
            (["muse_id"], {"name": "muse_id"}),
            (["platform"], {"name": "platform"}),
        ]
        
        for index_spec, options in tunnel_indexes:
            await self.create_index("tunnels", index_spec, options)
        
        # Payments
        payment_indexes = [
            (["org_id", "created_at"], {"name": "org_created_at"}),
            (["muse_id"], {"name": "muse_id"}),
            (["status"], {"name": "status"}),
            (["email"], {"name": "email"}),
        ]
        
        for index_spec, options in payment_indexes:
            await self.create_index("payments", index_spec, options)
    
    async def analyze_collections(self):
        """Analyser les collections existantes."""
        logger.info("🔍 Analyse des collections existantes...")
        
        collections = await db.list_collection_names()
        
        for collection_name in collections:
            try:
                # Compter les documents
                count = await db[collection_name].count_documents({})
                
                # Lister les index existants
                indexes = await db[collection_name].list_indexes().to_list(None)
                index_count = len(indexes)
                
                logger.info(f"📊 {collection_name}: {count} documents, {index_count} index")
                
                # Analyser la taille de la collection
                stats = await db.command("collStats", collection_name)
                size_mb = stats.get("size", 0) / (1024 * 1024)
                logger.info(f"   Taille: {size_mb:.2f} MB")
                
            except Exception as e:
                logger.error(f"❌ Erreur analyse {collection_name}: {e}")
    
    async def optimize_performance(self):
        """Optimiser les performances générales."""
        logger.info("🚀 Optimisation des performances...")
        
        # Configurer les paramètres de performance
        try:
            # Augmenter la taille du cache
            await db.command("setParameter", 1, "cacheSizeGB", 1)
            logger.info("✅ Cache size configuré")
        except Exception as e:
            logger.warning(f"⚠️ Impossible de configurer le cache: {e}")
        
        # Vérifier les paramètres de performance
        try:
            server_status = await db.command("serverStatus")
            logger.info(f"📊 Version MongoDB: {server_status.get('version', 'Unknown')}")
            logger.info(f"📊 Uptime: {server_status.get('uptime', 0)} secondes")
        except Exception as e:
            logger.warning(f"⚠️ Impossible de récupérer le statut serveur: {e}")
    
    async def run(self):
        """Exécuter toutes les optimisations."""
        logger.info("🚀 Début de l'optimisation MongoDB...")
        
        try:
            # Analyser les collections existantes
            await self.analyze_collections()
            
            # Optimiser les index par module
            await self.optimize_chat_indexes()
            await self.optimize_cloudphone_indexes()
            await self.optimize_otp_indexes()
            await self.optimize_observability_indexes()
            await self.optimize_other_indexes()
            
            # Optimiser les performances
            await self.optimize_performance()
            
            logger.info(f"✅ Optimisation terminée! {self.indexes_created} index créés")
            
            # Générer un rapport
            await self.generate_report()
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'optimisation: {e}")
            raise
    
    async def generate_report(self):
        """Générer un rapport d'optimisation."""
        report = f"""
# Rapport d'optimisation MongoDB

## Résumé
- Index créés: {self.indexes_created}
- Collections traitées: {self.collections_processed}

## Index créés par module

### Chat
- conversation_id + timestamp
- user_id + timestamp
- platform + timestamp
- role + timestamp
- conversation_id + role + timestamp
- text (recherche)

### CloudPhone
- Profiles: org_id + name (unique), org_id + area, org_id + tags
- Devices: org_id + state, org_id + area, org_id + provider_ref (unique)
- App Accounts: org_id + app, org_id + username
- Slots: org_id + device_id + app, org_id + device_id + slot_index (unique)
- Bindings: org_id + slot_id (unique), org_id + app_account_id

### OTP
- org_id + state
- slot_id
- device_id
- app + country
- provider
- created_at, updated_at
- provider_session_id (unique)
- org_id + app + country
- org_id + state + created_at

### Observabilité
- Activity Logs: org_id + timestamp, org_id + scope + timestamp
- Alerts: org_id + created_at, org_id + status, org_id + alert_type

## Recommandations
1. Surveiller les performances avec MongoDB Compass
2. Analyser les requêtes lentes avec profiler
3. Ajuster les index selon l'usage réel
4. Nettoyer régulièrement les collections

## Prochaines étapes
1. Tester les performances
2. Monitorer les métriques
3. Ajuster si nécessaire
"""
        
        with open("MONGODB_OPTIMIZATION_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info("📄 Rapport généré: MONGODB_OPTIMIZATION_REPORT.md")


async def main():
    """Fonction principale."""
    optimizer = MongoDBIndexOptimizer()
    await optimizer.run()


if __name__ == "__main__":
    asyncio.run(main())



