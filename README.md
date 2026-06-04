# Plateforme de Données d'Énergie - Néovolt

Prototype d'une plateforme de valorisation des données d'un distributeur d'énergie
régional (600 000 points de livraison). Le projet centralise les données dans une base
PostgreSQL, produit des analyses et tableaux de bord décisionnels, et entraîne deux
modèles de machine learning : détection de fraude et prévision de consommation.

## Architecture

- **Conteneur Database** : PostgreSQL 15-Alpine avec schéma relationnel Neovolt
- **Interface Admin** : pgAdmin 4 pour gestion/manipulation de la base
- **API** : FastAPI (à développer)
- **Données** : Clients, Compteurs, Météo, Relevés de Consommation

## Démarrage Rapide

### 1. Configuration Initiale

Assure-toi que le fichier `.env` existe à la racine avec les variables :

```bash
POSTGRES_DB=neovolt_grid_db
POSTGRES_USER=neovolt_service
POSTGRES_PASSWORD=N3oV0lt!Svc#2026aBz
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
PGADMIN_DEFAULT_EMAIL=admin@neovolt.io
PGADMIN_DEFAULT_PASSWORD=N3oV0lt!PgAdm#2026xYz
```

### 1.5 Installation des Dépendances Python (Optionnel - pour les tests)

Si tu veux lancer les scripts de test Python (`test/test_db_connection.py`) :

```bash
# Créer un environnement virtuel (recommandé)
python -m venv .venv
.\.venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

> Note : ce fichier `requirements.txt` pointe vers `pipeline/requirements.txt`.

### 2. Démarrage des Services

```bash
docker-compose up -d
```

Les services démarrent en arrière-plan.

## Réinitialisation Complète de la Base de Données

### Procédure Détaillée

Utilise cette procédure pour **réinitialiser complètement la base à blanc** et vérifier que le schéma s'applique correctement :

#### Étape 1 : Arrêter et Nettoyer

```bash
docker-compose down -v
```

Cela :
- Arrête tous les conteneurs (`database` et `pgadmin`)
- Supprime les volumes nommés (`postgres_data` et `pgadmin_data`) → **la base est à blanc**
- Conserve les images Docker (pas de ré-téléchargement)

#### Étape 2 : Reconstruire et Lancer

```bash
docker-compose up -d
```

Docker va :
1. Créer les volumes `postgres_data` et `pgadmin_data`
2. Lancer le conteneur PostgreSQL
3. Exécuter automatiquement le script `/docker-entrypoint-initdb.d/init.sql` (monté depuis `./scripts_sql/init.sql`)
4. Créer les 4 tables : `clients`, `compteurs`, `meteo`, `releves_consommation`
5. Créer les indexes de performance
6. Appliquer tous les commentaires SQL et contraintes

#### Étape 3 : Vérifier que PostgreSQL est "Healthy"

```bash
docker-compose ps
```

Attends que le conteneur `database` affiche un statut `healthy` (vérification du healthcheck) :

```
NAME                   STATUS
neovolt_postgres       Up ... (healthy)
neovolt_pgadmin        Up ...
```

#### Étape 4 : Lancer le Script de Vérification

```bash
.\test\verify_db_init.bat
```

Ce script :
- Lit les variables `.env` dynamiquement
- Exécute `docker exec neovolt_postgres psql -U neovolt_service -d neovolt_grid_db -c "\dt"`
- Affiche toutes les tables créées
- Vérifie la présence des 4 tables obligatoires
- Renvoie un code de sortie `0` si succès, `1` si erreur

**Résultat attendu :**

```
============================================================================
Vérification de l'initialisation PostgreSQL Neovolt
============================================================================

[1] Vérification du statut du conteneur...
    ✓ Conteneur en cours d'exécution : Up 30 seconds (healthy)

[2] Lister les tables de la base neovolt_grid_db...
 schema |      name       | type  | owner
--------+-----------------+-------+----------------
 public | clients         | table | neovolt_service
 public | compteurs       | table | neovolt_service
 public | meteo           | table | neovolt_service
 public | releves_consommation | table | neovolt_service

[3] Vérification de la présence des tables attendues...
    ✓ Table 'clients' trouvée
    ✓ Table 'compteurs' trouvée
    ✓ Table 'meteo' trouvée
    ✓ Table 'releves_consommation' trouvée

