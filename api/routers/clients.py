from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session

from db import engine, get_db
from schemas import ClientSchema
from auth import get_current_user

router = APIRouter(prefix="/clients", tags=["clients"], dependencies=[Depends(get_current_user)])
metadata = MetaData()
clients_table = Table("clients", metadata, autoload_with=engine)


@router.get("/", response_model=List[ClientSchema])
def read_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    stmt = select(clients_table).offset(skip).limit(limit)
    try:
        rows = db.execute(stmt).mappings().all()
        return [dict(row) for row in rows]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
