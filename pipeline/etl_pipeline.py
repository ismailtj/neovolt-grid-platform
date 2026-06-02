#!/usr/bin/env python3
"""
Pipeline ETL - Plateforme de Données d'Énergie Neovolt

Module principal pour l'ingestion et le nettoyage des données énergétiques.
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

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis .env à la racine du projet
project_root = Path(__file__).parent.parent  # Remonte de pipeline/ à la racine
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(dotenv_path=env_file)
    logger.info(f"Variables d'environnement chargées depuis {env_file}")
else:
    logger.warning(f"Fichier .env non trouvé à {env_file}")
    load_dotenv()


def get_db_engine():
    """
    Construit et retourne un objet SQLAlchemy Engine pour PostgreSQL.
    
    Extrait les variables d'environnement :
    - POSTGRES_USER
    - POSTGRES_PASSWORD
    - POSTGRES_HOST (défaut: localhost)
    - POSTGRES_PORT (défaut: 5432)
    - POSTGRES_DB
    
    Returns
    -------
    sqlalchemy.engine.Engine
        Objet Engine prêt à être utilisé pour les connexions à la base.
    
    Raises
    ------
    ValueError
        Si une variable d'environnement obligatoire est manquante.
    """
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB")
    
    # Validation
    required_vars = {
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": database,
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    if missing:
        raise ValueError(f"Variables d'environnement manquantes : {', '.join(missing)}")
    
    # Construction de la chaîne de connexion
    database_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    
    logger.info(f"Création du moteur PostgreSQL : {host}:{port}/{database}")
    try:
        engine = create_engine(database_url, echo=False)
    except ImportError as e:
        if "psycopg2" in str(e).lower():
            raise ImportError(
                "Le package 'psycopg2-binary' n'est pas installé. "
                "Exécutez `pip install -r requirements.txt` ou `pip install psycopg2-binary` "
                "dans l'environnement virtuel actif."
            ) from e
        raise
    
    return engine


def get_existing_pks(engine, table_name, pk_col):
    """Retourne un set des valeurs de clé primaire déjà présentes dans la table.

    En cas d'erreur, retourne un set vide et logue un avertissement.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT {pk_col} FROM {table_name}"))
            return {row[0] for row in result.fetchall()}
    except Exception as e:
        logger.warning(f"Impossible de récupérer les clés existantes pour {table_name}: {e}")
        return set()


def get_existing_pk_pairs(engine, table_name, pk_cols):
    """Retourne un set de tuples des clés primaires composites déjà présentes dans la table."""
    cols = ", ".join(pk_cols)
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT {cols} FROM {table_name}"))
            return {tuple(row) for row in result.fetchall()}
    except Exception as e:
        logger.warning(f"Impossible de récupérer les clés existantes pour {table_name}: {e}")
        return set()


def impute_missing_consumption(df):
    """Impute les consommations manquantes ou négatives dans releves_consommation.

    Règle d'imputation :
    1. moyenne par id_pdl
    2. fallback moyenne par zone
    3. fallback moyenne globale
    4. fallback 0 si nécessaire
    """
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

    global_mean = df['consommation_kwh'].mean()
    df['consommation_kwh'] = df['consommation_kwh'].fillna(global_mean)
    df['consommation_kwh'] = df['consommation_kwh'].fillna(0)

    invalid_after = df['consommation_kwh'].isna().sum()
    logger.info(
        f"  → Imputation des consommations manquantes ou négatives : {invalid_before} valeurs traitées, {invalid_after} restent NA après imputation"
    )

    return df


