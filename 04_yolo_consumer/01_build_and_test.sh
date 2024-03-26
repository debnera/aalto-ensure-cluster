# BUILD THE DOCKER IMAGE
docker build --no-cache -t workload_consumer -f consumer.Dockerfile .

# MAKE SURE THAT THE IMAGE WORKS
docker run workload_consumer