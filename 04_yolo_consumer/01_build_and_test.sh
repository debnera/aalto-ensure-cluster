# BUILD THE DOCKER IMAGE
docker build --no-cache -t workload_consumer_vino -f gpt.Dockerfile .

# MAKE SURE THAT THE IMAGE WORKS
docker run workload_consumer_vino
