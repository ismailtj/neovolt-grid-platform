
import pandas as pd
import numpy as np
import json, joblib
from datetime import datetime
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, average_precision_score

OUT = Path(__file__).resolve().parent.parent / "outputs"
MODELS = OUT / "models"; MODELS.mkdir(parents=True, exist_ok=True)
VERSION = "1.0.0"
HORODATAGE = datetime.now().strftime("%Y%m%d_%H%M")

# ---------- Modele 1 : detection de fraude ----------
f = pd.read_csv(OUT / "features_fraude.csv", index_col=0)
cols_fraude = ["ratio_chute", "ratio_vs_pairs", "conso_par_kva", "cv", "n_zero"]
Xf = f[cols_fraude].fillna(f[cols_fraude].median()).values
yf = f["fraude"].values

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
rf = RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42)
proba = cross_val_predict(rf, Xf, yf, cv=cv, method="predict_proba")[:, 1]
ordre = np.argsort(-proba)
metriques_fraude = {
    "roc_auc": round(float(roc_auc_score(yf, proba)), 3),
    "pr_auc": round(float(average_precision_score(yf, proba)), 3),
    "recall_at_50": round(float(yf[ordre[:50]].sum() / yf.sum()), 3),
    "seuil_recommande": 0.20,
}
rf.fit(Xf, yf)  # modele final sur toutes les donnees
chemin_rf = MODELS / f"fraude_rf_v{VERSION}_{HORODATAGE}.joblib"
joblib.dump({"modele": rf, "features": cols_fraude, "version": VERSION}, chemin_rf)

# ---------- Modele 2 : prevision de consommation ----------
df = pd.read_parquet(OUT / "table_analytique.parquet").rename(columns={"type_client_y": "type_client"})
v = df[df["conso"].notna()]
j = (v.groupby("date").agg(conso=("conso", "sum"), temp=("temp_moyenne_c", "mean"),
                           dju=("dju_chauffage", "mean")).reset_index().sort_values("date"))
j["conso"] /= 1000
j["mois"] = j["date"].dt.month; j["jsem"] = j["date"].dt.dayofweek
j["weekend"] = (j["jsem"] >= 5).astype(int)
j["lag1"] = j["conso"].shift(1); j["lag7"] = j["conso"].shift(7)
j["roll7"] = j["conso"].shift(1).rolling(7).mean()
j = j.dropna()
cols_prev = ["mois", "jsem", "weekend", "lag1", "lag7", "roll7", "temp", "dju"]
coupe = pd.Timestamp("2025-07-01")
tr, te = j[j["date"] < coupe], j[j["date"] >= coupe]
lr = LinearRegression().fit(tr[cols_prev], tr["conso"])
mape = float(np.mean(np.abs((te["conso"].values - lr.predict(te[cols_prev])) / te["conso"].values)) * 100)
metriques_prev = {"mape_pct": round(mape, 2), "horizon": "J+1", "validation": "chronologique"}
lr.fit(j[cols_prev], j["conso"])  # modele final sur tout l'historique
chemin_lr = MODELS / f"prevision_lr_v{VERSION}_{HORODATAGE}.joblib"
joblib.dump({"modele": lr, "features": cols_prev, "version": VERSION}, chemin_lr)

# ---------- Carte de modele (model card) ----------
carte = {
    "projet": "Neovolt Grid+",
    "version": VERSION,
    "date_entrainement": HORODATAGE,
    "graine_aleatoire": 42,
    "modeles": {
        "detection_fraude": {
            "algorithme": "RandomForestClassifier (class_weight=balanced)",
            "fichier": chemin_rf.name,
            "features": cols_fraude,
            "metriques": metriques_fraude,
            "usage": "Scoring batch J+1, liste de suspects -> revue humaine OBLIGATOIRE",
        },
        "prevision_consommation": {
            "algorithme": "LinearRegression",
            "fichier": chemin_lr.name,
            "features": cols_prev,
            "metriques": metriques_prev,
            "usage": "Prevision quotidienne demande reseau -> achats d'energie",
        },
    },
}
(MODELS / "model_card.json").write_text(json.dumps(carte, indent=2, ensure_ascii=False), encoding="utf-8")

print("Modeles entraines et sauvegardes dans outputs/models/ :")
print("  -", chemin_rf.name)
print("  -", chemin_lr.name)
print("\nMetriques journalisees (model_card.json) :")
print("  Fraude   :", metriques_fraude)
print("  Prevision:", metriques_prev)
print("\nCarte de modele ecrite : outputs/models/model_card.json")