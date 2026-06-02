#!/usr/bin/env python3
"""
Pipeline ETL - Plateforme de Données d'Énergie Neovolt
Ingestion + nettoyage des données énergétiques vers PostgreSQL.
Version idempotente : relançable sans erreur (meteo et releves corrigés).
"""
import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
    logger.info(f"Variables d'environnement chargées depuis {env_file}")
else:
    logger.warning(f"Fichier .env non trouvé à {env_file}")
    load_dotenv()


def get_db_engine():
    user = os.getenv("POSTGRES_USER"); password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost"); port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB")
    required = {"POSTGRES_USER": user, "POSTGRES_PASSWORD": password, "POSTGRES_DB": database}
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise ValueError(f"Variables d'environnement manquantes : {', '.join(missing)}")
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    logger.info(f"Création du moteur PostgreSQL : {host}:{port}/{database}")
    return create_engine(url, echo=False)


def get_existing_pks(engine, table_name, pk_col):
    try:
        with engine.connect() as conn:
            return {row[0] for row in conn.execute(text(f"SELECT {pk_col} FROM {table_name}")).fetchall()}
    except Exception as e:
        logger.warning(f"Clés existantes indisponibles pour {table_name}: {e}")
        return set()


def get_existing_pk_pairs(engine, table_name, pk_cols):
    cols = ", ".join(pk_cols)
    try:
        with engine.connect() as conn:
            # On normalise en TEXTE : PostgreSQL renvoie les dates comme objets date,
            # alors que le CSV les a en texte. Sans cela, la comparaison echoue.
            return {tuple(str(v) for v in row)
                    for row in conn.execute(text(f"SELECT {cols} FROM {table_name}")).fetchall()}
    except Exception as e:
        logger.warning(f"Clés existantes indisponibles pour {table_name}: {e}")
        return set()


def impute_missing_consumption(df):
    df = df.copy()
    df['consommation_kwh'] = pd.to_numeric(df['consommation_kwh'], errors='coerce')
    invalid_mask = df['consommation_kwh'].isna() | (df['consommation_kwh'] < 0)
    invalid_before = invalid_mask.sum()
    if invalid_before == 0:
        return df
    df.loc[invalid_mask, 'consommation_kwh'] = pd.NA
    id_mean = df.groupby('id_pdl', observed=True)['consommation_kwh'].mean()
    df['consommation_kwh'] = df['consommation_kwh'].fillna(df['id_pdl'].map(id_mean))
    zone_mean = df.groupby('zone', observed=True)['consommation_kwh'].mean()
    df['consommation_kwh'] = df['consommation_kwh'].fillna(df['zone'].map(zone_mean))
    df['consommation_kwh'] = df['consommation_kwh'].fillna(df['consommation_kwh'].mean()).fillna(0)
    logger.info(f"  → Imputation : {invalid_before} valeurs traitées, {int(df['consommation_kwh'].isna().sum())} restent NA")
    return df


def wait_for_db(engine, retries=12, delay=5):
    for attempt in range(1, retries + 1):
        try:
            with engine.connect():
                return
        except OperationalError:
            if attempt >= retries:
                raise
            logger.warning("PostgreSQL non disponible. Tentative %d/%d...", attempt, retries)
            time.sleep(delay)


def ingest_clients(engine, data_dir):
    logger.info("[1/4] Ingestion de clients.csv...")
    df = pd.read_csv(data_dir / "clients.csv")
    logger.info(f"  → {len(df)} lignes lues")
    existing = get_existing_pks(engine, 'clients', 'id_client')
    if existing:
        df = df[~df['id_client'].astype(str).isin(existing)]
        if df.empty:
            logger.info("  → Déjà à jour, rien à insérer."); return
    df.to_sql('clients', engine, if_exists='append', index=False)
    logger.info(f"  ✓ {len(df)} lignes insérées dans 'clients'")


