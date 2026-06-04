"""
Pont vers PostgreSQL : lit la base en SQL et renvoie un DataFrame pandas.
Aligne sur les memes variables que etl_pipeline.py (POSTGRES_*) lues depuis .env.
Usage dans n'importe quel script de src/ :  from db import lire_sql
"""
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

# Charge le .env de la racine du projet (memes variables que l'ETL)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

def _url():
    user = os.getenv("POSTGRES_USER", "neovolt")
    pwd  = os.getenv("POSTGRES_PASSWORD", "neovolt")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db   = os.getenv("POSTGRES_DB", "neovolt")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"

# Un seul moteur reutilise par toutes les requetes
engine = create_engine(_url(), echo=False)

def lire_sql(query, params=None):
    """Execute une requete SELECT et renvoie un DataFrame pandas."""
    return pd.read_sql(text(query), engine, params=params)