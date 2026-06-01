@echo off
REM ============================================================================
REM Script de Vérification Automatisée - Initialisation PostgreSQL
REM Wrapper Batch pour contourner les restrictions ExecutionPolicy PowerShell
REM ============================================================================

setlocal enabledelayedexpansion

REM Vérifier que .env existe
if not exist ".env" (
    echo Erreur : Fichier .env non trouve.
    exit /b 1
)

REM Lire les variables depuis .env
for /f "delims== tokens=1,2" %%a in (.env) do (
    set "%%a=%%b"
)

if not defined POSTGRES_DB (
    echo Erreur : POSTGRES_DB manquant dans .env
    exit /b 1
)

if not defined POSTGRES_USER (
    echo Erreur : POSTGRES_USER manquant dans .env
    exit /b 1
)

echo ============================================================================
echo Verification de l'initialisation PostgreSQL Neovolt
echo ============================================================================
echo.

REM [1] Verifier que le conteneur est en running
echo [1] Verification du statut du conteneur...
for /f "delims=" %%i in ('docker ps --filter "name=neovolt_postgres" --format "{{.Status}}" 2^>nul') do set "container_status=%%i"

if "!container_status!"=="" (
    echo.    X Conteneur neovolt_postgres non trouve en execution.
    exit /b 1
)
echo.    [OK] Conteneur en cours d'execution : !container_status!
echo.

REM [2] Lister les tables creees
echo [2] Lister les tables de la base !POSTGRES_DB!...
docker exec neovolt_postgres psql -U !POSTGRES_USER! -d !POSTGRES_DB! -c "\dt" 2>nul
if !ERRORLEVEL! neq 0 (
    echo.
    echo Erreur lors de l'execution de la commande psql
    exit /b 1
)
echo.

REM [3] Verifier la presence des 4 tables obligatoires
echo [3] Verification de la presence des tables attendues...

set "missing=0"

REM Verifier chaque table directement via psql
for %%t in (clients compteurs meteo releves_consommation) do (
    docker exec neovolt_postgres psql -U !POSTGRES_USER! -d !POSTGRES_DB! -c "SELECT 1 FROM information_schema.tables WHERE table_name='%%t'" 2>nul | findstr "1" >nul
    if !ERRORLEVEL! equ 0 (
        echo.    [OK] Table '%%t' trouvee
    ) else (
        echo.    [ERREUR] Table '%%t' MANQUANTE
        set "missing=1"
    )
)

echo.
if !missing! equ 1 (
    echo ============================================================================
    echo X ERREUR : Tables manquantes
    echo ============================================================================
    exit /b 1
) else (
    echo ============================================================================
    echo [OK] SUCCES : Toutes les tables Neovolt sont presentes et correctement initialisees !
    echo ============================================================================
    exit /b 0
)