def ingest_compteurs(engine, data_dir):
    logger.info("[2/4] Ingestion de compteurs.csv...")
    df = pd.read_csv(data_dir / "compteurs.csv")
    logger.info(f"  → {len(df)} lignes lues")
    existing = get_existing_pks(engine, 'compteurs', 'id_pdl')
    if existing:
        df = df[~df['id_pdl'].astype(str).isin(existing)]
        if df.empty:
            logger.info("  → Déjà à jour, rien à insérer."); return
    df.to_sql('compteurs', engine, if_exists='append', index=False)
    logger.info(f"  ✓ {len(df)} lignes insérées dans 'compteurs'")


def ingest_meteo(engine, data_dir):
    logger.info("[3/4] Ingestion de meteo.csv...")
    df = pd.read_csv(data_dir / "meteo.csv")
    logger.info(f"  → {len(df)} lignes lues")
    df['dju_chauffage'] = np.where(df['temp_moyenne_c'] < 17.0, 17.0 - df['temp_moyenne_c'], 0.0)
    df['dju_chauffage'] = df['dju_chauffage'].round(1).fillna(0.0)
    logger.info(f"  ✓ DJU calculé pour {len(df)} lignes")
    df = df.drop_duplicates(subset=['date', 'zone'])
    # Idempotence : retirer les (date, zone) deja en base (comparaison en TEXTE)
    existing = get_existing_pk_pairs(engine, 'meteo', ['date', 'zone'])
    if existing:
        cle = pd.Series(list(zip(df['date'].astype(str), df['zone'].astype(str))), index=df.index)
        before = len(df)
        df = df[~cle.isin(existing)]
        logger.info(f"  → {before - len(df)} lignes déjà en base ignorées, {len(df)} à insérer")
        if df.empty:
            logger.info("  → Déjà à jour, rien à insérer."); return
    df.to_sql('meteo', engine, if_exists='append', index=False, chunksize=500)
    logger.info(f"  ✓ {len(df)} lignes insérées dans 'meteo'")


def ingest_releves_consommation(engine, data_dir):
    logger.info("[4/4] Ingestion de releves_consommation.csv (volumétrie élevée)...")
    df = pd.read_csv(data_dir / "releves_consommation.csv")
    logger.info(f"  → {len(df)} lignes lues")
    df = df.drop_duplicates(subset=['id_pdl', 'date'])
    df = impute_missing_consumption(df)
    # Idempotence : retirer les (id_pdl, date) deja en base (comparaison en TEXTE)
    existing = get_existing_pk_pairs(engine, 'releves_consommation', ['id_pdl', 'date'])
    if existing:
        cle = pd.Series(list(zip(df['id_pdl'].astype(str), df['date'].astype(str))), index=df.index)
        before = len(df)
        df = df[~cle.isin(existing)]
        logger.info(f"  → {before - len(df)} relevés déjà en base ignorés, {len(df)} à insérer")
        if df.empty:
            logger.info("  → Déjà à jour, rien à insérer."); return
    df.to_sql('releves_consommation', engine, if_exists='append', index=False, chunksize=10000)
    logger.info(f"  ✓ {len(df)} lignes insérées dans 'releves_consommation'")


def run_pipeline():
    logger.info("=" * 60); logger.info("Démarrage du Pipeline ETL Neovolt"); logger.info("=" * 60)
    engine = get_db_engine()
    wait_for_db(engine)
    with engine.connect() as c:
        logger.info(f"✓ Connecté : {c.execute(text('SELECT version()')).fetchone()[0][:40]}")
    data_dir = project_root / "donnees"
    if not data_dir.exists():
        raise FileNotFoundError(f"Dossier {data_dir} introuvable")
    ingest_clients(engine, data_dir)
    ingest_compteurs(engine, data_dir)
    ingest_meteo(engine, data_dir)
    ingest_releves_consommation(engine, data_dir)
    logger.info("✓ Pipeline d'ingestion terminé avec SUCCÈS")
    return engine


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        logger.error(f"✗ Le pipeline s'est arrêté : {e}")
        exit(1)