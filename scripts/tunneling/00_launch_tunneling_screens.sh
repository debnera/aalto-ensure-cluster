screen -d -m -S ssh_tunnel ./reverse_proxy.sh
screen -d -m -S grafana_tunnel ./grafana_tunnel.sh
screen -d -m -S prometheus_tunnel ./prometheus_tunnel.sh
screen -d -m -S prometheus2_tunnel ./prometheus2_tunnel.sh
screen -ls
