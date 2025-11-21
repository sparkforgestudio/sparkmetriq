# api/services/cloudphone/excel_import.py
"""
Import Excel optionnel pour les profils CloudPhone.
Fonctionnalité d'onboarding agence/mise à jour en masse.
"""

import base64
import io
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
from api.services.cloudphone.repository import (
    create_profile, update_profile, find_profile_by_name, ensure_cloudphone_indexes
)
from api.schemas.cloudphone import ProfileCreate, ProfileUpdate, ExcelImportResponse

async def import_profiles_xlsx(file_content: str, file_name: str, org_id: str, upsert_mode: bool = True) -> ExcelImportResponse:
    """
    Importer des profils depuis un fichier Excel.
    file_content: contenu du fichier encodé en base64
    """
    try:
        # Décoder le contenu base64
        file_bytes = base64.b64decode(file_content)
        
        # Lire le fichier Excel
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(file_bytes))
        elif file_name.endswith('.csv'):
            df = pd.read_csv(io.StringIO(file_bytes.decode('utf-8')))
        else:
            return ExcelImportResponse(
                ok=False,
                imported_count=0,
                updated_count=0,
                errors=[{"row": 0, "error": "Unsupported file format. Use .xlsx or .csv"}],
                summary={"error": "Invalid file format"}
            )
        
        # Valider les colonnes requises
        required_columns = ["name"]
        optional_columns = ["area", "lang", "proxy_template", "tags", "remark", "provider_ref"]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return ExcelImportResponse(
                ok=False,
                imported_count=0,
                updated_count=0,
                errors=[{"row": 0, "error": f"Missing required columns: {missing_columns}"}],
                summary={"error": "Missing required columns"}
            )
        
        # Traiter chaque ligne
        imported_count = 0
        updated_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Nettoyer les données
                profile_data = _clean_row_data(row, optional_columns)
                
                # Vérifier si le profil existe déjà
                existing_profile = await find_profile_by_name(org_id, profile_data["name"])
                
                if existing_profile and upsert_mode:
                    # Mettre à jour le profil existant
                    update_data = ProfileUpdate(**profile_data)
                    await update_profile(org_id, existing_profile.id, update_data)
                    updated_count += 1
                elif not existing_profile:
                    # Créer un nouveau profil
                    create_data = ProfileCreate(**profile_data)
                    await create_profile(org_id, create_data)
                    imported_count += 1
                else:
                    # Profil existe mais upsert_mode = False
                    errors.append({
                        "row": index + 2,  # +2 car Excel commence à 1 et on a l'en-tête
                        "error": f"Profile '{profile_data['name']}' already exists"
                    })
                    
            except Exception as e:
                errors.append({
                    "row": index + 2,
                    "error": str(e)
                })
        
        return ExcelImportResponse(
            ok=len(errors) == 0,
            imported_count=imported_count,
            updated_count=updated_count,
            errors=errors,
            summary={
                "total_rows": len(df),
                "imported": imported_count,
                "updated": updated_count,
                "errors": len(errors)
            }
        )
        
    except Exception as e:
        return ExcelImportResponse(
            ok=False,
            imported_count=0,
            updated_count=0,
            errors=[{"row": 0, "error": f"File processing error: {str(e)}"}],
            summary={"error": "File processing failed"}
        )

def _clean_row_data(row: pd.Series, optional_columns: List[str]) -> Dict[str, Any]:
    """Nettoyer les données d'une ligne."""
    data = {}
    
    # Colonne requise
    data["name"] = str(row["name"]).strip()
    
    # Colonnes optionnelles
    for col in optional_columns:
        if col in row and pd.notna(row[col]):
            if col == "tags":
                # Traiter les tags (peuvent être séparés par virgule)
                tags_str = str(row[col]).strip()
                if tags_str:
                    data[col] = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                else:
                    data[col] = []
            else:
                data[col] = str(row[col]).strip()
        else:
            if col == "tags":
                data[col] = []
            else:
                data[col] = None
    
    return data

async def generate_empty_template() -> str:
    """Générer un template Excel vide."""
    # Créer un DataFrame avec les colonnes du template
    template_data = {
        "name": ["Exemple Profil 1", "Exemple Profil 2"],
        "area": ["EU", "US"],
        "lang": ["fr-FR", "en-US"],
        "proxy_template": ["residential_fixed_eu_01", "residential_fixed_us_01"],
        "tags": ["cosplay,fitness", "gaming,tech"],
        "remark": ["Profil pour cosplay EU", "Profil pour gaming US"],
        "provider_ref": ["PROF001", "PROF002"]
    }
    
    df = pd.DataFrame(template_data)
    
    # Convertir en Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Profiles', index=False)
    
    # Encoder en base64
    template_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
    
    return template_base64

