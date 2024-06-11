# TUNNELS TO CLOUD MACHINE
screen -dmS grafana_tunnel /home/anton/scripts/grafana_tunnel.sh
screen -dmS prometheus_tunnel /home/wickstjo/scripts/prometheus_tunnel.sh
#screen -dmS notebook_pf ssh -R 8888:130.233.193.117:8888 ansure@ansurevm.northeurope.cloudapp.azure.com

# KUBERNETES SERVICE PORT FORWARDS
screen -dmS grafana_pf kubectl -n monitoring port-forward svc/grafana 3000 --address=130.233.193.117
screen -dmS prometheus_pf kubectl -n monitoring port-forward svc/prometheus-k8s 9090 --address=130.233.193.117

screen -ls
