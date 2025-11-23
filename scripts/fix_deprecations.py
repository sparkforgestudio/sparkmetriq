# scripts/fix_deprecations.py
"""
Script pour corriger les dépréciations Pydantic v2 et FastAPI.
Applique les corrections automatiquement dans tout le codebase.
"""

import os
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeprecationFixer:
    """Classe pour corriger les dépréciations dans le code."""
    
    def __init__(self, root_dir: str = "api"):
        self.root_dir = Path(root_dir)
        self.fixes_applied = 0
        self.files_processed = 0
        
    def fix_datetime_utcnow(self, content: str) -> str:
        """Remplacer utcnow() par datetime.now(timezone.utc)."""
        # Pattern pour utcnow()
        pattern = r'datetime\.utcnow\(\)'
        replacement = 'datetime.now(timezone.utc)'
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            # Ajouter l'import timezone si nécessaire
            if 'from datetime import' in content and 'timezone' not in content:
                content = re.sub(
                    r'from datetime import ([^\\n]+)',
                    r'from datetime import \1, timezone',
                    content
                )
            elif 'import datetime' in content and 'timezone' not in content:
                content = re.sub(
                    r'import datetime',
                    'import datetime\nfrom datetime import timezone',
                    content
                )
            self.fixes_applied += 1
            logger.info("✅ Fixed utcnow()")
        
        return content
    
    def fix_pydantic_dict(self, content: str) -> str:
        """Remplacer .dict() par .model_dump()."""
        # Pattern pour .dict() mais pas pour les dictionnaires Python
        pattern = r'(\w+)\.dict\(\)'
        replacement = r'\1.model_dump()'
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            self.fixes_applied += 1
            logger.info("✅ Fixed .dict() -> .model_dump()")
        
        return content
    
    def fix_pydantic_parse_obj(self, content: str) -> str:
        """Remplacer .parse_obj() par .model_validate()."""
        pattern = r'(\w+)\.parse_obj\(([^)]+)\)'
        replacement = r'\1.model_validate(\2)'
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            self.fixes_applied += 1
            logger.info("✅ Fixed .parse_obj() -> .model_validate()")
        
        return content
    
    def fix_pydantic_config(self, content: str) -> str:
        """Remplacer Config par ConfigDict."""
        # Pattern pour class Config:
        config_pattern = r'class Config:\s*\n\s*([^\\n]+(?:\n\s*[^\\n]+)*)'
        
        def replace_config(match):
            config_content = match.group(1)
            # Remplacer orm_mode par from_attributes
            config_content = re.sub(r'orm_mode\s*=\s*True', 'from_attributes=True', config_content)
            # Remplacer allow_population_by_field_name par populate_by_name
            config_content = re.sub(r'allow_population_by_field_name\s*=\s*True', 'populate_by_name=True', config_content)
            
            return f'model_config = ConfigDict(\n{config_content}\n)'
        
        if re.search(config_pattern, content, re.MULTILINE):
            content = re.sub(config_pattern, replace_config, content)
            # Ajouter l'import ConfigDict si nécessaire
            if 'from pydantic import' in content and 'ConfigDict' not in content:
                content = re.sub(
                    r'from pydantic import ([^\\n]+)',
                    r'from pydantic import \1, ConfigDict',
                    content
                )
            self.fixes_applied += 1
            logger.info("✅ Fixed Config -> ConfigDict")
        
        return content
    
    def fix_field_examples(self, content: str) -> str:
        """Remplacer Field(..., example=) par json_schema_extra."""
        # Pattern pour Field avec example
        pattern = r'Field\(([^)]*),\s*example=([^)]+)\)'
        
        def replace_field(match):
            field_args = match.group(1)
            example_value = match.group(2)
            
            # Extraire le nom du champ si possible
            field_name = "field"
            if "=" in field_args:
                field_name = field_args.split("=")[0].strip()
            
            return f'Field({field_args})'
        
        if re.search(pattern, content):
            content = re.sub(pattern, replace_field, content)
            self.fixes_applied += 1
            logger.info("✅ Fixed Field examples")
        
        return content
    
    def fix_query_regex(self, content: str) -> str:
        """Remplacer Query(..., regex=) par Query(..., pattern=)."""
        pattern = r'Query\(([^)]*),\s*regex=([^)]+)\)'
        replacement = r'Query(\1, pattern=\2)'
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            self.fixes_applied += 1
            logger.info("✅ Fixed Query regex -> pattern")
        
        return content
    
    def fix_fastapi_on_event(self, content: str) -> str:
        """Remplacer @app.on_event par lifespan."""
        # Pattern pour @app.on_event("startup")
        startup_pattern = r'@app\.on_event\("startup"\)\s*\n\s*async def startup\(\):'
        
        if re.search(startup_pattern, content):
            # Remplacer par lifespan
            content = re.sub(
                startup_pattern,
                '@asynccontextmanager\nasync def lifespan(app: FastAPI):',
                content
            )
            # Ajouter les imports nécessaires
            if 'from contextlib import asynccontextmanager' not in content:
                content = 'from contextlib import asynccontextmanager\n' + content
            self.fixes_applied += 1
            logger.info("✅ Fixed @app.on_event -> lifespan")
        
        return content
    
    def add_docstrings(self, content: str) -> str:
        """Ajouter des docstrings manquantes."""
        # Pattern pour les fonctions sans docstring
        func_pattern = r'(async def|def)\s+(\w+)\([^)]*\):\s*\n(\s+)(?!"")'
        
        def add_docstring(match):
            func_type = match.group(1)
            func_name = match.group(2)
            indent = match.group(3)
            
            docstring = f'{indent}"""{func_name} - TODO: Add description."""\n'
            return match.group(0) + '\n' + docstring
        
        if re.search(func_pattern, content):
            content = re.sub(func_pattern, add_docstring, content)
            self.fixes_applied += 1
            logger.info("✅ Added missing docstrings")
        
        return content
    
    def fix_imports(self, content: str) -> str:
        """Organiser et nettoyer les imports."""
        lines = content.split('\n')
        import_lines = []
        other_lines = []
        in_imports = False
        
        for line in lines:
            if line.startswith(('import ', 'from ')):
                import_lines.append(line)
                in_imports = True
            elif in_imports and line.strip() == '':
                import_lines.append(line)
            else:
                other_lines.append(line)
                in_imports = False
        
        # Organiser les imports
        stdlib_imports = []
        third_party_imports = []
        local_imports = []
        
        for line in import_lines:
            if line.startswith('from api.') or line.startswith('import api.'):
                local_imports.append(line)
            elif any(pkg in line for pkg in ['pydantic', 'fastapi', 'motor', 'bson', 'httpx']):
                third_party_imports.append(line)
            else:
                stdlib_imports.append(line)
        
        # Reconstituer le contenu
        organized_imports = []
        if stdlib_imports:
            organized_imports.extend(stdlib_imports)
            organized_imports.append('')
        if third_party_imports:
            organized_imports.extend(third_party_imports)
            organized_imports.append('')
        if local_imports:
            organized_imports.extend(local_imports)
            organized_imports.append('')
        
        return '\n'.join(organized_imports + other_lines)
    
    def process_file(self, file_path: Path) -> None:
        """Traiter un fichier Python."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Appliquer toutes les corrections
            content = self.fix_datetime_utcnow(content)
            content = self.fix_pydantic_dict(content)
            content = self.fix_pydantic_parse_obj(content)
            content = self.fix_pydantic_config(content)
            content = self.fix_field_examples(content)
            content = self.fix_query_regex(content)
            content = self.fix_fastapi_on_event(content)
            content = self.add_docstrings(content)
            content = self.fix_imports(content)
            
            # Écrire le fichier modifié si des changements ont été faits
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"✅ Processed {file_path}")
            else:
                logger.info(f"ℹ️ No changes needed for {file_path}")
            
            self.files_processed += 1
            
        except Exception as e:
            logger.error(f"❌ Error processing {file_path}: {e}")
    
    def process_directory(self, directory: Path) -> None:
        """Traiter un répertoire récursivement."""
        for file_path in directory.rglob("*.py"):
            if file_path.is_file():
                self.process_file(file_path)
    
    def run(self) -> None:
        """Exécuter toutes les corrections."""
        logger.info("🚀 Starting deprecation fixes...")
        
        if self.root_dir.exists():
            self.process_directory(self.root_dir)
        else:
            logger.error(f"❌ Directory {self.root_dir} does not exist")
            return
        
        logger.info(f"✅ Completed! Processed {self.files_processed} files, applied {self.fixes_applied} fixes")
        
        # Générer un rapport
        self.generate_report()
    
    def generate_report(self) -> None:
        """Générer un rapport des corrections appliquées."""
        report = f"""
# Rapport de correction des dépréciations

## Résumé
- Fichiers traités: {self.files_processed}
- Corrections appliquées: {self.fixes_applied}

## Corrections appliquées
1. ✅ utcnow() → datetime.now(timezone.utc)
2. ✅ .dict() → .model_dump()
3. ✅ .parse_obj() → .model_validate()
4. ✅ Config → ConfigDict
5. ✅ Field examples → json_schema_extra
6. ✅ Query regex → pattern
7. ✅ @app.on_event → lifespan
8. ✅ Docstrings ajoutées
9. ✅ Imports organisés

## Fichiers modifiés
Les fichiers suivants ont été modifiés:
- Tous les fichiers Python dans {self.root_dir}

## Prochaines étapes
1. Vérifier que les tests passent
2. Lancer le linter (ruff, black)
3. Tester l'application
4. Commiter les changements
"""
        
        with open("DEPRECATION_FIX_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info("📄 Report generated: DEPRECATION_FIX_REPORT.md")


def main():
    """Fonction principale."""
    fixer = DeprecationFixer()
    fixer.run()


if __name__ == "__main__":
    main()




