
import pandas as pd
import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "outputs"
df = pd.read_parquet(OUT / "table_analytique.parquet").rename(columns={"type_client_y": "type_client"})
v = df[df["conso"].notna()]

print("=== 1. SAISONNALITE : conso moyenne par mois (kWh/j) ===")
print(v.groupby("mois")["conso"].mean().round(1).to_string())

print("\n=== 2. EFFET DU FROID : correlation conso~DJU par type de chauffage ===")
for ch in ["electrique", "gaz", "reseau_chaleur", "autre"]:
    sub = v[v["type_chauffage"] == ch].groupby("date").agg(
        conso=("conso", "sum"), dju=("dju_chauffage", "mean"))
    if len(sub) > 10:
        print(f"  {ch:15s} : correlation = {sub['conso'].corr(sub['dju']):+.2f}")

print("\n=== 3. PROFILS : conso mediane par type de client (kWh/j) ===")
print(v.groupby("type_client")["conso"].median().round(1).to_string())

print("\n=== 4. ZONES : conso mediane par zone (kWh/j) ===")
print(v.groupby("zone")["conso"].median().round(1).sort_values(ascending=False).to_string())

print("\n=== 5. JOUR DE SEMAINE (residentiel) : semaine vs week-end ===")
res = v[v["type_client"] == "residentiel"]
print(res.groupby("weekend")["conso"].median().round(2).to_string())