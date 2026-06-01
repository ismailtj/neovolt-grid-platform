@echo off
REM Test de connexion PostgreSQL depuis le conteneur Docker
REM Élimine le problème de réseau Windows/Docker

setlocal enabledelayedexpansion

echo ============================================================================
echo Test de Connexion PostgreSQL (depuis le conteneur)
echo ============================================================================
echo.

REM Lire les variables depuis .env
for /f "delims== tokens=1,2" %%a in (.env) do (
    set "%%a=%%b"
)

if not defined POSTGRES_DB (
    echo Erreur : POSTGRES_DB manquant dans .env
    exit /b 1
)

echo [*] Lancement du test depuis le conteneur neovolt_postgres...
echo.

REM Exécuter le test directement dans le conteneur
docker exec neovolt_postgres psql -U !POSTGRES_USER! -d !POSTGRES_DB! -c "SELECT 1" >nul 2>&1

if !ERRORLEVEL! equ 0 (
    echo ============================================================================
    echo [OK] SUCCES : Connexion reussie a PostgreSQL !
    echo ============================================================================
    exit /b 0
) else (
    echo ============================================================================
    echo [ERREUR] Impossible de se connecter a PostgreSQL
    echo ============================================================================
    echo.
    echo Suggestions :
    echo  1. Verifie que le conteneur est en execution : docker-compose ps
    echo  2. Verifie que le statut est 'healthy'
    echo  3. Consulte les logs : docker logs neovolt_postgres
    exit /b 1
)
