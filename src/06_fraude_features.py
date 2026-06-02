
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import numpy as np
from db import lire_sql

RACINE = Path(__file__).resolve().parent.parent
OUT = RACINE / "outputs"; OUT.mkdir(exist_ok=True)

# Consommation + infos compteur, depuis la base
rel = lire_sql("""
    SELECT r.id_pdl, r.date, r.consommation_kwh AS conso,
           c.type_client, c.puissance_souscrite_kva AS puissance
    FROM releves_consommation r
    JOIN compteurs c ON r.id_pdl = c.id_pdl
    ORDER BY r.id_pdl, r.date
""")
rel["date"] = pd.to_datetime(rel["date"])

# Position chronologique de chaque releve
rel["rang"] = rel.groupby("id_pdl").cumcount()
taille = rel.groupby("id_pdl")["date"].transform("size")
rel["depuis_fin"] = taille - 1 - rel["rang"]

# Profil par compteur
agg = rel.groupby("id_pdl").agg(
    moy=("conso", "mean"),
    ecart=("conso", "std"),
    n_zero=("conso", lambda s: int((s == 0).sum())),
    n_jours=("conso", "count"),
    puissance=("puissance", "first"),
    type_client=("type_client", "first"),
)
agg["cv"] = agg["ecart"] / agg["moy"]
agg["conso_par_kva"] = agg["moy"] / agg["puissance"]
prem = rel[rel["rang"] < 90].groupby("id_pdl")["conso"].mean()
dern = rel[rel["depuis_fin"] < 90].groupby("id_pdl")["conso"].mean()
agg["ratio_chute"] = (dern / prem).replace([np.inf, -np.inf], np.nan)
med_type = agg.groupby("type_client")["moy"].transform("median")
agg["ratio_vs_pairs"] = agg["moy"] / med_type

# Etiquettes (fichier de reference, hors base)
fr = pd.read_csv(RACINE / "donnees" / "cas_fraude_confirmes.csv")
agg["fraude"] = agg.index.isin(fr["id_pdl"]).astype(int)

cols = ["ratio_chute", "ratio_vs_pairs", "conso_par_kva", "cv", "n_zero", "moy"]
print("Profils calcules :", agg.shape[0], "compteurs | fraudes :", int(agg["fraude"].sum()))
print("\n=== MEDIANE par groupe (fraude=1 vs normal=0) ===")
print(agg.groupby("fraude")[cols].median().round(2).to_string())
agg.to_csv(OUT / "features_fraude.csv")
print("\nFeatures sauvegardees : outputs/features_fraude.csv")