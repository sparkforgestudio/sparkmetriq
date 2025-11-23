# scripts/add_entitlement_checks.py
"""
Script pour ajouter automatiquement les vérifications d'entitlement dans tous les endpoints.
À exécuter après avoir ajouté les helpers check_cloudphone_entitlement et check_otp_entitlement.
"""

import re
from pathlib import Path


def add_entitlement_check_to_file(file_path: Path, check_function: str):
    """
    Ajoute la vérification d'entitlement au début de chaque endpoint dans un fichier.
    
    Args:
        file_path: Chemin du fichier à modifier
        check_function: Nom de la fonction de vérification (check_cloudphone_entitlement ou check_otp_entitlement)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour trouver les définitions de fonctions async avec current_user
    pattern = r'(@router\.\w+\([^)]*\)\s*\n\s*async def \w+\([^)]*current_user[^)]*\):\s*\n\s*"""[^"]*"""\s*\n)'
    
    def add_check(match):
        func_def = match.group(1)
        # Ajouter la vérification après la docstring
        check_line = f"    # Vérifier l'entitlement\n    await {check_function}(current_user)\n\n    "
        return func_def + check_line
    
    new_content = re.sub(pattern, add_check, content)
    
    # Si le contenu a changé, l'écrire
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Modifié: {file_path}")
        return True
    else:
        print(f"ℹ️ Aucun changement: {file_path}")
        return False


def main():
    """Fonction principale."""
    print("🚀 Ajout des vérifications d'entitlement...")
    
    # CloudPhone routes
    cloudphone_file = Path("api/routes/cloudphone.py")
    if cloudphone_file.exists():
        add_entitlement_check_to_file(cloudphone_file, "check_cloudphone_entitlement")
    
    # OTP routes
    otp_file = Path("api/routes/otp.py")
    if otp_file.exists():
        add_entitlement_check_to_file(otp_file, "check_otp_entitlement")
    
    print("✅ Terminé!")


if __name__ == "__main__":
    main()




