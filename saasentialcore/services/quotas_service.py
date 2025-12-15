"""
Service de gestion des quotas pour saasentialcore.

Ce module gère la logique métier des quotas :
- Récupération et création de quotas d'organisation
- Mise à jour de l'utilisation
- Reset quotidien des compteurs
- Incrémentation/décrémentation des compteurs

Note: Ce service a été extrait d'une implémentation produit historique pour être
partagé avec d'autres applications consommatrices.
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from saasentialcore.models.schemas.quotas_schema import OrgQuotas, OrgLimits, OrgUsage, OrgQuotasUpdate
from saasentialcore.models.db.quotas import QuotasDB


class QuotasService:
    """
    Service de gestion des quotas.
    
    Gère la création, récupération et mise à jour des quotas dans MongoDB.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialise le service de quotas.
        
        Args:
            db: Base de données MongoDB
        """
        self.db = db
        self.collection = db["org_quotas"]
    
    async def _update_one_compat(
        self,
        collection,
        filter_doc: Dict[str, Any],
        update_doc: Dict[str, Any],
        upsert: bool = False,
    ) -> None:
        """
        Compatibilité Motor/PyMongo et FakeCollection (tests).
        
        Certains doubles (FakeCollection) n'acceptent pas les kwargs.
        """
        try:
            await collection.update_one(filter_doc, update_doc, upsert=upsert)
        except TypeError:
            await collection.update_one(filter_doc, update_doc)
    
    async def get_or_create_org_quotas(self, org_id: str) -> OrgQuotas:
        """
        Récupère les quotas d'une organisation ou les crée avec les valeurs par défaut.
        
        Args:
            org_id: Identifiant de l'organisation
        
        Returns:
            OrgQuotas avec les quotas de l'organisation
        """
        doc = await self.collection.find_one({"org_id": org_id})
        
        if doc:
            # Convertir le document MongoDB en OrgQuotas
            if "last_reset" in doc.get("usage", {}) and doc["usage"]["last_reset"]:
                # Convertir string ISO en date si nécessaire
                if isinstance(doc["usage"]["last_reset"], str):
                    doc["usage"]["last_reset"] = date.fromisoformat(doc["usage"]["last_reset"])
            
            return OrgQuotas(**doc)
        else:
            # Créer un nouveau document avec les valeurs par défaut
            quotas = OrgQuotas(org_id=org_id)
            await self.update_org_quotas(quotas)
            return quotas
    
    async def update_org_quotas(self, quotas: OrgQuotas) -> None:
        """
        Met à jour (upsert) les quotas d'une organisation.
        
        Args:
            quotas: Objet OrgQuotas à sauvegarder
        """
        quotas.updated_at = datetime.now(timezone.utc)
        doc = quotas.model_dump()
        
        # Convertir date en string ISO pour MongoDB
        if doc.get("usage", {}).get("last_reset"):
            doc["usage"]["last_reset"] = doc["usage"]["last_reset"].isoformat() if isinstance(doc["usage"]["last_reset"], date) else doc["usage"]["last_reset"]
        
        await self._update_one_compat(
            self.collection,
            {"org_id": quotas.org_id},
            {"$set": doc},
            upsert=True,
        )
    
    async def increment_scheduled_posts(self, org_id: str, delta: int = 1) -> OrgQuotas:
        """
        Incrémente le compteur de posts planifiés.
        
        Args:
            org_id: Identifiant de l'organisation
            delta: Valeur d'incrémentation (peut être négatif)
        
        Returns:
            OrgQuotas mis à jour
        """
        quotas = await self.get_or_create_org_quotas(org_id)
        quotas.usage.scheduled_posts = max(0, quotas.usage.scheduled_posts + delta)
        quotas.updated_at = datetime.now(timezone.utc)
        await self.update_org_quotas(quotas)
        return quotas
    
    async def increment_published_today(self, org_id: str, delta: int = 1) -> OrgQuotas:
        """
        Incrémente le compteur de posts publiés aujourd'hui.
        
        Args:
            org_id: Identifiant de l'organisation
            delta: Valeur d'incrémentation (peut être négatif)
        
        Returns:
            OrgQuotas mis à jour
        """
        quotas = await self.get_or_create_org_quotas(org_id)
        quotas = await self.reset_daily_usage_if_needed(quotas)
        quotas.usage.published_today = max(0, quotas.usage.published_today + delta)
        quotas.updated_at = datetime.now(timezone.utc)
        await self.update_org_quotas(quotas)
        return quotas
    
    async def reset_daily_usage_if_needed(self, quotas: OrgQuotas) -> OrgQuotas:
        """
        Remet published_today à zéro si la date a changé.
        
        Args:
            quotas: Objet OrgQuotas à vérifier
        
        Returns:
            OrgQuotas mis à jour si nécessaire
        """
        today = date.today()
        
        if quotas.usage.last_reset != today:
            quotas.usage.published_today = 0
            quotas.usage.last_reset = today
            quotas.updated_at = datetime.now(timezone.utc)
            await self.update_org_quotas(quotas)
        
        return quotas
    
    async def list_all_org_quotas(self) -> List[Dict[str, Any]]:
        """
        Liste tous les quotas de toutes les organisations.
        
        Returns:
            Liste de dictionnaires contenant les quotas de chaque organisation
        """
        cursor = self.collection.find({}).sort("org_id", 1)
        docs = await cursor.to_list(length=None)
        
        # Convertir les documents en list de dicts
        results = []
        for doc in docs:
            # Convertir last_reset si présent
            if "usage" in doc and "last_reset" in doc["usage"] and doc["usage"]["last_reset"]:
                if isinstance(doc["usage"]["last_reset"], str):
                    try:
                        doc["usage"]["last_reset"] = date.fromisoformat(doc["usage"]["last_reset"])
                    except ValueError:
                        doc["usage"]["last_reset"] = None
            
            results.append(doc)
        
        return results
    
    async def update_quotas_limits(self, org_id: str, quotas_update: OrgQuotasUpdate) -> OrgQuotas:
        """
        Met à jour les limites de quotas d'une organisation.
        
        Args:
            org_id: Identifiant de l'organisation
            quotas_update: Données de quotas à mettre à jour
        
        Returns:
            OrgQuotas mis à jour
        """
        quotas = await self.get_or_create_org_quotas(org_id)
        
        # Mise à jour des limites uniquement
        if quotas_update.max_scheduled_posts is not None:
            quotas.limits.max_scheduled_posts = quotas_update.max_scheduled_posts
        
        if quotas_update.max_published_per_day is not None:
            quotas.limits.max_published_per_day = quotas_update.max_published_per_day
        
        if quotas_update.max_platforms_per_post is not None:
            quotas.limits.max_platforms_per_post = quotas_update.max_platforms_per_post
        
        quotas.updated_at = datetime.now(timezone.utc)
        await self.update_org_quotas(quotas)
        return quotas
