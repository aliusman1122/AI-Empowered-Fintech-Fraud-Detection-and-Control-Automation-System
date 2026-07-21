$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackendDir = "backend"
$BackupDir = "backend_backup_$Timestamp"

Write-Host "Creating backup of backend directory to $BackupDir..."
Copy-Item -Path $BackendDir -Destination $BackupDir -Recurse

$ComposeBackup = "docker-compose_backup_$Timestamp.yml"
Write-Host "Creating backup of docker-compose.yml to $ComposeBackup..."
Copy-Item -Path "docker-compose.yml" -Destination $ComposeBackup

Write-Host "Backup completed successfully!"
