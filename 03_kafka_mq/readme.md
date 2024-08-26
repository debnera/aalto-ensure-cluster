## Overview

- We will use Kafka to transport data to worker-pods running in Kubernetes.
- Tracking Kafka's performance is imperative for assessing experiments.
    - We use `JMX` scraping to collect Kafka metrics from `Docker` containers.
    - We store said data in `Prometheus`, and visualize it with `Grafana`.
- Ideally, `Kafka` would be running within `Kubernetes`.
    - However, integration with the remaining tech stack was problematic.
    - Instead, we run `Kafka`, `Zookeeper` and a separate `Prometheus` instance externally.
    - Once an experiment has been performed, the data from both `Prometheus` instances (one for Kubernetes, one for Kafka) are aggregated and analyzed together.

- NOTE: Having only one Kafka consumer, as opposed to three, has seemed to work just as well and thus the current scripts in this branch and repo only use one. 

<!-- ########################################################################################################## -->
## Table of Contents

1. [Kafka's Docker Compose](#)
2. [Customization](#)
    1. [Shared Broker Vars](#)
    2. [Unique Broker Vars](#)
    3. [Prometheus Vars](#)

<!-- ########################################################################################################## -->
## KAFKA'S DOCKER COMPOSE

- The docker-compose file: `docker-compose.yaml`:
    - Contains 3 instances of `Kafka brokers`.
    - Contains 1 instance of `Zookeeper` (manages the `Kafka` brokers).
    - Contains 1 instance of `Prometheus` (aggregates metrics data).
- Other config files:
    - Kafka JMX module: `configs/jmx_prometheus_javaagent-0.17.2.jar`.
    - Kafka JMX config: `configs/kafka_scraper.yml`.
    - Prometheus scrape config: `configs/prometheus_config.yml`.
- Launch script: [`./run.sh`](run.sh)

```bash
# WHEN DOING MULTIPLE EXPERIMENTS, YOUR DISC FILLS UP QUICKLY WITH DEAD ARTIFACTS
# CLEAN UP OLD HANGING GABARGE, THEN CREATE FRESH ENVIRONMENT
docker volume prune -f
read -p "Press enter to continue..."

# CREATE NEW CONTAINERS
docker compose up --force-recreate --renew-anon-volumes --remove-orphans
```

<!-- ########################################################################################################## -->
## SHARED BROKER VARS

- The Kafka brokers share most variable values.

```yaml
# SHARED KAFKA PROPS
x-kafka_shared: &kafka_shared
  image: confluentinc/cp-kafka:7.3.0
  depends_on:
    - kafka_zookeeper
  volumes:
    - ./configs/kafka_scraper.yml:/usr/app/kafka_scraper.yml
    - ./configs/jmx_prometheus_javaagent-0.17.2.jar:/usr/app/jmx_prometheus_javaagent.jar
```

```yaml
# SHARED KAFKA ENV
x-kafka_env: &kafka_env
  KAFKA_AUTO_CREATE_TOPICS_ENABLE: True
  KAFKA_NUM_PARTITIONS: 10
  KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
  KAFKA_ZOOKEEPER_CONNECT: kafka_zookeeper:2181
  KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
  KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
  KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
  KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
  KAFKA_JMX_OPTS: "-javaagent:/usr/app/jmx_prometheus_javaagent.jar=11001:/usr/app/kafka_scraper.yml"
```

<!-- ########################################################################################################## -->
## UNIQUE BROKER VARS

- However, the following variable values must be unique for each broker:
    - The host port.
    - The broker ID.
    - The advertisement addresses.
        - Note that there are two addresses per broker, for internal and external communication.
        - The external IP (`130.233.193.117`) should point at the machine hosting the services of this file.

```yaml
# FIRST BROKER
kafka_broker_1:
    <<: *kafka_shared
    ports:
        - 10001:10001
    environment:
        <<: *kafka_env
        KAFKA_BROKER_ID: 1
        KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka_broker_1:11000,PLAINTEXT_HOST://130.233.193.117:10001
```

```yaml
# SECOND BROKER
kafka_broker_2:
    <<: *kafka_shared
    ports:
        - 10002:10002
    environment:
        <<: *kafka_env
        KAFKA_BROKER_ID: 2
        KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka_broker_2:11000,PLAINTEXT_HOST://130.233.193.117:10002
```

<!-- ########################################################################################################## -->
## PROMETHEUS VARS

- You can permanently store the prometheus' data on-disk.
- Make sure you `CHMOD 777` the correct directory on your filesystem first.
- Notice that this instance of `Prometheus` runs on port `9091`.
    - On `Kubernetes`, it runs on port `9090`.

```yaml
prometheus:
    image: prom/prometheus:v2.43.0
    volumes:
        - ./configs/prometheus_config.yml:/etc/prometheus/config.yml
        - ./db_prometheus:/prometheus:rw
    ports:
        - '9091:9090'
    command:
        - '--config.file=/etc/prometheus/config.yml'
```


<!-- - Scraping config: `configs/kafka_scraper.yml`.
- JMX module: `configs/jmx_prometheus_javaagent-0.17.2.jar`. -->

<!-- 
- Deploy cached (modified) files: `./01_cached_monitoring.sh`

```yaml
volumes:
    - ./configs/kafka_scraper.yml:/usr/app/kafka_scraper.yml
    - ./configs/jmx_prometheus_javaagent-0.17.2.jar:/usr/app/jmx_prometheus_javaagent.jar
```

- Generate fresh deployment files: `./01_fresh_monitoring.sh`

```bash
# CLONE THE PROMETHEUS & GRAFANA DEPLOYMENT FILES FROM REPO
git clone --depth 1 https://github.com/prometheus-operator/kube-prometheus
```

```bash
kubectl apply --server-side -f kube-prometheus/manifests/setup
kubectl wait --for condition=Established --all CustomResourceDefinition --namespace=monitoring
kubectl apply -f kube-prometheus/manifests/
``` -->