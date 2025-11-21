# api/services/messaging/template_engine.py
"""
Moteur de template Jinja2 sandboxé pour le Message Builder.
Fournit des filtres safe pour le rendu des messages personnalisés.
"""

from jinja2.sandbox import SandboxedEnvironment
from jinja2 import StrictUndefined
from datetime import datetime
from typing import Dict, Any, List, Tuple
import re


def _filters():
    """
    Retourne les filtres safe disponibles dans les templates.
    
    Returns:
        Dictionnaire de filtres
    """
    return {
        "upper": str.upper,
        "lower": str.lower,
        "title": str.title,
        "capitalize": str.capitalize,
        "date": lambda dt, fmt="%Y-%m-%d": (
            dt.strftime(fmt) if isinstance(dt, datetime) else str(dt)
        ),
        "default": lambda v, d="": (v if v not in (None, "") else d),
        "round": lambda v, n=0: (
            round(float(v), int(n)) if v is not None else None
        ),
        "strip": str.strip,
        "truncate": lambda s, length=50: (
            (s[:int(length)] + "...") if len(str(s)) > int(length) else str(s)
        ),
    }


def get_env():
    """
    Crée et retourne l'environnement Jinja2 sandboxé.
    
    Returns:
        SandboxedEnvironment configuré
    """
    env = SandboxedEnvironment(
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True
    )
    env.filters.update(_filters())
    return env


def render_template(body: str, variables: Dict[str, Any]) -> str:
    """
    Rend un template avec les variables fournies.
    
    Args:
        body: Corps du template (syntaxe Jinja2)
        variables: Dictionnaire de variables
        
    Returns:
        Template rendu
        
    Raises:
        Exception: Si erreur de rendu (variable manquante, etc.)
    """
    env = get_env()
    tmpl = env.from_string(body)
    return tmpl.render(**variables)


def validate_template(body: str, allow_links: bool = True) -> Tuple[bool, str]:
    """
    Valide un template (vérifie la syntaxe et les liens).
    
    Args:
        body: Corps du template
        allow_links: Autoriser les liens http/https
        
    Returns:
        Tuple (valide, message_erreur)
    """
    try:
        env = get_env()
        env.parse(body)
    except Exception as e:
        return False, f"Template syntax error: {str(e)}"
    
    # Vérifier les liens si non autorisés
    if not allow_links:
        link_pattern = r'https?://[^\s]+'
        if re.search(link_pattern, body):
            return False, "Links (http/https) are not allowed in templates"
    
    return True, ""


def extract_variables(body: str) -> List[str]:
    """
    Extrait les variables utilisées dans un template.
    
    Args:
        body: Corps du template
        
    Returns:
        Liste des noms de variables
    """
    import re
    # Pattern pour trouver {{ variable }} ou {{ variable|filter }}
    pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'
    matches = re.findall(pattern, body)
    # Dédupliquer et nettoyer
    variables = list(set(matches))
    return variables
