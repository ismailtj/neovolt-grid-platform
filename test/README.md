# Tests Infrastructure - Neovolt

Dossier centralisé pour les scripts de test et vérification de la plateforme.

## Installation des Dépendances

### Prérequis Système

- Python 3.8+
- Docker et Docker Compose
- Fichier `.env` à la racine du projet

### 1. Créer un Environnement Virtuel (Recommandé)

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Installer les Dépendances

```bash
pip install -r requirements.txt
```

Cela installe :
- `python-dotenv==1.0.0` : Chargement des variables `.env`
- `psycopg2-binary==2.9.9` : Adaptateur PostgreSQL pour Python

---

## Test de Connectivité PostgreSQL

### Fichier : `test_db_connection.py`

Teste la connexion à PostgreSQL en utilisant `psycopg2`.

**Pré-requis :**
```bash
pip install python-dotenv psycopg2-binary
```

**Exécution :**
```bash
python test/test_db_connection.py
```

**Résultat attendu :**
```
Systèm technique OK : Connexion réussie à la base PostgreSQL de Néovolt !
```

---

## Vérification Initialisation Base de Données

### Fichier : `verify_db_init.bat`

Vérifie que les 4 tables du schéma Neovolt ont été créées lors du premier lancement du conteneur PostgreSQL.

**Pré-requis :**
- Docker Compose en cours d'exécution (`docker-compose up -d`)
- Fichier `.env` à la racine du projet

**Exécution :**
```bash
.\test\verify_db_init.bat
```

**Étapes du script :**
1. Vérifie le statut du conteneur `neovolt_postgres` (doit être `healthy`)
2. Liste les tables de la base `neovolt_grid_db`
3. Valide la présence des 4 tables obligatoires :
   - `clients`
   - `compteurs`
   - `meteo`
   - `releves_consommation`

**Résultat attendu :**
```
[OK] SUCCES : Toutes les tables Neovolt sont presentes et correctement initialisees !
```

---

## Procédure Complète de Test

Après avoir relancé les services, exécute cet ordre :

```bash
# 1. Arrêter et nettoyer
docker-compose down -v

# 2. Relancer les services
docker-compose up -d

# 3. Attendre que le conteneur soit healthy
docker-compose ps

# 4. Vérifier l'initialisation base
.\test\verify_db_init.bat

# 5. Tester la connectivité Python
python test/test_db_connection.py
```

## Code de Sortie

- **0** : Succès (tous les tests passent)
- **1** : Erreur (consulte les logs)

```bash
# Vérifier le code de sortie (Windows)
echo %ERRORLEVEL%  # Après exécution du .bat

# Linux/Mac
echo $?  # Après exécution d'un script shell
```
