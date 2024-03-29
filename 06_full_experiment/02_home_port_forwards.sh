# EXAMPLE VARIABLE
CLOUD_PROXY="ansure@ansurevm.northeurope.cloudapp.azure.com"

# MIRROR CLOUD_PROXY:PORT TO LOCALHOST:PORT
screen -dmS grafana_proxy ssh -L 3000:localhost:3000 $CLOUD_PROXY
screen -dmS prometheus_proxy ssh -L 9090:localhost:9090 $CLOUD_PROXY