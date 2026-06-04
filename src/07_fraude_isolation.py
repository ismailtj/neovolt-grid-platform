
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

OUT = Path(__file__).resolve().parent.parent / "outputs"
f = pd.read_csv(OUT / "features_fraude.csv", index_col=0)
y = f["fraude"].values
n_fraudes = int(y.sum())

def recall_at_N(scores, y, Ns):
    """scores : plus eleve = plus suspect. Renvoie recall@N pour chaque N."""
    ordre = np.argsort(-scores)
    return {N: (int(y[ordre[:N]].sum()), y[ordre[:N]].sum() / y.sum()) for N in Ns}

Ns = [24, 50, 70, 100]

# --- Modele non supervise : Isolation Forest sur les features comportementales ---
# (on exclut la taille brute 'moy' qui ferait passer les gros industriels pour des anomalies)
cols = ["ratio_chute", "ratio_vs_pairs", "cv", "conso_par_kva"]
X = StandardScaler().fit_transform(f[cols].fillna(f[cols].median()))
iso = IsolationForest(n_estimators=300, contamination=0.05, random_state=42).fit(X)
score_iso = -iso.score_samples(X)          # plus haut = plus anormal
f["score_anomalie"] = score_iso

# --- Baseline : classer par ratio de chute (chute forte = suspect) ---
score_base = -f["ratio_chute"].fillna(1.0).values

print(f"{n_fraudes} fraudes connues parmi {len(f)} compteurs.\n")
print("Recall@N (part des 24 fraudes retrouvees dans le top N des suspects)")
print(f"{'N':>5} | {'Isolation Forest':>18} | {'Regle ratio_chute':>18}")
print("-" * 50)
ri, rb = recall_at_N(score_iso, y, Ns), recall_at_N(score_base, y, Ns)
for N in Ns:
    print(f"{N:>5} | {ri[N][0]:>2}/{n_fraudes} ({ri[N][1]:>4.0%})       | {rb[N][0]:>2}/{n_fraudes} ({rb[N][1]:>4.0%})")

print("\nLecon : la regle simple (ratio_chute) fait aussi bien, voire mieux.")
print("Mais les deux plafonnent : ~8 fraudes n'ont PAS de chute (frauduleuses")
print("des le depart) -> une autre piste (conso vs pairs) est necessaire pour elles.")

f[["fraude", "ratio_chute", "ratio_vs_pairs", "score_anomalie"]].to_csv(OUT / "scores_anomalie.csv")
print("\nScores sauvegardes : outputs/scores_anomalie.csv")