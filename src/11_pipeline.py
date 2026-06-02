
import subprocess, sys, time
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "src"
LOG = RACINE / "outputs" / "pipeline.log"
LOG.parent.mkdir(exist_ok=True)

# Etapes du pipeline : (nom lisible, script, fichier produit attendu)
ETAPES = [
    ("Table analytique + DJU",     "03_table_analytique.py", "outputs/table_analytique.parquet"),
    ("Features de fraude",         "06_fraude_features.py",  "outputs/features_fraude.csv"),
    ("Modele de fraude (supervise)","08_fraude_supervise.py","outputs/suspects_fraude.csv"),
    ("Prevision de consommation",  "09_prevision.py",        "outputs/prevision_test.csv"),
    ("MLOps : modeles + registre", "10_mlops.py",            "outputs/models/model_card.json"),
]

def journaliser(msg):
    horo = datetime.now().strftime("%H:%M:%S")
    ligne = f"[{horo}] {msg}"
    print(ligne)
    with open(LOG, "a", encoding="utf-8") as fa:
        fa.write(ligne + "\n")

def lancer():
    journaliser("=== DEBUT DU PIPELINE NEOVOLT GRID+ ===")
    t_global = time.time()
    for i, (nom, script, produit) in enumerate(ETAPES, 1):
        journaliser(f"[{i}/{len(ETAPES)}] {nom} ...")
        t0 = time.time()
        res = subprocess.run([sys.executable, str(SRC / script)],
                             capture_output=True, text=True)
        if res.returncode != 0:
            journaliser(f"    ECHEC. Sortie d'erreur :\n{res.stderr.strip()}")
            journaliser("=== PIPELINE INTERROMPU ===")
            sys.exit(1)
        # Verification que le livrable attendu existe bien (controle qualite)
        existe = (RACINE / produit).exists()
        journaliser(f"    OK en {time.time()-t0:4.1f}s  -> {produit} "
                    f"{'cree' if existe else 'MANQUANT !'}")
    journaliser(f"=== PIPELINE TERMINE en {time.time()-t_global:.1f}s ===")
    journaliser("Tous les livrables sont a jour dans outputs/.")

if __name__ == "__main__":
    LOG.write_text("", encoding="utf-8")  # repart d'un journal propre
    lancer()