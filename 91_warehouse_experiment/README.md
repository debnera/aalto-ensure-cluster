# Collaborative warehouse AGVs

This is an example application where lidar-data is being generated 
from multiple autonomous guided vehicles (AGVs) that represent robots in a warehouse.

The lidar data is processed on a cluster to collaboratively create a real-time view to the state of the
warehouse in the form of a occupancy grid.

The application is split to multiple workers and one master. The worker nodes receive point clouds
that are used to compute a local occupancy grid. The occupancy grid is essentially a map of the warehouse,
showing which squares are currently occupied by some obstacle and which are empty. The local occupancy grid
is then send to the master, which constructs a global occupancy grid from the data of all workers.

This application represents a workload, where the individual applications running on the cluster must
communicate with each other to create a combined view of the world.

Data can be fed to the cluster over Kafka either from real vehicles, simulated vehicles or 
a previously collected dataset.

# How to debug locally
- Optional: Launch kubernetes on Docker-Desktop (most of the scripts work without kubernetes)
- Launch `local_kube_kafka/` with `docker compose up` (This runs outside kubernetes, but works with the local kubernetes setup)
- Launch the application
- Feed data to the cluster over Kafka

# Update yolo consumer (in docker hub)
- `cd docker`
- `docker build -t debnera/warehouse_master:0.1 -f master.Dockerfile .`
- `docker push debnera/warehouse_master:0.1`

- `docker build -t debnera/warehouse_worker:0.1 -f worker.Dockerfile .`
- `docker push debnera/warehouse_worker:0.1`