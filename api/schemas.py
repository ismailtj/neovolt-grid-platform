from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_SEGMENTS = {
    "particulier",
    "petit_pro",
    "entreprise",
    "collectivite",
}

VALID_ZONES = {
    "Val-Nord",
    "Centre-Ville",
    "Plateau-Est",
    "Rives-Sud",
    "Zone-Industrielle",
    "Coteaux-Ouest",
    "Bourg-Ancien",
    "Parc-Tertiaire",
}

VALID_TYPE_CLIENTS = {"residentiel", "professionnel", "industriel"}
VALID_PUISSANCES_SOUSCRITES = {6, 9, 12, 36, 120, 250}


class ClientSchema(BaseModel):
    id_client: str = Field(..., example="CLI-00001")
    segment: str = Field(..., example="particulier")
    commune: str
    code_postal: str
    date_entree: date
    nb_personnes_foyer: Optional[int] = Field(None, ge=1, le=5)
    surface_m2: int

    model_config = ConfigDict(from_attributes=True)

    @field_validator("segment")
    @classmethod
    def validate_segment(cls, value: str) -> str:
        if value not in VALID_SEGMENTS:
            raise ValueError(
                f"segment doit être l'une des valeurs suivantes : {sorted(VALID_SEGMENTS)}"
            )
        return value


class CompteurSchema(BaseModel):
    id_pdl: str = Field(..., example="PDL-000001")
    id_client: str
    zone: str
    type_client: str
    puissance_souscrite_kva: int
    type_chauffage: str
    type_compteur: str
    date_pose: date
    statut: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("zone")
    @classmethod
    def validate_zone(cls, value: str) -> str:
        if value not in VALID_ZONES:
            raise ValueError(f"zone doit être l'une des valeurs suivantes : {sorted(VALID_ZONES)}")
        return value

    @field_validator("type_client")
    @classmethod
    def validate_type_client(cls, value: str) -> str:
        if value not in VALID_TYPE_CLIENTS:
            raise ValueError(
                f"type_client doit être l'une des valeurs suivantes : {sorted(VALID_TYPE_CLIENTS)}"
            )
        return value

    @field_validator("puissance_souscrite_kva")
    @classmethod
    def validate_puissance_souscrite_kva(cls, value: int) -> int:
        if value not in VALID_PUISSANCES_SOUSCRITES:
            raise ValueError(
                f"puissance_souscrite_kva doit être l'une des valeurs suivantes : {sorted(VALID_PUISSANCES_SOUSCRITES)}"
            )
        return value


class MeteoSchema(BaseModel):
    date: date
    zone: str
    temp_moyenne_c: float
    temp_min_c: float
    temp_max_c: float
    dju_chauffage: float

    model_config = ConfigDict(from_attributes=True)

    @field_validator("zone")
    @classmethod
    def validate_zone(cls, value: str) -> str:
        if value not in VALID_ZONES:
            raise ValueError(f"zone doit être l'une des valeurs suivantes : {sorted(VALID_ZONES)}")
        return value


class ReleveConsommationSchema(BaseModel):
    id_pdl: str
    date: date
    consommation_kwh: float = Field(..., ge=0.0)
    zone: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("zone")
    @classmethod
    def validate_zone(cls, value: str) -> str:
        if value not in VALID_ZONES:
            raise ValueError(f"zone doit être l'une des valeurs suivantes : {sorted(VALID_ZONES)}")
        return value


class GlobalStatsResponse(BaseModel):
    consommation_totale_kwh: float
    consommation_moyenne_quotidienne: Optional[float]
    nombre_total_releves: int

    model_config = ConfigDict(from_attributes=True)


class ZoneStatsResponse(BaseModel):
    zone: str
    consommation_totale: float
    consommation_moyenne: Optional[float]
    pic_consommation: Optional[float]
    pic_consommation_date: Optional[date]

    model_config = ConfigDict(from_attributes=True)
