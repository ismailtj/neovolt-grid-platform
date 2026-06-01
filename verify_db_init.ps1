# ============================================================================
# Script de Vérification Automatisée - Initialisation PostgreSQL
# ============================================================================
# Ce script vérifie que les tables Neovolt ont été créées correctement
# lors du premier lancement du conteneur PostgreSQL via init.sql

# Charger les variables d'environnement depuis .env
$env_file = ".\.env"
if (-not (Test-Path $env_file)) {
    Write-Host "Erreur : Fichier .env non trouvé." -ForegroundColor Red
    exit 1
}

# Parser les variables .env
$env_vars = @{}
Get-Content $env_file | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        $env_vars[$key] = $value
    }
}

$POSTGRES_DB = $env_vars["POSTGRES_DB"]
$POSTGRES_USER = $env_vars["POSTGRES_USER"]

if (-not $POSTGRES_DB -or -not $POSTGRES_USER) {
    Write-Host "Erreur : POSTGRES_DB ou POSTGRES_USER manquants dans .env" -ForegroundColor Red
    exit 1
}

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Vérification de l'initialisation PostgreSQL Neovolt" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier que le conteneur est en running
Write-Host "[1] Vérification du statut du conteneur..." -ForegroundColor Yellow
$container_status = docker ps --filter "name=neovolt_postgres" --format "{{.Status}}"
if ([string]::IsNullOrEmpty($container_status)) {
    Write-Host "Erreur : Conteneur neovolt_postgres non trouvé en exécution." -ForegroundColor Red
    exit 1
}
Write-Host "    ✓ Conteneur en cours d'exécution : $container_status" -ForegroundColor Green
Write-Host ""

# Lister les tables créées
Write-Host "[2] Lister les tables de la base $POSTGRES_DB..." -ForegroundColor Yellow
$tables_output = docker exec neovolt_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors de l'exécution de la commande psql:" -ForegroundColor Red
    Write-Host $tables_output
    exit 1
}

Write-Host $tables_output
Write-Host ""

# Vérifier la présence des 4 tables obligatoires
Write-Host "[3] Vérification de la présence des tables attendues..." -ForegroundColor Yellow
$expected_tables = @("clients", "compteurs", "meteo", "releves_consommation")
$missing_tables = @()

foreach ($table in $expected_tables) {
    if ($tables_output -match "\| $table ") {
        Write-Host "    ✓ Table '$table' trouvée" -ForegroundColor Green
    } else {
        Write-Host "    ✗ Table '$table' MANQUANTE" -ForegroundColor Red
        $missing_tables += $table
    }
}

Write-Host ""
if ($missing_tables.Count -gt 0) {
    Write-Host "Erreur : Tables manquantes - $($missing_tables -join ', ')" -ForegroundColor Red
    exit 1
} else {
    Write-Host "============================================================================" -ForegroundColor Green
    Write-Host "✓ SUCCÈS : Toutes les tables Neovolt sont présentes et correctement initialisées !" -ForegroundColor Green
    Write-Host "============================================================================" -ForegroundColor Green
    exit 0
}
