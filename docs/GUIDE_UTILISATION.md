# GUIDE D'UTILISATION — Plateforme Néovolt
## Démarrage, Configuration et Tests en 10 Minutes

---

## 1. Prérequis

Avant de commencer, assure-toi d'avoir installé sur ta machine :

| Composant | Version Min | Vérification |
|-----------|------------|--------------|
| **Docker Desktop** | 20.10+ | `docker --version` |
| **Docker Compose** | 2.0+ | `docker compose version` |
| **Git** (optionnel) | 2.30+ | `git --version` |
| **Postman** OU Navigateur | Dernière | Pour tester les requêtes HTTP |
| **PostgreSQL CLI** (optionnel) | 13+ | `psql --version` (pour accès direct DB) |

### Téléchargements
- **Docker Desktop** : https://www.docker.com/products/docker-desktop
- **Postman** : https://www.postman.com/downloads/
- **Git Bash** (Windows) : https://git-scm.com/download/win

---

## 2. Configuration de l'Environnement

### Étape 1 : Cloner le dépôt GitHub

Si tu n'as pas encore le projet localement, utilise :

```bash
git clone https://github.com/ismailtj/neovolt-grid-platform.git
```

Puis déplace-toi dans le dossier du projet :

```bash
cd neovolt-grid-platform
```

### Étape 2 : Créer le fichier `.env`

À la **racine du projet** (même niveau que `docker-compose.yml`), crée un fichier nommé `.env` avec exactement ce contenu :

```bash
# ============================================================================
# CONFIGURATION PostgreSQL (Database Container)
# ============================================================================
POSTGRES_DB=neovolt_grid_db
POSTGRES_USER=neovolt_service
POSTGRES_PASSWORD=N3oV0lt!Svc#2026aBz
POSTGRES_HOST=database
POSTGRES_PORT=5432

# ============================================================================
# CONFIGURATION pgAdmin (Admin Interface)
# ============================================================================
PGADMIN_DEFAULT_EMAIL=admin@neovolt.io
PGADMIN_DEFAULT_PASSWORD=N3oV0lt!PgAdm#2026xYz

# ============================================================================
# CONFIGURATION API FastAPI (REST API)
# ============================================================================
APP_ENV=development
JWT_SECRET_KEY=your-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Utilisateur de test par défaut (sera créé au démarrage API)
AUTH_USERNAME=admin
AUTH_PASSWORD=aa

```

> ⚠️ **IMPORTANT** : Ce fichier contient des **identifiants sensibles**. 
> - ✅ En **développement local** : OK comme ci-dessus
> - ❌ En **production** : Utiliser des mots de passe forts et des secrets vault

### Étape 3 : Vérifier la Structure

Ton projet doit ressembler à ceci :

```
neovolt-grid-platform/
├── .env                          ← Le fichier qu'on vient de créer
├── docker-compose.yml
├── README.md
├── donnees/
├── pipeline/
├── scripts_sql/
├── api/
└── test/
```

Si le fichier `.env` n'existe pas ou est mal placé, Docker Compose affichera :
```
ERROR: missing required environment variables (POSTGRES_DB, POSTGRES_USER, ...)
```

---

## 3. Procédure de Lancement — Étape par Étape

### Étape 1 : Ouvrir un Terminal

#### Sur **Windows**
- Appuie sur `Win + R`, tape `cmd`, puis Entrée
- Ou utilise **PowerShell**

#### Sur **macOS / Linux**
- Ouvre Terminal (Cmd + Espace → `terminal`)

### Étape 2 : Naviguer vers le Projet

```bash
cd "C:\Users\[tonUsername]\Documents\ESIC2\neovolt-grid-platform"
```

ou si tu as téléchargé ailleurs :

```bash
cd /chemin/vers/neovolt-grid-platform
```

### Étape 3 : Lancer l'Infrastructure Complète

```bash
docker compose up --build -d
```

**Ce qui se passe** :
- `--build` : Reconstruit les images Docker (API)
- `-d` : Démarre en arrière-plan (detached mode)

**Sortie attendue** :
```
[+] Building 15.3s (9/9) FINISHED
[+] Running 4/4
 ✓ Container neovolt_postgres    Started
 ✓ Container neovolt_pgadmin      Started
 ✓ Container neovolt_etl          Started
 ✓ Container neovolt_api          Started
```

### Étape 4 : Vérifier que Tous les Conteneurs Tournent

```bash
docker compose ps
```

