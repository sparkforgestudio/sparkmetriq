# api/routes/redirect.py
"""
Route publique de redirection pour les liens courts /r/{code}.
"""

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from typing import Optional

from api.services.tracking.redirect_service import resolve_and_log

router = APIRouter()


@router.get("/r/{code}")
async def redirect(
    code: str,
    request: Request,
    u: Optional[str] = Query(None, description="User ref (optionnel)")
):
    """
    Redirige vers l'URL de destination et log le clic.
    
    Args:
        code: Code du lien court
        request: Requête HTTP
        u: Référence utilisateur (optionnel)
        
    Returns:
        RedirectResponse vers la destination
        
    Raises:
        HTTPException: 404 si lien non trouvé, 410 si expiré/quota atteint
    """
    try:
        # Extraire les informations de la requête
        ip = request.client.host if request.client else ""
        ua = request.headers.get("user-agent", "")
        ref = request.headers.get("referer", "")
        
        # Extraire les paramètres de query
        q = dict(request.query_params)
        
        # Résoudre le lien et logger le clic
        dest = await resolve_and_log(
            code=code,
            user_ref=u,
            ip=ip,
            ua=ua,
            ref=ref,
            q=q
        )
        
        # Rediriger vers la destination
        return RedirectResponse(url=dest, status_code=302)
        
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Link not found"
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=410,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )




