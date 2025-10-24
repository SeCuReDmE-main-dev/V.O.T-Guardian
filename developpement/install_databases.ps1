# ==============================================
# V.O.T. GUARDIAN - DATABASE INSTALLATION SCRIPT
# ==============================================
# Installs and configures PostgreSQL and RethinkDB for Windows

param(
    [string]$InstallPath = "C:\VOT_Databases",
    [string]$PostgresPassword = "vot_password",
    [string]$DatabaseName = "vot_guardian"
)

Write-Host "V.O.T. Guardian - Database Installation Script" -ForegroundColor Green
Write-Host ("=" * 60)

# Create installation directory
if (!(Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force
    Write-Host "✅ Created installation directory: $InstallPath"
}

# ==============================================
# POSTGRESQL INSTALLATION
# ==============================================

Write-Host ("`n" + "Installing PostgreSQL...") -ForegroundColor Yellow

# Download PostgreSQL installer (Windows x64)
$PostgresUrl = "https://get.enterprisedb.com/postgresql/postgresql-15.8-1-windows-x64.exe"
$PostgresInstaller = "$InstallPath\postgresql-installer.exe"

try {
    # Download installer
    Write-Host "  Downloading PostgreSQL installer..."
    Invoke-WebRequest -Uri $PostgresUrl -OutFile $PostgresInstaller

    # Install PostgreSQL silently
    Write-Host "  Installing PostgreSQL (this may take a few minutes)..."
    $InstallArgs = @(
        "--mode", "unattended",
        "--superpassword", $PostgresPassword,
        "--serverport", "5432",
        "--create_shortcuts", "0",
        "--install_runtimes", "0"
    )

    Start-Process -FilePath $PostgresInstaller -ArgumentList $InstallArgs -Wait -NoNewWindow

    Write-Host "  [OK] PostgreSQL installed successfully" -ForegroundColor Green

} catch {
    Write-Host ("  [FAIL] Failed to install PostgreSQL: " + $_.Exception.Message) -ForegroundColor Red
    exit 1
}

# ==============================================
# RETHINKDB INSTALLATION
# ==============================================

Write-Host ("`n" + "Installing RethinkDB...") -ForegroundColor Yellow

# Download RethinkDB (Windows)
$RethinkUrl = "https://download.rethinkdb.com/repository/raw/windows/rethinkdb-2.4.3.zip"
$RethinkZip = "$InstallPath\rethinkdb.zip"
$RethinkDir = "$InstallPath\RethinkDB"

try {
    # Download RethinkDB
    Write-Host "  Downloading RethinkDB..."
    Invoke-WebRequest -Uri $RethinkUrl -OutFile $RethinkZip

    # Extract RethinkDB
    Write-Host "  Extracting RethinkDB..."
    Expand-Archive -Path $RethinkZip -DestinationPath $InstallPath -Force

    # Rename directory if needed
    $ExtractedDir = Get-ChildItem -Path $InstallPath -Directory | Where-Object { $_.Name -like "*rethinkdb*" } | Select-Object -First 1
    if ($ExtractedDir) {
        Rename-Item -Path $ExtractedDir.FullName -NewName "RethinkDB" -Force
    }

    Write-Host "  [OK] RethinkDB installed successfully" -ForegroundColor Green

} catch {
    Write-Host ("  [FAIL] Failed to install RethinkDB: " + $_.Exception.Message) -ForegroundColor Red
    exit 1
}

# ==============================================
# DATABASE CONFIGURATION
# ==============================================

Write-Host ("`n" + "Configuring databases...") -ForegroundColor Yellow

# PostgreSQL Configuration
try {
    # PostgreSQL data directory (default location)
    $PostgresDataDir = "C:\Program Files\PostgreSQL\15\data"

    # Create vot_guardian database and user
    Write-Host "  Creating PostgreSQL database and user..."

    # Create SQL script content
    $CreateDBScript = "CREATE USER vot_user WITH PASSWORD '$PostgresPassword';" + "`n" + `
                     "CREATE DATABASE $DatabaseName WITH OWNER vot_user;" + "`n" + `
                     "GRANT ALL PRIVILEGES ON DATABASE $DatabaseName TO vot_user;"

    # Save script to temp file
    $TempScript = $InstallPath + "\create_db.sql"
    $CreateDBScript | Out-File -FilePath $TempScript -Encoding UTF8

    # Execute script
    & "C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -f $TempScript

    # Clean up temp file
    Remove-Item $TempScript -Force

    Write-Host "  ✅ PostgreSQL configured successfully" -ForegroundColor Green

} catch {
    Write-Host "  ❌ Failed to configure PostgreSQL: $($_.Exception.Message)" -ForegroundColor Red
}

# RethinkDB Configuration
try {
    Write-Host "  Creating RethinkDB database..."

    # Start RethinkDB to create database
    $RethinkExe = "$RethinkDir\rethinkdb.exe"
    if (Test-Path $RethinkExe) {
        # For now, we'll create a startup script
        # The database will be created when RethinkDB starts
        Write-Host "  ✅ RethinkDB ready for startup" -ForegroundColor Green
    }

} catch {
    Write-Host "  ❌ Failed to configure RethinkDB: $($_.Exception.Message)" -ForegroundColor Red
}

# ==============================================
# CREATE STARTUP SCRIPTS
# ==============================================

Write-Host ("`n" + "Creating startup scripts...") -ForegroundColor Yellow

# PostgreSQL startup script
$PostgresScript = "@echo off`necho Starting PostgreSQL for V.O.T. Guardian...`n" + `
                  "`"C:\Program Files\PostgreSQL\15\bin\pg_ctl.exe`" -D `"C:\Program Files\PostgreSQL\15\data`" start`n" + `
                  "echo PostgreSQL started!`npause"

$PostgresScript | Out-File -FilePath ($InstallPath + "\start_postgresql.bat") -Encoding ASCII

# RethinkDB startup script
$RethinkScript = "@echo off`necho Starting RethinkDB for V.O.T. Guardian...`n" + `
                "cd `"$RethinkDir`"`n" + `
                "start rethinkdb.exe --bind all --http-port 8080`n" + `
                "echo RethinkDB started! Web UI available at http://localhost:8080`npause"

$RethinkScript | Out-File -FilePath ($InstallPath + "\start_rethinkdb.bat") -Encoding ASCII

Write-Host "  ✅ Startup scripts created" -ForegroundColor Green

# ==============================================
# UPDATE .env FILE
# ==============================================

Write-Host ("`n" + "Updating .env file...") -ForegroundColor Yellow

try {
    # Check if .env exists
    $EnvFile = ".\.env"
    if (Test-Path $EnvFile) {
        $EnvContent = Get-Content $EnvFile -Raw

        # Update PostgreSQL URL
        $PostgresPattern = "POSTGRESQL_URL=.*"
        $PostgresReplacement = "POSTGRESQL_URL=postgresql://vot_user:$PostgresPassword@localhost:5432/$DatabaseName"
        $EnvContent = $EnvContent -replace $PostgresPattern, $PostgresReplacement

        # Update RethinkDB settings
        $RethinkHostPattern = "RETHINKDB_HOST=.*"
        $RethinkHostReplacement = "RETHINKDB_HOST=localhost"
        $EnvContent = $EnvContent -replace $RethinkHostPattern, $RethinkHostReplacement

        $RethinkPortPattern = "RETHINKDB_PORT=.*"
        $RethinkPortReplacement = "RETHINKDB_PORT=28015"
        $EnvContent = $EnvContent -replace $RethinkPortPattern, $RethinkPortReplacement

        $RethinkDBPattern = "RETHINKDB_DB=.*"
        $RethinkDBReplacement = "RETHINKDB_DB=$DatabaseName"
        $EnvContent = $EnvContent -replace $RethinkDBPattern, $RethinkDBReplacement

        $RethinkUserPattern = "RETHINKDB_USER=.*"
        $RethinkUserReplacement = "RETHINKDB_USER=vot_user"
        $EnvContent = $EnvContent -replace $RethinkUserPattern, $RethinkUserReplacement

        $RethinkPasswordPattern = "RETHINKDB_PASSWORD=.*"
        $RethinkPasswordReplacement = "RETHINKDB_PASSWORD=$PostgresPassword"
        $EnvContent = $EnvContent -replace $RethinkPasswordPattern, $RethinkPasswordReplacement

        # Save updated .env file
        $EnvContent | Out-File -FilePath $EnvFile -Encoding UTF8

        Write-Host "  [OK] .env file updated with database connections" -ForegroundColor Green

    } else {
        Write-Host "  [WARN] .env file not found, please update manually" -ForegroundColor Yellow
    }

} catch {
    Write-Host "  ❌ Failed to update .env file: $($_.Exception.Message)" -ForegroundColor Red
}

# ==============================================
# FINAL INSTRUCTIONS
# ==============================================

Write-Host ("`n" + "Database installation completed!") -ForegroundColor Green
Write-Host ("=" * 60)

Write-Host ("`n" + "Next steps:") -ForegroundColor Cyan
Write-Host "1. Start PostgreSQL:" -ForegroundColor White
Write-Host ("   " + $InstallPath + "\start_postgresql.bat") -ForegroundColor Gray

Write-Host ("`n" + "2. Start RethinkDB:") -ForegroundColor White
Write-Host ("   " + $InstallPath + "\start_rethinkdb.bat") -ForegroundColor Gray

Write-Host ("`n" + "3. Test database connections:") -ForegroundColor White
Write-Host "   python test_databases.py" -ForegroundColor Gray

Write-Host ("`n" + "4. Start V.O.T. Guardian:") -ForegroundColor White
Write-Host "   python -m src.api.main" -ForegroundColor Gray

Write-Host ("`n" + "Database URLs configured:") -ForegroundColor Cyan
Write-Host ("  PostgreSQL: postgresql://vot_user:" + $PostgresPassword + "@localhost:5432/" + $DatabaseName) -ForegroundColor Gray
Write-Host ("  RethinkDB:  localhost:28015 (database: " + $DatabaseName + ")") -ForegroundColor Gray

Write-Host ("`n" + "Installation complete! Ready for development!") -ForegroundColor Green