**Résultat attendu** :
```
NAME                   COMMAND                  SERVICE     STATUS              PORTS
neovolt_postgres       "docker-entrypoint..."   database    Up 10s (healthy)    5432/tcp
neovolt_pgadmin        "/entrypoint.sh"         pgadmin     Up 8s               0.0.0.0:8080->80/tcp
neovolt_etl            "bash -c 'pip install..."python      Exited (0)          
neovolt_api            "uvicorn main:app..."    api         Up 5s               0.0.0.0:8000->8000/tcp
```

**Explications** :
- `neovolt_postgres` : **healthy** = base prête ✅
- `neovolt_pgadmin` : **Up** = interface admin accessible ✅
- `neovolt_etl` : **Exited (0)** = pipeline batch exécuté et terminé OK ✅
- `neovolt_api` : **Up** = API en écoute sur port 8000 ✅

### Étape 5 : Attendre l'Initialisation (⏱️ 30-60 sec)

Le conteneur PostgreSQL exécute le schéma SQL (`scripts_sql/init.sql`). Vérifie les logs :

```bash
docker logs neovolt_postgres --tail 20
```

Dès que tu vois :
```
LOG:  database system is ready to accept connections
```

→ C'est bon ! La base est initialisée.

---

## 4. Comment Tester l'Application

### Test 1 : Accéder à Swagger (Documentation Interactive)

Ouvre ton navigateur et accède à :

```
http://localhost:8000/docs
```

Tu devrais voir l'interface Swagger officielle de FastAPI avec :
- Liste de toutes les routes (auth, clients, compteurs, meteo, releves, stats)
- Description de chaque endpoint
- Zone pour tester directement les requêtes

**Écran attendu** :
```
    Swagger UI
    ═══════════════════════════════════════
    [Authorize] [Explore]
    
    auth
      POST   /auth/login
      GET    /auth/register
      POST   /auth/register
    
    clients
      GET    /clients
    
    compteurs
      GET    /compteurs
      GET    /compteurs/
    
    meteo
      GET    /meteo
      GET    /meteo/filtre
    
    releves
      GET    /releves
      GET    /releves/filtre
    
    stats
      GET    /stats/global
```

### Test 2 : Le Flux de Sécurité JWT (Login + Token)

#### 2.1 — Se logger et récupérer le Token

Dans Swagger, clique sur le bouton **`POST /auth/login`** :

1. Clique sur **"Try it out"**
2. Renseigne les champs :
   - **username** : `admin`
   - **password** : `aa`
3. Clique sur **"Execute"**

**Réponse attendue** :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTcxNDc0NDAwMH0.7h...",
  "token_type": "bearer"
}
```

Copie la valeur de `access_token` (elle commence par `eyJ...`).

#### 2.2 — Autoriser Swagger avec le Token

1. Clique sur le bouton bleu **"Authorize"** en haut à droite
2. Dans la fenêtre "Available authorizations", champs de texte au-dessous de `Bearer (HTTP)` :
   - Colle ton token :
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTcxNDc0NDAwMH0.7h...
   ```
3. Clique sur **"Authorize"** → Puis **"Close"**

Dès maintenant, tous les endpoints protégés afficheront un 🔒 **cadenas** et utiliseront ton token automatiquement.

#### 2.3 — Tester une Route Protégée

Clique sur **`GET /stats/global`** :

1. Clique **"Try it out"**
2. Clique **"Execute"**

**Réponse attendue** (si données pré-chargées) :
```json
{
  "consommation_totale_kwh": 123456.50,
  "consommation_moyenne_quotidienne": 45.23,
  "nombre_total_releves": 2730
}
```

Si tu **n'autorises pas** (pas de token) :
```json
{
  "detail": "Could not validate credentials"
}
```

### Test 3 : Requêtes Clés à Tester

#### Test 3.1 — Filtrer les Relevés par Zone et Dates

Dans Swagger, clique sur **`GET /releves/filtre`** :

1. **Try it out**
2. Renseigne les paramètres optionnels :
   - `zone` : `Val-Nord`
   - `date_debut` : `2024-01-01`
   - `date_fin` : `2024-01-31`
   - `limit` : `50`
3. **Execute**

**Réponse attendue** :
```json
[
  {
    "id_pdl": "PDL-000001",
    "date": "2024-01-01",
    "consommation_kwh": 25.50,
    "zone": "Val-Nord"
  },
  {
    "id_pdl": "PDL-000002",
    "date": "2024-01-01",
    "consommation_kwh": 18.75,
    "zone": "Val-Nord"
  }
]
```

#### Test 3.2 — Voir les Statistiques Globales

Clique sur **`GET /stats/global`** (protection JWT active) :

1. **Try it out** → **Execute**

