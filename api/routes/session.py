from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from fastapi import Response

router = APIRouter()

@router.get("/session", response_model=UserResponse)
async def get_session(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@router.post("/logout")
async def logout(response: Response):
    """
    Déconnexion : invalide le cookie/token du client (à gérer côté frontend).
    """
    # Option 1 : Pour un token dans un cookie sécurisé
    response.delete_cookie("access_token")

    # Option 2 : Pour un token envoyé dans Authorization (à traiter côté client)
    return {"message": "Déconnexion effectuée"}
