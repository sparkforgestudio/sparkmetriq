"""
Dépendances centralisées pour l'intégration de saasentialcore.

Ce module centralise les imports des services de saasentialcore pour faciliter
la migration progressive et l'utilisation future du module core générique.

⚠️ IMPORTANT : Ces imports sont préparés mais pas encore utilisés dans le code applicatif.
Ils seront activés progressivement lors de la migration vers saasentialcore.
"""

# Services de saasentialcore
# Note: Les services nécessitent une instance de base de données MongoDB
# qui sera injectée lors de l'utilisation réelle
from saasentialcore.services.auth_service import AuthService
from saasentialcore.services.scheduler_service import SchedulerService
from saasentialcore.services.quotas_service import QuotasService

# TODO: Lors de l'activation, créer des instances avec la base de données :
# from api.databases.databases import get_core_db
# 
# def get_saasentialcore_auth_service():
#     """Retourne une instance d'AuthService configurée."""
#     db = get_core_db()
#     return AuthService(db)
# 
# def get_saasentialcore_scheduler_service():
#     """Retourne une instance de SchedulerService configurée."""
#     db = get_core_db()
#     return SchedulerService(db)
# 
# def get_saasentialcore_quotas_service():
#     """Retourne une instance de QuotasService configurée."""
#     db = get_core_db()
#     return QuotasService(db)


