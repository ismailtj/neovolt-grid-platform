import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import MetaData, Table, select, insert
from sqlalchemy.orm import Session

from db import SessionLocal, engine, get_db

project_root = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=project_root / ".env")

APP_ENV = os.getenv("APP_ENV", "development").lower()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_this_secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

metadata = MetaData()
users_table = Table("users", metadata, autoload_with=engine)


def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# These credentials are used for prototype/demo only.
# For production, replace with a user store or identity provider.
DEFAULT_AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
DEFAULT_AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "admin123")
DEFAULT_AUTH_PASSWORD_HASH = get_password_hash(DEFAULT_AUTH_PASSWORD)


def get_user(username: str, db: Session) -> Optional[str]:
    stmt = select(users_table.c.password_hash).where(users_table.c.username == username)
    return db.execute(stmt).scalar_one_or_none()


def register_user(username: str, password: str, db: Session) -> bool:
    if get_user(username, db) is not None:
        return False
    stmt = insert(users_table).values(
        username=username,
        password_hash=get_password_hash(password),
    )
    db.execute(stmt)
    db.commit()
    return True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password


def authenticate_user(username: str, password: str, db: Session) -> Optional[str]:
    hashed_password = get_user(username, db)
    if hashed_password is None:
        return None
    if not verify_password(password, hashed_password):
        return None
    return username


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username, db)
    if user is None:
        raise credentials_exception
    return username


def ensure_default_user() -> None:
    db = SessionLocal()
    try:
        if get_user(DEFAULT_AUTH_USERNAME, db) is None:
            stmt = insert(users_table).values(
                username=DEFAULT_AUTH_USERNAME,
                password_hash=DEFAULT_AUTH_PASSWORD_HASH,
            )
            db.execute(stmt)
            db.commit()
    finally:
        db.close()
