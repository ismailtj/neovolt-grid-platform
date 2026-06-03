# API

This folder contains the FastAPI application for the Néovolt grid platform.

## Setup

1. Install dependencies:
   ```bash
   pip install -r api/requirements.txt
   ```

2. Ensure `.env` exists in the repository root and contains PostgreSQL credentials:
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`
   - `POSTGRES_DB`
   - `APP_ENV` (`development` or `production`)
   - `JWT_SECRET_KEY`
   - `JWT_ALGORITHM`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`
   - `AUTH_USERNAME`
   - `AUTH_PASSWORD`

## Run

```bash
uvicorn api.main:app --reload
```

## Run in Docker

To launch the API container after the database is ready, run:

```bash
docker compose up --build --force-recreate api
```

## 🔐 Système d'Authentification JWT

This API uses JWT-based authentication to protect sensitive endpoints.

### Variables d'environnement requises
- `JWT_SECRET_KEY` : secret fort utilisé pour signer les tokens.
- `JWT_ALGORITHM` : algorithme JWT (default `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES` : durée de vie du token en minutes (default `60`).
- `AUTH_USERNAME` : identifiant prototype pour la connexion (default `admin`).
- `AUTH_PASSWORD` : mot de passe prototype (default `admin123`).

### Flux d'authentification
1. Envoyer une requête `POST /auth/login` avec des identifiants via `form-data` ou `x-www-form-urlencoded`.
2. Le serveur répond avec un token JWT :
   ```json
   {"access_token": "<TOKEN>", "token_type": "bearer"}
   ```
3. Pour appeler une route protégée comme `GET /stats/global`, ajouter l'en-tête HTTP :
   ```http
   Authorization: Bearer <TOKEN>
   ```

### Exemple `curl`

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

```bash
curl -X GET "http://localhost:8000/stats/global" \
  -H "Authorization: Bearer <TOKEN>"
```

### Swagger / OpenAPI

Swagger et OpenAPI sont accessibles uniquement en mode développement (`APP_ENV=development`). En production (`APP_ENV=production`), la documentation est désactivée pour renforcer la sécurité.

1. Ouvrez `http://localhost:8000/docs`.
2. Dans Swagger, vous verrez le groupe `auth` avec les endpoints :
   - `POST /auth/login`
   - `GET /auth/register`
   - `POST /auth/register`
3. Cliquez sur le bouton `Authorize` en haut à droite.
4. Saisissez `Bearer <TOKEN>` dans la fenêtre d'autorisation.
5. Les routes protégées afficheront un cadenas et accepteront votre token.

### Utilisation de l'authentification dans Swagger

- `POST /auth/login` est exposé dans Swagger et accepte les champs `username` et `password`.
- `GET /auth/register` affiche le formulaire HTML de test.
- `POST /auth/register` crée un nouvel utilisateur de test avec `username` et `password`.

### Route d'enregistrement de test

- `GET /auth/register` : affiche un formulaire HTML simple pour ajouter un nouvel utilisateur en mode développement.
- `POST /auth/register` : enregistre un nouvel utilisateur avec `username` et `password`.

> Cette route est prévue uniquement pour les tests et le prototypage. En production, la création de compte doit être gérée via un processus sécurisé avec vérification d'email, confirmation de mot de passe, gestion des rôles et protections contre les créations non autorisées.

## Endpoints

- `GET /` - API status check
- `GET /health/db` - PostgreSQL connectivity health check
