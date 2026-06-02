
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

OUT = Path(__file__).resolve().parent.parent / "outputs"
df = pd.read_parquet(OUT / "table_analytique.parquet").rename(columns={"type_client_y": "type_client"})
v = df[df["conso"].notna()]

# 1) Serie journaliere : conso totale (MWh) + meteo moyenne + calendrier
j = (v.groupby("date")
       .agg(conso=("conso", "sum"), temp=("temp_moyenne_c", "mean"), dju=("dju_chauffage", "mean"))
       .reset_index().sort_values("date").reset_index(drop=True))
j["conso"] = j["conso"] / 1000                       # kWh -> MWh
j["mois"] = j["date"].dt.month
j["jsem"] = j["date"].dt.dayofweek
j["weekend"] = (j["jsem"] >= 5).astype(int)
# Variables "retard" : la consommation passee predit la future
j["lag1"] = j["conso"].shift(1)                      # hier
j["lag7"] = j["conso"].shift(7)                      # meme jour la semaine derniere
j["roll7"] = j["conso"].shift(1).rolling(7).mean()   # moyenne 7 derniers jours
j = j.dropna().reset_index(drop=True)

# 2) Split chronologique : on teste sur les 6 derniers mois (jamais vus a l'entrainement)
coupe = pd.Timestamp("2025-07-01")
tr, te = j[j["date"] < coupe].copy(), j[j["date"] >= coupe].copy()
print(f"Train : {len(tr)} jours (< {coupe.date()})  |  Test : {len(te)} jours (futur)\n")

def evalue(nom, reel, pred):
    mae = mean_absolute_error(reel, pred)
    rmse = np.sqrt(mean_squared_error(reel, pred))
    mape = np.mean(np.abs((reel - pred) / reel)) * 100
    print(f"  {nom:34s} MAE={mae:5.1f} MWh   RMSE={rmse:5.1f}   MAPE={mape:5.2f}%")
    return mape

reel = te["conso"].values

# 3) Baselines
print("=== Baselines (aucun modele) ===")
evalue("Naive (= hier)", reel, te["lag1"].values)
evalue("Saisonniere (= meme jour S-1)", reel, te["lag7"].values)

# 4) Modeles avec meteo
feats_cal = ["mois", "jsem", "weekend", "lag1", "lag7", "roll7"]
feats = feats_cal + ["temp", "dju"]
print("\n=== Modeles (calendrier + retards + meteo) ===")
for nom, model in [("Regression lineaire", LinearRegression()),
                   ("Random Forest", RandomForestRegressor(n_estimators=300, random_state=42)),
                   ("Gradient Boosting", HistGradientBoostingRegressor(random_state=42))]:
    model.fit(tr[feats], tr["conso"])
    evalue(nom, reel, model.predict(te[feats]))

# 5) Apport de la meteo (sur le meilleur modele : regression lineaire)
print("\n=== Apport de la meteo (regression lineaire) ===")
lr_sans = LinearRegression().fit(tr[feats_cal], tr["conso"])
evalue("SANS meteo", reel, lr_sans.predict(te[feats_cal]))
lr = LinearRegression().fit(tr[feats], tr["conso"])
evalue("AVEC meteo", reel, lr.predict(te[feats]))

# 6) Sauvegarde reel vs predit (modele retenu) pour visualisation
te["prevision"] = lr.predict(te[feats])
te[["date", "conso", "prevision", "temp"]].to_csv(OUT / "prevision_test.csv", index=False)
print("\nModele retenu : regression lineaire avec meteo (~4,5% d'erreur a J+1).")
print("Reel vs predit sauvegarde : outputs/prevision_test.csv")