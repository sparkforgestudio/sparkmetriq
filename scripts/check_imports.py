# scripts/check_imports.py
"""
Script pour vérifier tous les imports dans le codebase et identifier ceux qui échouent.
"""

import ast
import os
from pathlib import Path
from typing import List, Tuple

def find_python_files(root_dir: str = "api") -> List[Path]:
    """Trouve tous les fichiers Python dans le répertoire."""
    files = []
    for root, dirs, filenames in os.walk(root_dir):
        # Ignorer __pycache__ et venv
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'venv', '.venv', 'node_modules')]
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(Path(root) / filename)
    return files

def extract_imports(file_path: Path) -> List[Tuple[str, str]]:
    """Extrait tous les imports d'un fichier Python."""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, None))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append((module, alias.name))
    except Exception as e:
        # Ignorer les erreurs de parsing (fichiers corrompus, etc.)
        pass
    return imports

def check_import_exists(module: str, name: str = None) -> bool:
    """Vérifie si un import peut être résolu."""
    try:
        if name:
            # Import from module
            parts = module.split('.')
            if parts[0] == 'api':
                # Vérifier si le fichier existe
                file_path = Path('api') / '/'.join(parts[1:]) / '__init__.py'
                if file_path.exists():
                    return True
                file_path = Path('api') / '/'.join(parts[1:]) + '.py'
                if file_path.exists():
                    # Vérifier si le nom est exporté (simplifié)
                    return True
        else:
            # Import module
            parts = module.split('.')
            if parts[0] == 'api':
                file_path = Path('api') / '/'.join(parts[1:]) / '__init__.py'
                if file_path.exists():
                    return True
                file_path = Path('api') / '/'.join(parts[1:]) + '.py'
                return file_path.exists()
    except Exception:
        pass
    return False

def main():
    """Fonction principale."""
    print("🔍 Vérification des imports dans le codebase...\n")
    
    files = find_python_files()
    errors = []
    
    for file_path in files:
        imports = extract_imports(file_path)
        for module, name in imports:
            if module and module.startswith('api.'):
                if not check_import_exists(module, name):
                    errors.append((str(file_path), module, name))
    
    if errors:
        print(f"❌ {len(errors)} imports potentiellement problématiques trouvés:\n")
        for file_path, module, name in errors[:20]:  # Limiter à 20 pour l'affichage
            if name:
                print(f"  {file_path}: from {module} import {name}")
            else:
                print(f"  {file_path}: import {module}")
        if len(errors) > 20:
            print(f"\n  ... et {len(errors) - 20} autres")
    else:
        print("✅ Aucun import problématique trouvé!")
    
    return errors

if __name__ == "__main__":
    main()
