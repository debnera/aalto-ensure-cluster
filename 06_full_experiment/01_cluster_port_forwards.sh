# SET THE MASTER IP
MASTER_IP="130.233.193.117"
CLOUD_PROXY="ansure@ansurevm.northeurope.cloudapp.azure.com"

# KUBERNETES SERVICE PORT FORWARDS
screen -dmS grafana_pf kubectl -n monitoring port-forward svc/grafana 3000 --address=$MASTER_IP
screen -dmS prometheus_pf kubectl -n monitoring port-forward svc/prometheus-k8s 9090 --address=$MASTER_IP

# CREATE PORT FORWARDS TO CLOUD TUNNEL
screen -dmS grafana_pf ssh -R 3000:$MASTER_IP:3000 $CLOUD_PROXY
screen -dmS prometheus_pf ssh -R 9090:$MASTER_IP:9090 $CLOUD_PROXY
#screen -dmS notebook_pf ssh -R 8888:$MASTER_IP:8888 $CLOUD_VM

screen -ls