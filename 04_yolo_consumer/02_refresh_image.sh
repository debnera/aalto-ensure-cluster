# LOGIN TO DOCKER HUB IF NECESSARY
# docker login

# SET YOUR GIT USERNAME
MY_GIT_USERNAME="roopekettunen"

# BUILD THE DOCKER IMAGE
docker build -t workload_consumer_vino -f gpt.Dockerfile .

# TAG & UPLOAD THE IMAGE TO DOCKER HUB REGISTRY
docker tag workload_consumer_vino:latest $MY_GIT_USERNAME/workload_consumer_vino:latest
docker push $MY_GIT_USERNAME/workload_consumer_vino:latest
