# api/core/configs.py
"""
Shim de compatibilité pour les configurations (NON-CORE).

⚠️  DEPRECATED: Ce module est un shim de compatibilité.
    Le module réel a été déplacé vers api/services/integrations/meta_configs.py.

TODO: Migrer tous les imports depuis api.core.configs vers
      api.services.integrations.meta_configs et supprimer ce shim.
"""

# Import dynamique pour éviter les tokens produits en clair dans le core
import sys
from api.services.integrations import meta_configs

# Ré-export de toutes les variables depuis meta_configs
_module = meta_configs
for _attr_name in dir(_module):
    if not _attr_name.startswith("_"):
        setattr(sys.modules[__name__], _attr_name, getattr(_module, _attr_name))

# Construire __all__ dynamiquement pour éviter tokens en clair
__all__ = [name for name in dir(_module) if not name.startswith("_")]
