# Exposing the cluster to an external cloud service

These are helper scripts that expose SSH, Grafana and Prometheus ports to an external cloud server. 

By using these, you do not need to be physically present at the cluster and can work remotely.

This also means that the cluster is exposed to anyone who has access to the external cloud server.

# Before you start

These scripts expect that you have an environment variable $CLOUD set to point to your external server.

It is recommended to add these to your .bashrc-file, so they are automatically set on login.

For example:

# Anton's cloud
export CLOUD=ec2-user@ec2-13-60-99-128.eu-north-1.compute.amazonaws.com
# or Jaakko's cloud
export CLOUD=ansure@ansurevm.northeurope.cloudapp.azure.com

## SSH

This opens up a reverse proxy, enabling anyone to SSH to the cluster from the external cloud service

ssh -R 7011:localhost:22 $CLOUD

You can then connect to this cluster from the remote server by using:

ssh user@localhost:7011

## Grafana

This only exposes the port that Grafana uses to the remote cloud server. Grafana still needs to be launched separately.

./grafana_tunnel.sh

## Prometheus

This only exposes the port that Prometheus uses to the remote cloud server. Prometheus still needs to be launched separately.

./prometheus_tunnel.sh

## Using screen

You probably want to launch these as separate screens, so they keep running in the background.


screen -d -m -S cloud_ssh ./reverse_proxy.sh
screen -d -m -S cloud_grafana ./grafana_tunnel.sh
screen -d -m -S cloud_prometheus ./prometheus_tunnel.sh

