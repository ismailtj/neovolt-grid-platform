# Pipeline ETL - Neovolt

Pipeline d'ingestion et de nettoyage des données énergétiques pour la plateforme Neovolt.

## Installation

### Prérequis

- Python 3.8+
- PostgreSQL (conteneurisé via Docker Compose)
- Git

### 1. Créer un Environnement Virtuel

Pour éviter les conflits de dépendances, crée un environnement virtuel dédié au pipeline.

**Windows :**
```bash
cd pipeline
python -m venv .venv
.\.venv\Scripts\activate
```

**Mac / Linux :**
```bash
cd pipeline
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Installer les Dépendances

Une fois l'environnement virtuel activé :

```bash
pip install -r requirements.txt
```

### 3. Vérifier l'Installation

```bash
python etl_pipeline.py
```

Tu devrais voir :
```
[INFO] Variables d'environnement chargées depuis c:\...\exam final\.env
[INFO] Création du moteur PostgreSQL : localhost:5432/neovolt_grid_db
[INFO] Connecté à : PostgreSQL 15.x on ...
[INFO] Pipeline initialisé avec succès, prêt pour l'ingestion
```

## Structure des Fichiers

```
pipeline/
├── requirements.txt        # Dépendances Python
├── etl_pipeline.py        # Script principal du pipeline
├── README.md              # Cette documentation
└── (futurs modules ETL)
```

## Dépendances

| Paquet | Version | Utilité |
|--------|---------|---------|
| `pandas` | >= 2.0.0 | Manipulation et nettoyage des données |
| `sqlalchemy` | >= 2.0.0 | ORM et gestion des connexions BD |
| `psycopg2-binary` | >= 2.9.0 | Connecteur PostgreSQL natif |
| `python-dotenv` | >= 1.0.0 | Chargement sécurisé du `.env` |

## Utilisation

### Lancer le Pipeline

```bash
python pipeline/etl_pipeline.py
```

### Désactiver l'Environnement Virtuel

```bash
# Windows
.\.venv\Scripts\deactivate

# Mac / Linux
deactivate
```

## Architecture du Pipeline

Le pipeline suit une structure ETL classique :

1. **Extract** : Extraction des données depuis PostgreSQL (table `releves_consommation`, `clients`, etc.)
2. **Transform** : Nettoyage, validation et enrichissement des données avec Pandas
3. **Load** : Chargement des données transformées dans la BD

### Fonction `get_db_engine()`

Crée et retourne un moteur SQLAlchemy configuré automatiquement via les variables `.env`.

```python
engine = get_db_engine()  # Récupère un Engine prêt à l'emploi
```

### Fonction `run_pipeline()`

Point d'entrée principal du pipeline. Initialise le moteur BD et teste la connexion.

```python
engine = run_pipeline()  # Lance le pipeline et retourne l'Engine
```

## Développement

### Ajouter une Étape ETL

```python
def extract_data(engine):
    """Extrait les données depuis PostgreSQL"""
    query = "SELECT * FROM releves_consommation LIMIT 1000"
    df = pd.read_sql(query, engine)
    return df

def transform_data(df):
    """Nettoie et transforme les données"""
    # Ajoute ici la logique de transformation
    return df

def load_data(df, engine):
    """Charge les données dans PostgreSQL"""
    df.to_sql('table_output', engine, if_exists='append', index=False)
```

## Troubleshooting

### Erreur : `Variables d'environnement manquantes`

Vérifie que le fichier `.env` existe à la racine et contient :
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST` (optionnel, défaut: localhost)
- `POSTGRES_PORT` (optionnel, défaut: 5432)

### Erreur : `ModuleNotFoundError: No module named 'pandas'`

L'environnement virtuel n'est pas activé. Relance :
```bash
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### Erreur de Connexion PostgreSQL

```bash
# Vérifie que PostgreSQL est en exécution
docker-compose ps

# Teste la connectivité
docker exec neovolt_postgres pg_isready -U neovolt_service
```

## Documentation SQLAlchemy

- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [PostgreSQL Dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)

## Documentation Pandas

- [Pandas Documentation](https://pandas.pydata.org/docs/)
