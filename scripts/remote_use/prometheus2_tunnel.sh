# Tunnel for the secondary prometheus, used by our non-kubernetes Kafka setup
ssh -R 9091:130.233.193.117:9091 $CLOUD
