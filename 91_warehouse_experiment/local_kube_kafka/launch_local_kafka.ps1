# Function to get a single, valid local IP address
function Get-LocalIPAddress {
   # Retrieve the local IP addresses by filtering non-loopback IPv4 addresses
   # Prioritize non-link-local addresses (not in 169.254.x.x range)
   $ipconfig = Get-NetIPAddress | Where-Object {
      $_.AddressFamily -eq 'IPv4' -and
              $_.IPAddress -notlike '127.*' -and
              $_.IPAddress -notlike '169.254.*'
   }

   # If multiple IPs are still present, select the first valid one (customizable logic)
   if ($ipconfig) {
      return $ipconfig.IPAddress | Select-Object -First 1
   } else {
      return $null
   }
}

# Retrieve the IP address
$LOCAL_IP = Get-LocalIPAddress

# Check if IP address retrieval was successful
if (-not $LOCAL_IP) {
   Write-Host "Error: Could not retrieve a valid local IP address." -ForegroundColor Red
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