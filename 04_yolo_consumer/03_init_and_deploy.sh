# MAKE SURE THAT THE USER GAVE AT LEAST ONE ARGUMENT TO THE SCRIPT
if [[ -z $1 ]]
then
  echo "ERROR: DEFINE THE NUMBER OF TOPIC PARTITIONS";
  echo "Example: ./03_init_and_deploy.sh 5"
  exit 1;
fi

# INITIALIZE KAFKA TOPICS & WAIT FOR ABIT
python3 app/kafka_init.py -n $1
sleep 5

read -p "KAFKA TOPICS READY, PRESS ENTER TO DELOY PODS..."

# THEN DEPLOY FRESH PODS
kubectl apply -f yolo_deployment.yaml