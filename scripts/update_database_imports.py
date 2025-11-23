# scripts/update_database_imports.py
"""
Script pour mettre à jour automatiquement les imports de base de données
selon le type de service (Core vs BI).
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set


# Collections par base de données
CORE_COLLECTIONS = {
    'users', 'profiles', 'devices', 'device_app_slots', 'bindings_appaccount_slot',
    'otp_sessions', 'org_entitlements', 'chat_messages', 'payments',
    'tunnels', 'ppv_logs', 'conversation_daily', 'revenue_daily', 'ppv_daily',
    'auth_tokens', 'password_resets', 'user_sessions'
}

BI_COLLECTIONS = {
    'events_funnel', 'scheduled_drafts', 'scheduled_jobs', 'publish_logs',
    'ab_tests', 'recycle_policies', 'ai_action_plans', 'ai_alerts',
    'ai_collab_suggestions', 'ai_reco_history', 'trends_cache',
    'chat_threads', 'fan_tags', 'fan_notes', 'operator_roles',
    'muse_assignments', 'audit_events', 'muse_metrics_daily',
    'integration_hooks', 'rag_documents', 'rag_embeddings', 'vector_index',
    'scraped_contents', 'creator_analytics', 'platform_metrics',
    'funnel_events', 'conversation_metrics', 'revenue_metrics'
}

# Services par type
CORE_SERVICES = {
    'auth', 'users', 'payments', 'cloudphone', 'otp', 'chat_omnichannel',
    'tunnels', 'ppv', 'webhooks'
}

BI_SERVICES = {
    'analytics', 'assistant', 'scheduler', 'talent', 'ai_marketing',
    'logs', 'stats', 'funnel', 'forecast', 'conversation_service',
    'tunnel_analysis', 'activity_logger', 'funnel_config'
}


def determine_db_type(file_path: Path) -> str:
    """
    Détermine si un fichier doit utiliser la base Core ou BI.
    
    Args:
        file_path: Chemin du fichier
        
    Returns:
        'core' ou 'bi'
    """
    path_str = str(file_path)
    
    # Vérifier par service
    for service in CORE_SERVICES:
        if f'/services/{service}/' in path_str or f'/routes/{service}' in path_str:
            return 'core'
    
    for service in BI_SERVICES:
        if f'/services/{service}/' in path_str or f'/routes/{service}' in path_str:
            return 'bi'
    
    # Vérifier par collection utilisée dans le fichier
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chercher les collections utilisées
        collections_used = set()
        for collection in CORE_COLLECTIONS | BI_COLLECTIONS:
            if f"['{collection}']" in content or f'["{collection}"]' in content:
                collections_used.add(collection)
        
        # Déterminer selon les collections
        core_count = len(collections_used & CORE_COLLECTIONS)
        bi_count = len(collections_used & BI_COLLECTIONS)
        
        if bi_count > core_count:
            return 'bi'
        else:
            return 'core'
            
    except Exception:
        # Par défaut, utiliser Core
        return 'core'


def update_file_imports(file_path: Path, db_type: str) -> bool:
    """
    Met à jour les imports de base de données dans un fichier.
    
    Args:
        file_path: Chemin du fichier
        db_type: 'core' ou 'bi'
        
    Returns:
        True si le fichier a été modifié
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remplacer l'import
        old_import = "from api.databases.databases import db"
        if db_type == 'core':
            new_import = "from api.databases.databases import get_core_db\n\n# Utiliser la base Core\ndb = get_core_db()"
        else:
            new_import = "from api.databases.databases import get_bi_db\n\n# Utiliser la base BI\ndb = get_bi_db()"
        
        if old_import in content:
            content = content.replace(old_import, new_import)
        
        # Écrire le fichier modifié
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Erreur traitement {file_path}: {e}")
        return False


def main():
    """Fonction principale."""
    print("🔄 Mise à jour des imports de base de données...")
    
    # Parcourir tous les fichiers Python
    api_dir = Path("api")
    updated_files = []
    
    for py_file in api_dir.rglob("*.py"):
        if py_file.name.startswith('__'):
            continue
        
        # Déterminer le type de base
        db_type = determine_db_type(py_file)
        
        # Mettre à jour le fichier
        if update_file_imports(py_file, db_type):
            updated_files.append((py_file, db_type))
            print(f"✅ {py_file} -> {db_type.upper()}")
    
    print(f"\n📊 Résumé:")
    print(f"  Fichiers modifiés: {len(updated_files)}")
    
    core_count = sum(1 for _, db_type in updated_files if db_type == 'core')
    bi_count = sum(1 for _, db_type in updated_files if db_type == 'bi')
    
    print(f"  Base Core: {core_count} fichiers")
    print(f"  Base BI: {bi_count} fichiers")
    
    print("\n✅ Mise à jour terminée!")


if __name__ == "__main__":
    main()