def get_template_info() -> Dict[str, Any]:
    """Récupérer les informations sur le template."""
    return {
        "columns": {
            "name": {
                "required": True,
                "description": "Nom du profil (unique par organisation)",
                "example": "Profil Cosplay EU"
            },
            "area": {
                "required": False,
                "description": "Zone géographique (EU, US, ASIA, etc.)",
                "example": "EU"
            },
            "lang": {
                "required": False,
                "description": "Langue du device (fr-FR, en-US, etc.)",
                "example": "fr-FR"
            },
            "proxy_template": {
                "required": False,
                "description": "Template de proxy à utiliser",
                "example": "residential_fixed_eu_01"
            },
            "tags": {
                "required": False,
                "description": "Tags séparés par virgule",
                "example": "cosplay,fitness,gaming"
            },
            "remark": {
                "required": False,
                "description": "Remarque sur le profil",
                "example": "Profil optimisé pour cosplay"
            },
            "provider_ref": {
                "required": False,
                "description": "Référence externe (depuis système existant)",
                "example": "PROF001"
            }
        },
        "rules": [
            "Le nom du profil doit être unique dans l'organisation",
            "Les tags doivent être séparés par des virgules",
            "Les zones supportées: EU, US, ASIA, LATAM",
            "Les langues supportées: fr-FR, en-US, es-ES, de-DE, etc.",
            "En mode upsert, les profils existants seront mis à jour"
        ],
        "limits": {
            "max_rows": 1000,
            "max_file_size": "10MB",
            "supported_formats": [".xlsx", ".csv"]
        }
    }

async def validate_import_file(file_content: str, file_name: str) -> Dict[str, Any]:
    """Valider un fichier d'import avant traitement."""
    try:
        # Décoder le contenu
        file_bytes = base64.b64decode(file_content)
        
        # Vérifier la taille du fichier (max 10MB)
        if len(file_bytes) > 10 * 1024 * 1024:
            return {
                "valid": False,
                "error": "File too large. Maximum size is 10MB."
            }
        
        # Lire le fichier pour vérifier la structure
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(file_bytes))
        elif file_name.endswith('.csv'):
            df = pd.read_csv(io.StringIO(file_bytes.decode('utf-8')))
        else:
            return {
                "valid": False,
                "error": "Unsupported file format. Use .xlsx or .csv"
            }
        
        # Vérifier les colonnes requises
        required_columns = ["name"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "valid": False,
                "error": f"Missing required columns: {missing_columns}"
            }
        
        # Vérifier le nombre de lignes
        if len(df) > 1000:
            return {
                "valid": False,
                "error": "Too many rows. Maximum is 1000 rows."
            }
        
        # Vérifier les noms vides
        empty_names = df["name"].isna().sum()
        if empty_names > 0:
            return {
                "valid": False,
                "error": f"Found {empty_names} rows with empty names"
            }
        
        return {
            "valid": True,
            "rows_count": len(df),
            "columns": list(df.columns),
            "sample_data": df.head(3).to_dict('records')
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": f"File validation error: {str(e)}"
        }

async def export_profiles_to_excel(org_id: str, filters: Optional[Dict[str, Any]] = None) -> str:
    """Exporter les profils vers Excel."""
    from api.services.cloudphone.repository import list_profiles
    from api.schemas.cloudphone import ProfileSearchParams
    
    # Récupérer tous les profils
    params = ProfileSearchParams(page=1, page_size=1000)
    if filters:
        if filters.get("search"):
            params.search = filters["search"]
        if filters.get("area"):
            params.area = filters["area"]
        if filters.get("tag"):
            params.tag = filters["tag"]
    
    profiles_response = await list_profiles(org_id, params)
    
    # Convertir en DataFrame
    profiles_data = []
    for profile in profiles_response.items:
        profiles_data.append({
            "name": profile.name,
            "area": profile.area or "",
            "lang": profile.lang or "",
            "proxy_template": profile.proxy_template or "",
            "tags": ",".join(profile.tags) if profile.tags else "",
            "remark": profile.remark or "",
            "provider_ref": profile.provider_ref or "",
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        })
    
    df = pd.DataFrame(profiles_data)
    
    # Convertir en Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Profiles', index=False)
    
    # Encoder en base64
    export_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
    
    return export_base64
