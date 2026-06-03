from typing import List
from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import MetaData, Table, select
from sqlalchemy import and_
from sqlalchemy.orm import Session

from db import engine, get_db
from schemas import MeteoSchema, VALID_ZONES
from auth import get_current_user

router = APIRouter(prefix="/meteo", tags=["meteo"], dependencies=[Depends(get_current_user)])
metadata = MetaData()
meteo_table = Table("meteo", metadata, autoload_with=engine)


@router.get("/", response_model=List[MeteoSchema])
def read_meteo(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    stmt = select(meteo_table).offset(skip).limit(limit)
    try:
        rows = db.execute(stmt).mappings().all()
        return [dict(row) for row in rows]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/filtre", response_model=List[MeteoSchema])
def filter_meteo(
    zone: Optional[str] = Query(None),
    date_debut: Optional[date] = Query(None),
    date_fin: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    if zone is not None and zone not in VALID_ZONES:
        raise HTTPException(status_code=400, detail=f"zone invalide. Valeurs acceptées: {sorted(VALID_ZONES)}")
    if date_debut and date_fin and date_debut > date_fin:
        raise HTTPException(status_code=400, detail="date_debut ne peut pas être postérieure à date_fin")

    conditions = []
    if zone is not None:
        conditions.append(meteo_table.c.zone == zone)
    if date_debut is not None:
        conditions.append(meteo_table.c.date >= date_debut)
    if date_fin is not None:
        conditions.append(meteo_table.c.date <= date_fin)

    if conditions:
        stmt = select(meteo_table).where(and_(*conditions)).offset(skip).limit(limit)
    else:
        stmt = select(meteo_table).offset(skip).limit(limit)

    try:
        rows = db.execute(stmt).mappings().all()
        return [dict(row) for row in rows]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
