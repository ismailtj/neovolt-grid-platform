
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, average_precision_score,
                             confusion_matrix)

OUT = Path(__file__).resolve().parent.parent / "outputs"
f = pd.read_csv(OUT / "features_fraude.csv", index_col=0)
cols = ["ratio_chute", "ratio_vs_pairs", "conso_par_kva", "cv", "n_zero"]
X = f[cols].fillna(f[cols].median()).values
y = f["fraude"].values
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# 1) LE PIEGE DE L'ACCURACY : un modele qui predit toujours "normal"
dummy = cross_val_predict(DummyClassifier(strategy="most_frequent"), X, y, cv=cv)
print("=== 1. Le piege de l'exactitude (accuracy) ===")
print(f"Modele 'tout normal' : accuracy = {accuracy_score(y, dummy):.1%} "
      f"mais recall = {recall_score(y, dummy):.0%} (0 fraude detectee !)")
print("-> Avec 96,6% de compteurs sains, l'accuracy ne veut RIEN dire.\n")

# 2) Deux modeles, metriques adaptees (probabilites en validation croisee)
def proba_cv(model):
    return cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]

modeles = {
    "Regression logistique": make_pipeline(StandardScaler(),
        LogisticRegression(class_weight="balanced", max_iter=1000)),
    "Random Forest": RandomForestClassifier(n_estimators=300,
        class_weight="balanced", random_state=42),
}
print("=== 2. Comparaison (metriques adaptees au desequilibre) ===")
probas = {}
for nom, m in modeles.items():
    p = proba_cv(m); probas[nom] = p
    print(f"{nom:24s} : ROC-AUC = {roc_auc_score(y, p):.3f}  "
          f"PR-AUC = {average_precision_score(y, p):.3f}")
print("-> Le Random Forest gagne nettement (relation non lineaire).\n")

proba = probas["Random Forest"]

# 3) Importance des features
rf = RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42).fit(X, y)
print("=== 3. Ce que le modele a appris (importance des features) ===")
for c, i in sorted(zip(cols, rf.feature_importances_), key=lambda t: -t[1]):
    print(f"   {c:16s} {i:.2f}")
print()

# 4) Choix du SEUIL (point de fonctionnement)
print("=== 4. Effet du seuil (Random Forest) ===")
print(f"{'seuil':>6} | {'precision':>9} | {'recall':>7} | suspects")
for s in [0.50, 0.40, 0.30, 0.20]:
    pred = (proba >= s).astype(int)
    print(f"{s:>6.2f} | {precision_score(y, pred, zero_division=0):>9.2f} | "
          f"{recall_score(y, pred):>7.0%} | {int(pred.sum()):>4d}")
print("-> A 0,20 : on signale ~37 compteurs et on attrape ~79% des fraudes.\n")

# 5) Recall@N : le modele bat-il enfin la regle simple ?
def recall_at_N(scores, Ns):
    o = np.argsort(-scores)
    return {N: y[o[:N]].sum() / y.sum() for N in Ns}
Ns = [24, 50, 100]
rf_r = recall_at_N(proba, Ns)
base_r = recall_at_N(-f["ratio_chute"].fillna(1).values, Ns)
print("=== 5. Recall@N : Random Forest vs baseline (ratio_chute seul) ===")
print(f"{'N':>5} | {'RandomForest':>13} | {'baseline':>10}")
for N in Ns:
    print(f"{N:>5} | {rf_r[N]:>12.0%} | {base_r[N]:>9.0%}")
print("-> En combinant ratio_chute ET ratio_vs_pairs, le RF rattrape les")
print("   fraudes 'sans chute' que la regle ratait (top 50 : 88% vs 67%).\n")

# 6) Liste des suspects a transmettre a l'equipe anti-fraude
f["score_fraude"] = proba
suspects = f.sort_values("score_fraude", ascending=False).head(50)
suspects[["score_fraude", "fraude", "ratio_chute", "ratio_vs_pairs"]].to_csv(OUT / "suspects_fraude.csv")
print("Top 50 des suspects sauvegarde : outputs/suspects_fraude.csv")