def wait_for_db(engine, retries=12, delay=5):
    """Attendre que PostgreSQL soit disponible avant de lancer la pipeline."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as connection:
                return
        except OperationalError:
            if attempt >= retries:
                raise
            logger.warning(
                "PostgreSQL non disponible %s:%s. "
                "Tentative %d/%d. Attente %d secondes...",
                host,
                port,
                attempt,
                retries,
                delay,
            )
            time.sleep(delay)


def ingest_clients(engine, data_dir):
    """
    Ingère le fichier CSV clients.csv dans la table clients.
    
    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        Moteur de connexion à PostgreSQL
    data_dir : Path
        Chemin vers le dossier contenant les fichiers CSV
    
    Raises
    ------
    FileNotFoundError
        Si le fichier CSV n'existe pas
    Exception
        En cas d'erreur lors de l'insertion en base
    """
    csv_file = data_dir / "clients.csv"
    logger.info(f"[1/4] Début de l'ingestion de {csv_file.name}...")
    
    try:
        if not csv_file.exists():
            raise FileNotFoundError(f"Fichier {csv_file} non trouvé")
        
        # Lecture du CSV
        df = pd.read_csv(csv_file)
        logger.info(f"  → {len(df)} lignes lues depuis {csv_file.name}")

        # Éviter les doublons : filtrer les id_client déjà présents en base
        existing = get_existing_pks(engine, 'clients', 'id_client')
        if existing:
            before = len(df)
            df = df[~df['id_client'].isin(existing)]
            logger.info(f"  → {len(existing)} clés existantes trouvées, {len(df)} lignes restant après déduplication")
            if df.empty:
                logger.info("  → Aucune nouvelle ligne à insérer pour 'clients'; saut de l'étape.")
                return

        # Insertion en base
        df.to_sql('clients', engine, if_exists='append', index=False)
        logger.info(f"  ✓ Ingestion réussie : {len(df)} lignes insérées dans 'clients'")
        
    except FileNotFoundError as e:
        logger.error(f"  ✗ Erreur fichier : {e}")
        raise
    except Exception as e:
        logger.error(f"  ✗ Erreur lors de l'ingestion de clients : {e}")
        raise


def ingest_compteurs(engine, data_dir):
    """
    Ingère le fichier CSV compteurs.csv dans la table compteurs.
    
    Dépendance : La table clients doit être pré-remplie (clé étrangère).
    
    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        Moteur de connexion à PostgreSQL
    data_dir : Path
        Chemin vers le dossier contenant les fichiers CSV
    
    Raises
    ------
    FileNotFoundError
        Si le fichier CSV n'existe pas
    Exception
        En cas d'erreur lors de l'insertion en base
    """
    csv_file = data_dir / "compteurs.csv"
    logger.info(f"[2/4] Début de l'ingestion de {csv_file.name}...")
    
    try:
        if not csv_file.exists():
            raise FileNotFoundError(f"Fichier {csv_file} non trouvé")
        
        # Lecture du CSV
        df = pd.read_csv(csv_file)
        logger.info(f"  → {len(df)} lignes lues depuis {csv_file.name}")

        # Éviter les doublons : filtrer les id_pdl déjà présents en base
        existing = get_existing_pks(engine, 'compteurs', 'id_pdl')
        if existing:
            before = len(df)
            # CSV peut utiliser une colonne nommée 'id_pdl' ou 'id_pdl' correspondant au schéma
            if 'id_pdl' in df.columns:
                df = df[~df['id_pdl'].isin(existing)]
            elif 'id_compteur' in df.columns:
                df = df[~df['id_compteur'].isin(existing)]
            logger.info(f"  → {len(existing)} clés existantes trouvées, {len(df)} lignes restant après déduplication")
            if df.empty:
                logger.info("  → Aucune nouvelle ligne à insérer pour 'compteurs'; saut de l'étape.")
                return

        # Insertion en base
        df.to_sql('compteurs', engine, if_exists='append', index=False)
        logger.info(f"  ✓ Ingestion réussie : {len(df)} lignes insérées dans 'compteurs'")
        
    except FileNotFoundError as e:
        logger.error(f"  ✗ Erreur fichier : {e}")
        raise
    except Exception as e:
        logger.error(f"  ✗ Erreur lors de l'ingestion de compteurs : {e}")
        raise


def ingest_meteo(engine, data_dir):
    """
    Ingère le fichier CSV meteo.csv dans la table meteo.
    
    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        Moteur de connexion à PostgreSQL
    data_dir : Path
        Chemin vers le dossier contenant les fichiers CSV
    
    Raises
    ------
    FileNotFoundError
        Si le fichier CSV n'existe pas
    Exception
        En cas d'erreur lors de l'insertion en base
    """
    csv_file = data_dir / "meteo.csv"
    logger.info(f"[3/4] Début de l'ingestion de {csv_file.name}...")
    
    try:
        if not csv_file.exists():
            raise FileNotFoundError(f"Fichier {csv_file} non trouvé")
        
        # Lecture du CSV
        df = pd.read_csv(csv_file)
        logger.info(f"  → {len(df)} lignes lues depuis {csv_file.name}")

        # Calcul métier du Degré-Jour de Chauffage (DJU)
        if 'temp_moyenne_c' not in df.columns:
            raise ValueError("Colonne 'temp_moyenne_c' manquante dans le fichier meteo.csv")

        missing_temp = df['temp_moyenne_c'].isna().sum()
        if missing_temp > 0:
            logger.warning(
                f"  ⚠️ {missing_temp} valeurs manquantes de temp_moyenne_c détectées ; DJU fixé à 0.0 sur ces lignes"
            )

        df['dju_chauffage'] = np.where(
            df['temp_moyenne_c'] < 17.0,
            17.0 - df['temp_moyenne_c'],
            0.0,
        )
        df['dju_chauffage'] = df['dju_chauffage'].round(1).fillna(0.0)
        logger.info(
            f"  ✓ Calcul Métier OK : Variable DJU calculée avec succès pour {len(df)} lignes de météo."
        )

        # Déduplication locale sur la clé primaire composite (date, zone)
        if df.duplicated(subset=['date', 'zone']).any():
            before = len(df)
            df = df.drop_duplicates(subset=['date', 'zone'])
            logger.info(f"  → {before - len(df)} doublons internes supprimés, {len(df)} lignes restantes")

        # Filtrer les lignes déjà présentes en base pour éviter les conflits de clé primaire
        existing = get_existing_pk_pairs(engine, 'meteo', ['date', 'zone'])
        if existing:
            before = len(df)
            df = df[~df.set_index(['date', 'zone']).index.isin(existing)]
            logger.info(f"  → {len(existing)} lignes existantes trouvées en base, {len(df)} lignes restantes après déduplication")
            if df.empty:
                logger.info("  → Aucune nouvelle ligne à insérer pour 'meteo'; saut de l'étape.")
                return

        # Insertion en base par lots avec fallback vers une insertion plus compacte
        try:
            df.to_sql('meteo', engine, if_exists='append', index=False, method='multi', chunksize=50)
        except Exception:
            logger.warning(
                "  ⚠️ Échec de l'insertion multi-lignes ; tentative avec la méthode par défaut et des paquets plus petits..."
            )
            df.to_sql('meteo', engine, if_exists='append', index=False, chunksize=10)

        logger.info(f"  ✓ Ingestion réussie : {len(df)} lignes insérées dans 'meteo' (par lots)")
        
    except FileNotFoundError as e:
        logger.error(f"  ✗ Erreur fichier : {e}")
        raise
    except Exception as e:
        logger.error(f"  ✗ Erreur lors de l'ingestion de meteo : {e}")
        raise


def ingest_releves_consommation(engine, data_dir):
    """
    Ingère le fichier CSV releves_consommation.csv dans la table releves_consommation.
    
    ⚠️ ATTENTION : Cette table contient +500 000 lignes (volumétrie très élevée).
    Utilise chunksize=10000 pour fragmenter l'insertion et éviter l'explosion mémoire.
    
    Dépendance : La table compteurs doit être pré-remplie (clé étrangère).
    
    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        Moteur de connexion à PostgreSQL
    data_dir : Path
        Chemin vers le dossier contenant les fichiers CSV
    
    Raises
    ------
    FileNotFoundError
        Si le fichier CSV n'existe pas
    Exception
        En cas d'erreur lors de l'insertion en base
    """
    csv_file = data_dir / "releves_consommation.csv"
    logger.info(f"[4/4] Début de l'ingestion de {csv_file.name}...")
    logger.info(f"      ⚠️  Attention : volumétrie élevée (+500k lignes), chunksize=10000...")
    
    try:
        if not csv_file.exists():
            raise FileNotFoundError(f"Fichier {csv_file} non trouvé")
        
        # Lecture du CSV
        df = pd.read_csv(csv_file)
        logger.info(f"  → {len(df)} lignes lues depuis {csv_file.name}")

        # Supprimer les doublons exacts sur la clé primaire composite (id_pdl, date)
        if df.duplicated(subset=['id_pdl', 'date']).any():
            before = len(df)
            df = df.drop_duplicates(subset=['id_pdl', 'date'])
            logger.info(f"  → {before - len(df)} doublons supprimés sur (id_pdl, date), {len(df)} lignes restantes")

        # Imputation des consommations manquantes avant insertion
        df = impute_missing_consumption(df)

        # Insertion en base avec chunksize pour optimisation mémoire
        df.to_sql('releves_consommation', engine, if_exists='append', index=False, chunksize=10000)
        logger.info(f"  ✓ Ingestion réussie : {len(df)} lignes insérées dans 'releves_consommation'")
        logger.info(f"      (fragmentée en paquets de 10 000 lignes)")
        
    except FileNotFoundError as e:
        logger.error(f"  ✗ Erreur fichier : {e}")
        raise
    except Exception as e:
        logger.error(f"  ✗ Erreur lors de l'ingestion de releves_consommation : {e}")
        raise


def run_pipeline():
    """
    Point d'entrée principal du pipeline ETL.
    
    Orchestration des étapes :
    1. Initialisation et test de connexion PostgreSQL
    2. Ingestion des données CSV dans les tables (respect des dépendances FK)
    3. Affichage du résumé d'exécution
    """
    logger.info("=" * 80)
    logger.info("Démarrage du Pipeline ETL Neovolt - INGESTION BRUTE")
    logger.info("=" * 80)
    
    try:
        # Obtenir le moteur de base de données
        engine = get_db_engine()
        
        # Attendre la disponibilité de PostgreSQL
        wait_for_db(engine)
        
        # Test de connexion
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            pg_version = result.fetchone()[0]
            logger.info(f"✓ Connecté à : {pg_version}")
        
        logger.info("")
        logger.info("Étapes d'ingestion :")
        logger.info("-" * 80)
        
        # Déterminer le chemin du dossier donnees/
        data_dir = project_root / "donnees"
        
        if not data_dir.exists():
            logger.error(f"✗ Dossier {data_dir} n'existe pas")
            raise FileNotFoundError(f"Dossier {data_dir} introuvable")
        
        # Ingestion dans l'ordre des dépendances FK
        ingest_clients(engine, data_dir)
        ingest_compteurs(engine, data_dir)
        ingest_meteo(engine, data_dir)
        ingest_releves_consommation(engine, data_dir)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✓ Pipeline d'ingestion brute terminé avec SUCCÈS")
        logger.info("=" * 80)
        
        return engine
        
    except ValueError as e:
        logger.error(f"✗ Erreur de configuration : {e}")
        raise
    except FileNotFoundError as e:
        logger.error(f"✗ Erreur fichier : {e}")
        raise
    except Exception as e:
        logger.error(f"✗ Erreur lors de l'exécution du pipeline : {e}")
        raise


if __name__ == "__main__":
    try:
        engine = run_pipeline()
    except Exception as e:
        logger.error(f"✗ Le pipeline s'est arrêté avec une erreur : {e}")
        exit(1)

