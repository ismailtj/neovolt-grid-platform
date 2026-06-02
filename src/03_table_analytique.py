
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
from db import lire_sql

OUT = Path(__file__).resolve().parent.parent / "outputs"; OUT.mkdir(exist_ok=True)

# Jointure des 4 tables, cote PostgreSQL
requete = """
SELECT r.id_pdl, r.date, r.consommation_kwh AS conso, r.zone,
       c.type_client, c.type_chauffage, c.puissance_souscrite_kva,
       cl.segment, cl.surface_m2, cl.nb_personnes_foyer,
       m.temp_moyenne_c, m.dju_chauffage
FROM releves_consommation r
JOIN compteurs c  ON r.id_pdl = c.id_pdl
JOIN clients   cl ON c.id_client = cl.id_client
JOIN meteo     m  ON r.date = m.date AND r.zone = m.zone
"""
df = lire_sql(requete)
df["date"] = pd.to_datetime(df["date"])

# Variables calendaires
df["mois"] = df["date"].dt.month
df["annee"] = df["date"].dt.year
df["jour_semaine"] = df["date"].dt.dayofweek
df["weekend"] = df["jour_semaine"] >= 5
saisons = {12:"Hiver",1:"Hiver",2:"Hiver",3:"Printemps",4:"Printemps",5:"Printemps",
           6:"Ete",7:"Ete",8:"Ete",9:"Automne",10:"Automne",11:"Automne"}
df["saison"] = df["mois"].map(saisons)

print("Table analytique (depuis la base) :", df.shape[0], "lignes x", df.shape[1], "colonnes")
print("Consommation manquante :", int(df["conso"].isna().sum()), "(0 attendu : donnees imputees)")
df.to_parquet(OUT / "table_analytique.parquet", index=False)
print("Sauvegardee : outputs/table_analytique.parquet")