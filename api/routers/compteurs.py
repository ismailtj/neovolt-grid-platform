from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session

from db import engine, get_db
from schemas import CompteurSchema
from auth import get_current_user

router = APIRouter(prefix="/compteurs", tags=["compteurs"], dependencies=[Depends(get_current_user)])
metadata = MetaData()
compteurs_table = Table("compteurs", metadata, autoload_with=engine)


@router.get("", include_in_schema=False, response_model=List[CompteurSchema])
@router.get("/", response_model=List[CompteurSchema])
def read_compteurs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    stmt = select(compteurs_table).offset(skip).limit(limit)
    try:
        rows = db.execute(stmt).mappings().all()
        return [dict(row) for row in rows]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
