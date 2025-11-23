# api/utils/responses.py
"""
Utilitaires pour les réponses API normalisées.
Standardise les formats de réponse pour la cohérence.
"""

from typing import Any, Dict, Optional, List, Union
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timezone


class SuccessResponse(BaseModel):
    """Réponse de succès standardisée."""
    
    success: bool = True
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "message": "Operation completed successfully",
                    "data": {"id": "507f1f77bcf86cd799439011"},
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            ]
        }


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée."""
    
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": "Validation error",
                    "details": {"field": "name", "message": "Field is required"},
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            ]
        }


class PaginatedResponse(BaseModel):
    """Réponse paginée standardisée."""
    
    success: bool = True
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "items": [{"id": "1", "name": "Item 1"}],
                    "total": 100,
                    "page": 1,
                    "page_size": 25,
                    "total_pages": 4,
                    "has_next": True,
                    "has_prev": False,
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            ]
        }


def create_success_response(
    message: str,
    data: Optional[Any] = None,
    status_code: int = 200
) -> JSONResponse:
    """
    Créer une réponse de succès standardisée.
    
    Args:
        message: Message de succès
        data: Données à retourner
        status_code: Code de statut HTTP
        
    Returns:
        JSONResponse standardisée
    """
    response_data = SuccessResponse(
        message=message,
        data=data
    )
    return JSONResponse(
        content=response_data.model_dump(),
        status_code=status_code
    )


def create_error_response(
    error: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400
) -> JSONResponse:
    """
    Créer une réponse d'erreur standardisée.
    
    Args:
        error: Message d'erreur
        details: Détails de l'erreur
        status_code: Code de statut HTTP
        
    Returns:
        JSONResponse standardisée
    """
    response_data = ErrorResponse(
        error=error,
        details=details
    )
    return JSONResponse(
        content=response_data.model_dump(),
        status_code=status_code
    )


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    status_code: int = 200
) -> JSONResponse:
    """
    Créer une réponse paginée standardisée.
    
    Args:
        items: Liste des éléments
        total: Nombre total d'éléments
        page: Page actuelle
        page_size: Taille de la page
        status_code: Code de statut HTTP
        
    Returns:
        JSONResponse paginée
    """
    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1
    
    response_data = PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )
    return JSONResponse(
        content=response_data.model_dump(),
        status_code=status_code
    )


def raise_http_exception(
    status_code: int,
    detail: str,
    headers: Optional[Dict[str, str]] = None
) -> None:
    """
    Lever une exception HTTP standardisée.
    
    Args:
        status_code: Code de statut HTTP
        detail: Détail de l'erreur
        headers: En-têtes HTTP optionnels
        
    Raises:
        HTTPException
    """
    raise HTTPException(
        status_code=status_code,
        detail=detail,
        headers=headers
    )


def raise_validation_error(
    field: str,
    message: str,
    value: Optional[Any] = None
) -> None:
    """
    Lever une erreur de validation standardisée.
    
    Args:
        field: Nom du champ
        message: Message d'erreur
        value: Valeur qui a causé l'erreur
        
    Raises:
        HTTPException avec code 422
    """
    details = {
        "field": field,
        "message": message
    }
    if value is not None:
        details["value"] = str(value)
    
    raise HTTPException(
        status_code=422,
        detail=f"Validation error: {message}",
        headers={"X-Error-Details": str(details)}
    )


def raise_not_found_error(
    resource_type: str,
    resource_id: str
) -> None:
    """
    Lever une erreur de ressource non trouvée.
    
    Args:
        resource_type: Type de ressource
        resource_id: ID de la ressource
        
    Raises:
        HTTPException avec code 404
    """
    raise HTTPException(
        status_code=404,
        detail=f"{resource_type} with id '{resource_id}' not found"
    )


def raise_conflict_error(
    resource_type: str,
    field: str,
    value: str
) -> None:
    """
    Lever une erreur de conflit (ressource déjà existante).
    
    Args:
        resource_type: Type de ressource
        field: Champ en conflit
        value: Valeur en conflit
        
    Raises:
        HTTPException avec code 409
    """
    raise HTTPException(
        status_code=409,
        detail=f"{resource_type} with {field} '{value}' already exists"
    )


def raise_forbidden_error(
    action: str,
    resource: str
) -> None:
    """
    Lever une erreur d'accès interdit.
    
    Args:
        action: Action tentée
        resource: Ressource concernée
        
    Raises:
        HTTPException avec code 403
    """
    raise HTTPException(
        status_code=403,
        detail=f"Access forbidden: cannot {action} {resource}"
    )


def raise_unauthorized_error(
    reason: str = "Invalid credentials"
) -> None:
    """
    Lever une erreur d'authentification.
    
    Args:
        reason: Raison de l'erreur
        
    Raises:
        HTTPException avec code 401
    """
    raise HTTPException(
        status_code=401,
        detail=f"Unauthorized: {reason}"
    )


def raise_server_error(
    operation: str,
    details: Optional[str] = None
) -> None:
    """
    Lever une erreur serveur interne.
    
    Args:
        operation: Opération qui a échoué
        details: Détails de l'erreur
        
    Raises:
        HTTPException avec code 500
    """
    message = f"Internal server error during {operation}"
    if details:
        message += f": {details}"
    
    raise HTTPException(
        status_code=500,
        detail=message
    )


# Constantes pour les codes de statut HTTP
class HTTPStatus:
    """Codes de statut HTTP standardisés."""
    
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503


# Constantes pour les messages d'erreur
class ErrorMessages:
    """Messages d'erreur standardisés."""
    
    VALIDATION_ERROR = "Validation error"
    NOT_FOUND = "Resource not found"
    CONFLICT = "Resource already exists"
    FORBIDDEN = "Access forbidden"
    UNAUTHORIZED = "Unauthorized access"
    SERVER_ERROR = "Internal server error"
    TIMEOUT = "Operation timeout"
    RATE_LIMIT = "Rate limit exceeded"
    QUOTA_EXCEEDED = "Quota exceeded"
    INVALID_TOKEN = "Invalid or expired token"
    MISSING_PERMISSIONS = "Missing required permissions"




