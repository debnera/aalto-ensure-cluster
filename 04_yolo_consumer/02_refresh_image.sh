# LOGIN TO DOCKER HUB IF NECESSARY
# docker login

# SET YOUR GIT USERNAME
MY_GIT_USERNAME="wickstjo"

# BUILD THE DOCKER IMAGE
docker build --no-cache -t workload_consumer -f consumer.Dockerfile .

# TAG & UPLOAD THE IMAGE TO DOCKER HUB REGISTRY
docker tag workload_consumer:latest $MY_GIT_USERNAME/workload_consumer:latest
docker push $MY_GIT_USERNAME/workload_consumer:latest