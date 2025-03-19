#!/bin/bash
# This script launches the local Kafka setup, which requires knowing
# the IP-address of this local computer. Simply using 'localhost' does not work.
# Therefore, we first fetch the IP and then launch Kafka with that.

# Function to get the current IP address
get_ip_address() {
   hostname --all-ip-addresses | awk '{print $1}'
}

# Retrieve the IP address
LOCAL_IP=$(get_ip_address)

# Check if IP address retrieval was successful
if [ -z "$LOCAL_IP" ]; then
   echo "Error: Could not retrieve IP address."
   exit 1
else
   echo "Local IP address is set to $LOCAL_IP"
fi

# Export the IP address as an environment variable
export LOCAL_IP

# Remove existing Kafka containers, volumes, and networks
echo "Stopping and removing existing Kafka-related Docker components..."

docker compose down -v --remove-orphans

echo "Removed existing Kafka-related Docker components."

# Prune unused networks and volumes
docker network prune -f
docker volume prune -f

echo "Pruned unused networks and volumes."

# Run docker compose with the updated environment variable
docker compose up