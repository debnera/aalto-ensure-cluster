# Debug locally

- Optional: Launch kubernetes on Docker-Desktop (most of the scripts work without kubernetes)
- Launch `local_kube_kafka/` with `docker compose up` (This runs outside kubernetes, but works with the local kubernetes setup)
- Launch

# Update yolo consumer (in docker hub)
`docker build -t debnera/ov_yolo:0.5 -f ov.Dockerfile .`
`docker push debnera/ov_yolo:0.5`