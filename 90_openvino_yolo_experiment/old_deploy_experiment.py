import time
import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Load Kubernetes configuration
config.load_kube_config()

# Define the deployment YAML template
deployment_yaml = """
apiVersion: v1
kind: Namespace
metadata:
  labels:
    pod-security.kubernetes.io/warn: privileged
    pod-security.kubernetes.io/warn-version: latest
  name: workloadb
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yolo-consumer
  namespace: workloadb
spec:
  replicas: 1
  selector:
    matchLabels:
      run: yolo-consumer
  template:
    metadata:
      labels:
        run: yolo-consumer
    spec:
      containers:
        - name: yolo-consumer
          image: debnera/workload_consumer_vino:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 80
          env:
            - name: YOLO_MODEL
              value: "{yolo_model}"
            - name: KAFKA_INPUT_TOPIC
              value: "yolo_input"
            - name: KAFKA_OUTPUT_TOPIC
              value: "yolo_output"
            - name: KAFKA_SERVERS
              value: "10.96.0.1:10001"
          resources:
            limits:
              cpu: 1000m
            requests:
              cpu: 1000m
---
apiVersion: v1
kind: Service
metadata:
  name: yolo-consumer
  namespace: workloadb
  labels:
    run: yolo-consumer
spec:
  ports:
    - port: 80
  selector:
    run: yolo-consumer
"""

# Define the different YOLO_MODEL values to test
yolo_models = ["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"]


# Function to deploy the application
def deploy_application(yolo_model):
    k8s_client = client.ApiClient()
    k8s_apps_v1 = client.AppsV1Api(k8s_client)
    k8s_core_v1 = client.CoreV1Api(k8s_client)

    # Prepare the YAML with the current YOLO_MODEL
    deployment = deployment_yaml.format(yolo_model=yolo_model)
    deployment_objects = list(yaml.safe_load_all(deployment))

    # Create Namespace
    namespace = deployment_objects[0]
    try:
        k8s_core_v1.create_namespace(namespace)
    except ApiException as e:
        if e.status != 409:  # Ignore error if namespace already exists
            raise

    # Create Deployment
    deployment = deployment_objects[1]
    k8s_apps_v1.create_namespaced_deployment(
        body=deployment, namespace="workloadb"
    )

    # Create Service
    service = deployment_objects[2]
    k8s_core_v1.create_namespaced_service(
        body=service, namespace="workloadb"
    )


# Function to delete the deployment and service
def clean_up():
    k8s_client = client.ApiClient()
    k8s_apps_v1 = client.AppsV1Api(k8s_client)
    k8s_core_v1 = client.CoreV1Api(k8s_client)

    k8s_apps_v1.delete_namespaced_deployment(
        name="yolo-consumer", namespace="workloadb"
    )
    k8s_core_v1.delete_namespaced_service(
        name="yolo-consumer", namespace="workloadb"
    )
    k8s_core_v1.delete_namespace(name="workloadb")