============================================================================
✓ SUCCÈS : Toutes les tables Neovolt sont présentes et correctement initialisées !
============================================================================
```

## Charger les données (ETL)

```bash
python pipeline/etl_pipeline.py
```

Le pipeline nettoie les CSV (déduplication, imputation des valeurs manquantes/négatives,
calcul du degré-jour de chauffage) puis charge les tables dans l'ordre des dépendances :
`clients → compteurs → meteo → releves_consommation`. Il est **idempotent** : relançable
sans erreur ni doublon.
 
Résultat attendu : 700 clients, 700 compteurs, 5 848 lignes météo, 511 700 relevés.

## Analyses & modèles (lisent la base)

```bash
python src/03_table_analytique.py   # → outputs/table_analytique.parquet
python src/04_analyses.py           # statistiques descriptives (console)
python src/05_dashboard.py          # → outputs/dashboard_neovolt.html
python src/06_fraude_features.py    # → outputs/features_fraude.csv
python src/07_fraude_isolation.py   # détection non supervisée + baseline
python src/08_fraude_supervise.py   # → outputs/suspects_fraude.csv
python src/09_prevision.py          # → outputs/prevision_test.csv
python src/10_mlops.py              # → outputs/models/ (modèles + model_card.json)
python src/11_pipeline.py           # → outputs/pipeline.log
```

Ouvrir `outputs/dashboard_neovolt.html` dans un navigateur pour le tableau de bord interactif.

## Base de données
 
Quatre tables (voir `scripts_sql/init.sql`) :
 
| Table | Description | Clé primaire |
|---|---|---|
| `clients` | Métadonnées commerciales et géographiques | `id_client` |
| `compteurs` | Points de livraison (PDL) | `id_pdl` |
| `meteo` | Observations quotidiennes par zone + DJU | `(date, zone)` |
| `releves_consommation` | Table de faits (+500k lignes) | `(id_pdl, date)` |
 
Les contraintes `CHECK` et les clés étrangères garantissent la qualité : c'est l'ETL
qui rend les données conformes (nettoyage) avant le chargement.
 
## Résultats clés
 
**Analyse (Data Analyst).** La consommation est ~25 % plus élevée en hiver. La sensibilité
au froid est portée par les clients chauffés à l'électricité : corrélation
consommation/degré-jour de **+0,69** (contre +0,14 pour le gaz). Satisfaction client
moyenne basse (2,45/5) relevée dans les réclamations.
 
**Détection de fraude (Data Scientist).** Modèle Random Forest, **ROC-AUC 0,92**. Au seuil
recommandé (0,20), il signale ~37 compteurs et retrouve ~79 % des fraudes connues. La
variable la plus discriminante est la **chute de consommation** (`ratio_chute`).
 
**Prévision de consommation (Data Scientist).** Régression à J+1, **erreur moyenne ~4,5 %**
(MAPE), meilleure que la baseline saisonnière (6,1 %). Validation chronologique.

## Choix techniques notables
 
- **PostgreSQL comme source de vérité unique** : une seule base cohérente, lue par tous les composants.
- **Nettoyage par imputation** : les valeurs manquantes/négatives sont remplacées par la
  moyenne du compteur (puis de la zone, puis globale) — la base est complète et directement exploitable.
- **Pipeline idempotent** : relançable sans corrompre les données (vérification des clés déjà présentes).
- **Approche « baseline d'abord »** en ML : une règle simple est systématiquement comparée
  aux modèles ; la complexité n'est retenue que si elle apporte une valeur mesurable.
- **Métriques adaptées au déséquilibre** : précision, rappel, PR-AUC et recall@N pour la
  fraude (l'exactitude serait trompeuse avec 96 % de compteurs sains).


## Accès aux Services

### PostgreSQL (Port 5432)

- **Host** : `localhost` ou `database` (depuis pgAdmin)
- **Port** : `5432`
- **Database** : `neovolt_grid_db`
- **User** : `neovolt_service`
- **Password** : Voir `.env`

### pgAdmin (Port 8080)

- **URL** : `http://localhost:8080`
- **Email** : Voir `.env` (ex: `admin@neovolt.io`)
- **Password** : Voir `.env`

**Configuration du serveur PostgreSQL dans pgAdmin :**
- Host name/address : `database`
- Port : `5432`
- Maintenance database : `postgres` ou `neovolt_grid_db`
- Username : `neovolt_service`
- Password : (depuis `.env`)

## Scripts Utiles

### Tester la Connectivité à PostgreSQL

```bash
pip install python-dotenv psycopg2-binary
python test/test_db_connection.py
```

### Consulter les Logs du Conteneur

```bash
docker logs -f neovolt_postgres --tail 100
```

### Accéder directement à la CLI PostgreSQL

```bash
docker exec -it neovolt_postgres psql -U neovolt_service -d neovolt_grid_db
```

## Fichiers Clés

- `.gitignore` : Exclusions Git (secrets, données, volumes locaux)
- `.env` : Variables d'environnement (NE JAMAIS committer)
- `requirements.txt` : Dépendances Python (pour tests)
- `docker-compose.yml` : Orchestration des conteneurs (database + pgAdmin)
- `scripts_sql/init.sql` : Schéma relationnel Neovolt (4 tables, indexes, contraintes)
- `test/test_db_connection.py` : Test de connectivité Python
- `test/verify_db_init.bat` : Vérification Batch post-initialisation
- `test/README.md` : Documentation des tests

## Documentation Schéma

Le schéma `init.sql` contient :

- **Table `clients`** : Métadonnées commerciales (700 clients max)
- **Table `compteurs`** : Points de livraison (PDL / compteurs) avec zones et types
- **Table `meteo`** : Données météo quotidiennes par zone (températures, DJU chauffage)
- **Table `releves_consommation`** : Fait principal (500k+ lignes) — consommations quotidiennes

Toutes les tables incluent :
- Contraintes CHECK nommées pour validation
- Commentaires SQL pour documentation
- Indexes B-Tree pour performance analytique
- Clés étrangères avec cascade deletion

## Troubleshooting

### Le conteneur PostgreSQL ne démarre pas

```bash
docker logs neovolt_postgres
```

Vérifie que le fichier `./scripts_sql/init.sql` existe et est accessible.

### Les tables ne sont pas créées après `docker-compose up`

- Vérifie le statut healthcheck : `docker-compose ps`
- Attends quelques secondes (init peut prendre du temps)
- Relance : `docker-compose down -v && docker-compose up -d`
- Consulte les logs : `docker logs neovolt_postgres`

### pgAdmin n'accède pas à PostgreSQL

- Utilise `database` comme Host (pas `localhost`)
- Vérifie les identifiants dans `.env`
- Reconnecte le serveur dans pgAdmin interface

## Sécurité

- ⚠️ **NE JAMAIS committer `.env`** — secrets et mots de passe
- ⚠️ **NE JAMAIS pousser les volumes** (`postgres_data/`, `pgadmin_data/`)
- Utilise des mots de passe forts en production
- Chiffre le transport réseau (SSL/TLS) si multi-hôte
