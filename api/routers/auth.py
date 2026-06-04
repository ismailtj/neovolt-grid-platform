from pydantic import BaseModel
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import APP_ENV, authenticate_user, create_access_token, register_user
from db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


def _assert_registration_allowed() -> None:
    if APP_ENV == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled in production.",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtenir un token JWT",
    description="Authentifie l'utilisateur et renvoie un token JWT pour accéder aux routes protégées.",
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/register",
    response_class=HTMLResponse,
    summary="Formulaire d'inscription de test",
    description="Affiche un formulaire HTML simple pour créer un compte utilisateur de test en mode développement.",
)
def register_form():
    _assert_registration_allowed()
    return HTMLResponse(
        """
        <html>
            <head>
                <title>Register User</title>
            </head>
            <body>
                <h1>Register a new user</h1>
                <form action="/auth/register" method="post">
                    <label>Username:</label><br>
                    <input type="text" name="username" required /><br><br>
                    <label>Password:</label><br>
                    <input type="password" name="password" required /><br><br>
                    <button type="submit">Register</button>
                </form>
            </body>
        </html>
        """
    )


@router.post(
    "/register",
    summary="Enregistrer un utilisateur de test",
    description="Enregistre un nouvel utilisateur en mode développement. Cette route est désactivée en production.",
)
def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    _assert_registration_allowed()
    if not register_user(username, password, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists.",
        )
    return {"username": username, "status": "registered"}