Cela retourne les **agrégations** de **TOUTE** la base :
```json
{
  "consommation_totale_kwh": 523450.75,
  "consommation_moyenne_quotidienne": 191.5,
  "nombre_total_releves": 2730
}
```

#### Test 3.3 — Lister les Compteurs avec Pagination

Clique sur **`GET /compteurs`** :

1. **Try it out**
2. Paramètres :
   - `skip` : `0` (commence à l'enregistrement 0)
   - `limit` : `10` (retourner 10 compteurs)
3. **Execute**

**Réponse attendue** :
```json
[
  {
    "id_pdl": "PDL-000001",
    "id_client": "CLI-00001",
    "zone": "Val-Nord",
    "type_client": "residentiel",
    "puissance_souscrite_kva": 6,
    "type_chauffage": "electrique",
    "type_compteur": "communicant",
    "date_pose": "2022-03-15",
    "statut": "actif"
  },
  ...
]
```

---

## 5. Tester via Postman (Alternative à Swagger)

### Étape 1 : Importer la Collection

Postman peut être utilisé comme alternative à Swagger pour des tests plus avancés (scripts, environnements, etc.).

#### Créer manuellement une requête Login

1. Ouvre **Postman**
2. Clique sur **"+"** pour créer une nouvelle requête
3. Configure :
   - **Méthode** : `POST`
   - **URL** : `http://localhost:8000/auth/login`
   - **Headers** : 
     - `Content-Type: application/x-www-form-urlencoded`
   - **Body** → **form-data** :
     - `username` : `admin`
     - `password` : `aa`
4. Clique **"Send"**

**Réponse** :
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

#### Tester une Route Protégée avec le Token

1. Nouvelle requête **GET**
   - **URL** : `http://localhost:8000/stats/global`
   - **Headers** :
     - `Authorization: Bearer eyJ...` ← Colle ton token ici
2. Clique **"Send"**

**Réponse** :
```json
{
  "consommation_totale_kwh": 123456.50,
  ...
}
```

---

## 6. Accès à pgAdmin (Gestion Base de Données)

### Ouvrir pgAdmin

Va à : `http://localhost:8080`

**Identifiants** :
- Email : `admin@neovolt.io` (depuis `.env`)
- Mot de passe : `N3oV0lt!PgAdm#2026xYz` (depuis `.env`)

### Se Connecter à la Base PostgreSQL

1. Dans pgAdmin, dans le panneau gauche : **"Servers"** → clic droit → **"Register"** → **"Server..."**
2. **General tab** :
   - Name : `Neovolt`
3. **Connection tab** :
   - Host name/address : `database`
   - Port : `5432`
   - Maintenance database : `postgres`
   - Username : `neovolt_service`
   - Password : `N3oV0lt!Svc#2026aBz`
4. Clique **"Save"**

Maintenant tu vois la base et peux :
- Explorer les tables (`clients`, `compteurs`, `meteo`, `releves_consommation`, `users`)
- Écrire des requêtes SQL custom
- Éditer les données

---

## 7. Commandes Utiles

### Voir les Logs de l'API

```bash
docker logs -f neovolt_api --tail 50
```

Cela affiche les 50 dernières lignes en live (Ctrl+C pour quitter).

### Accéder à la CLI PostgreSQL Directement

```bash
docker exec -it neovolt_postgres psql -U neovolt_service -d neovolt_grid_db
```

Puis tu peux exécuter du SQL :
```sql
SELECT COUNT(*) FROM releves_consommation;
SELECT DISTINCT zone FROM compteurs ORDER BY zone;
\dt  -- Lister les tables
\q   -- Quitter
```

### Arrêter les Conteneurs

```bash
docker compose down
```

Cela arrête mais **ne supprime pas** les données PostgreSQL.

### Réinitialiser Complètement (Effacer la Base)

```bash
docker compose down -v
```

Le `-v` supprime aussi les volumes → base vide à la prochaine startup.

### Relancer après Reset

```bash
docker compose up --build -d
```

---

## 8. Troubleshooting

### Erreur : "Cannot connect to Docker daemon"

**Cause** : Docker Desktop n'est pas lancé.

**Solution** : Ouvre Docker Desktop → attends que le daemon soit prêt (2-3 min).

### Erreur : "ports already in use"

**Cause** : Les ports 5432, 8000, ou 8080 sont utilisés par une autre application.

**Solution** :
```bash
docker compose down -v  # Arrête tous les conteneurs
docker compose up --build -d  # Relance
```

### Base PostgreSQL ne démarre pas (unhealthy)

**Cause** : Le script `init.sql` a une erreur SQL.

**Solution** : Vérifie les logs
```bash
docker logs neovolt_postgres
```

Tu cherches des erreurs SQL comme `syntax error` ou `duplicate table`.

### API ne démarre pas (Container exits)

**Cause** : Importation Python échouée (dépendances manquantes ou erreur de syntaxe).

**Solution** :
```bash
docker logs neovolt_api
```

Regarde la stack trace Python.

### Je n'arrive pas à logger (401 Unauthorized)

**Cause 1** : Mauvais identifiant/mot de passe.
- Vérifie `.env` : `AUTH_USERNAME=admin`, `AUTH_PASSWORD=aa`

**Cause 2** : La table `users` n'a pas été créée.
- Réinitialise : `docker compose down -v && docker compose up -d`
- Attends 30 sec que `neovolt_postgres` passe à `healthy`

---

## 9. Flux Complet de Test (5 minutes)

```
1. docker compose up --build -d
   ↓ Attendre 30 sec (DB healthy)
   
2. Ouvrir http://localhost:8000/docs
   ↓
   
3. POST /auth/login (username: admin, password: aa)
   ↓ Copier le token
   
4. Cliquer "Authorize", coller le token
   ↓
   
5. GET /releves/filtre (zone: Val-Nord, date_debut: 2024-01-01)
   ↓ Voir les relevés de la zone
   
6. GET /stats/global
   ↓ Voir les agrégations totales
   
7. Clique "Logout"
   ↓ Essayer GET /stats/global sans token → 401 ✅
```

---

## 10. Pour les Enseignants 

### Objectifs de Validation

Nous avons conçu cette plateforme en tenant compte des critères suivants. Vous trouverez ci-dessous les éléments clés que vous pouvez explorer pour vérifier le bon fonctionnement de l'architecture :

| Aspect à Explorer | Suggestion de Test | Ce que cela démontre |
|---------|---|---|
| **Architecture Conteneurisée** | Exécuter `docker compose ps` pour vérifier que les 4 services sont actifs | ✅ Infrastructure reproductible et orchestrée |
| **Schéma Relationnel** | Accéder à pgAdmin (http://localhost:8080) et explorer les 5 tables | ✅ Normalisation des données, contraintes métier |
| **API REST Documentée** | Consulter Swagger (http://localhost:8000/docs) | ✅ Exposition claire des endpoints et de leurs contrats |
| **Authentification & Sécurité** | Effectuer un login via `/auth/login`, puis consulter une route protégée | ✅ Implémentation OAuth2 Bearer JWT |
| **Persistance des Données** | Utiliser GET /releves/filtre pour récupérer des données de la base | ✅ ETL en amont et requêtage SQL performant |
| **Contrôle d'Accès** | Tenter d'accéder à GET /stats/global sans token (résultat : 401) | ✅ Protection des endpoints sensibles |
| **Performance à l'Échelle** | Consulter GET /releves avec pagination (limit=100) | ✅ Gestion de volumétrie (500k+ lignes) sans dépassement mémoire |

### Fichiers Clés pour l'Évaluation

Vous trouverez la documentation technique et les justifications dans les fichiers suivants :

- **`RAPPORT.md`** → Analyse approfondie de l'architecture, justification des choix technologiques et focus méthodologiques
- **`scripts_sql/init.sql`** → Schéma relationnel complet avec contraintes et indexes B-Tree
- **`api/auth.py`** → Implémentation du protocole JWT et gestion sécurisée des utilisateurs
- **`api/routers/stats.py`** → Exemple d'agrégations performantes réalisées côté PostgreSQL
- **`docker-compose.yml` + `.env`** → Configuration et reproducibilité de l'infrastructure

### Étapes Suggérées pour la Découverte

1. **Démarrage rapide** : `docker compose up --build -d` (⏱️ ~30 sec d'attente)
2. **Vérification de l'infrastructure** : `docker compose ps` (tous les services doivent être UP)
3. **Test du flux complet** :
   - Swagger : http://localhost:8000/docs
   - Login avec `admin` / `aa`
   - Consulter les endpoints protégés
4. **Exploration des données** : pgAdmin (http://localhost:8080) pour inspecter les tables
5. **Validation de la sécurité** : Tenter d'accéder à `/stats/global` sans token

---

## Conclusion

La plateforme **Néovolt** offre une démonstration complète des principes de développement moderne : **architecture conteneurisée**, **API sécurisée**, **scalabilité** et **maintenabilité**.

Nous vous remercions de votre intérêt et restons disponible pour toute question technique.

Pour une assistance, veuillez consulter le `README.md` à la racine du projet.
