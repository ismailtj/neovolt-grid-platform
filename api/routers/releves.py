from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import MetaData, Table, select, and_
from sqlalchemy.orm import Session

from db import engine, get_db
from schemas import ReleveConsommationSchema, VALID_ZONES
from auth import get_current_user

router = APIRouter(prefix="/releves", tags=["releves"], dependencies=[Depends(get_current_user)])
metadata = MetaData()
releves_table = Table("releves_consommation", metadata, autoload_with=engine)


@router.get("/", response_model=List[ReleveConsommationSchema])
def read_releves(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    stmt = select(releves_table).offset(skip).limit(limit)
    try:
        rows = db.execute(stmt).mappings().all()
        return [dict(row) for row in rows]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/filtre", response_model=List[ReleveConsommationSchema])
def filter_releves(
    zone: Optional[str] = Query(None),
    date_debut: Optional[date] = Query(None),
    date_fin: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    # Validation business
    if zone is not None and zone not in VALID_ZONES:
        raise HTTPException(status_code=400, detail=f"zone invalide. Valeurs acceptées: {sorted(VALID_ZONES)}")
    if date_debut and date_fin and date_debut > date_fin:
        raise HTTPException(status_code=400, detail="date_debut ne peut pas être postérieure à date_fin")

    conditions = []
    if zone is not None:
        conditions.append(releves_table.c.zone == zone)
    if date_debut is not None:
        conditions.append(releves_table.c.date >= date_debut)
    if date_fin is not None:
        conditions.append(releves_table.c.date <= date_fin)

    if conditions:
        stmt = select(releves_table).where(and_(*conditions)).offset(skip).limit(limit)
    else:
        stmt = select(releves_table).offset(skip).limit(limit)

    try:
        rows = db.execute(stmt).mappings().all()
        return [dict(row) for row in rows]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
