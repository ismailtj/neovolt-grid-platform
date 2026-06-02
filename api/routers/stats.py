from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import MetaData, Table, select, func
from sqlalchemy.orm import Session

from db import engine, get_db
from schemas import GlobalStatsResponse, ZoneStatsResponse, VALID_ZONES

router = APIRouter(prefix="/stats", tags=["stats"])
metadata = MetaData()
releves_table = Table("releves_consommation", metadata, autoload_with=engine)


@router.get("/global", response_model=GlobalStatsResponse)
def global_stats(db: Session = Depends(get_db)):
    stmt = select(
        func.coalesce(func.sum(releves_table.c.consommation_kwh), 0).label("consommation_totale_kwh"),
        func.avg(releves_table.c.consommation_kwh).label("consommation_moyenne_quotidienne"),
        func.count().label("nombre_total_releves"),
    )
    try:
        result = db.execute(stmt).one()
        consommation_totale = float(result.consumption_totale_kwh) if hasattr(result, 'consumption_totale_kwh') else float(result[0] or 0)
    except Exception:
        # fallback mapping access
        result = db.execute(stmt).one()
        consommation_totale = float(result[0] or 0)

    # Better extraction using labels
    row = db.execute(stmt).mappings().one()
    return GlobalStatsResponse(
        consommation_totale_kwh=float(row["consommation_totale_kwh"] or 0),
        consommation_moyenne_quotidienne=(float(row["consommation_moyenne_quotidienne"]) if row["consommation_moyenne_quotidienne"] is not None else None),
        nombre_total_releves=int(row["nombre_total_releves"] or 0),
    )


@router.get("/zone/{zone}", response_model=ZoneStatsResponse)
def zone_stats(zone: str, db: Session = Depends(get_db)):
    if zone not in VALID_ZONES:
        raise HTTPException(status_code=404, detail=f"Zone '{zone}' introuvable. Valeurs acceptées: {sorted(VALID_ZONES)}")

    # Aggregations: total, avg, max
    stmt = select(
        func.coalesce(func.sum(releves_table.c.consommation_kwh), 0).label("consommation_totale"),
        func.avg(releves_table.c.consommation_kwh).label("consommation_moyenne"),
        func.max(releves_table.c.consommation_kwh).label("pic_consommation"),
    ).where(releves_table.c.zone == zone)

    row = db.execute(stmt).mappings().one()
    consommation_totale = float(row["consommation_totale"] or 0)
    consommation_moyenne = float(row["consommation_moyenne"]) if row["consommation_moyenne"] is not None else None
    pic_val = row["pic_consommation"]

    pic_date = None
    if pic_val is not None:
        # get date associated with max value — pick earliest/latest occurrence
        stmt2 = select(releves_table.c.date).where(
            (releves_table.c.zone == zone) & (releves_table.c.consommation_kwh == pic_val)
        ).order_by(releves_table.c.date.desc()).limit(1)
        res2 = db.execute(stmt2).scalar()
        if res2 is not None:
            pic_date = res2

    return ZoneStatsResponse(
        zone=zone,
        consommation_totale=consommation_totale,
        consommation_moyenne=consommation_moyenne,
        pic_consommation=float(pic_val) if pic_val is not None else None,
        pic_consommation_date=pic_date,
    )
