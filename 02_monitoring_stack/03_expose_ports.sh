# KUBERNETES SERVICE PORT FORWARDS (make them available on the master node)
screen -dmS grafana_pf kubectl -n monitoring port-forward svc/grafana 3000
screen -dmS prometheus_pf kubectl -n monitoring port-forward svc/prometheus-k8s 9090
echo "Launched screens grafana_pf (port 3000) and prometheus_pf (port 9090)"
