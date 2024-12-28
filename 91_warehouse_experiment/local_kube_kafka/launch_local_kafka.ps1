# This script launches the local Kafka setup, which requires knowing
# the IP address of this local computer. Simply using 'localhost' does not work.
# Therefore, the script fetches the IP and launches Kafka with it.

# Function to get the current local IP address
function Get-LocalIPAddress {
   # Retrieve the local IP address by filtering non-loopback IPv4 addresses
   $ipconfig = Get-NetIPAddress | Where-Object { $_.AddressFamily -eq 'IPv4' -and $_.IPAddress -notlike '127.*' }
   if ($ipconfig) {
      return $ipconfig.IPAddress
   } else {
      return $null
   }
}

# Retrieve the IP address
$LOCAL_IP = Get-LocalIPAddress

# Check if IP address retrieval was successful
if (-not $LOCAL_IP) {
   Write-Host "Error: Could not retrieve IP address." -ForegroundColor Red
   exit 1
} else {
   Write-Host "Local IP address is set to $LOCAL_IP" -ForegroundColor Green
}

# Set the IP address as an environment variable
$env:LOCAL_IP = $LOCAL_IP

# Stop and remove existing Kafka-related Docker containers, volumes, and networks
Write-Host "Stopping and removing existing Kafka-related Docker components..." -ForegroundColor Yellow
docker compose down -v --remove-orphans
Write-Host "Removed existing Kafka-related Docker components." -ForegroundColor Green

# Prune unused networks and volumes
Write-Host "Pruning unused networks and volumes..." -ForegroundColor Yellow
docker network prune -f
docker volume prune -f
Write-Host "Pruned unused networks and volumes." -ForegroundColor Green

# Run docker-compose with the updated environment variable
Write-Host "Starting Kafka with updated environment variable..." -ForegroundColor Yellow
docker compose up