## Helpers for launching the cluster

These are helper scripts for quickly launching the cluster. The scripts are an alternative to running the commands on 
each worker manually.

The scripts assume that the master node is already running.

00_create_new_kube_token.sh creates a new join token on the master node, that can be used to connect worker nodes.
The join token is printed to the kube.token-file.

01_reset_and_connect_workers.sh copies the kube.token-file to each worker and runs reset_and_reconnect.sh on them.

This script will ask for worker password multiple times in plain text (not the master node password!).


```bash
# Manual alternative:
# 1. Launch master node (see instructions in the repository)
# 2. Create a new join token and get the join command:
kubeadm token create --print-join-command
# 3. Manually copy the "--token .. --discovery-token-..." to kube.token
# 4. Copy the token-file to all workers
# 5. Connect to all workers one-by-one and run the "reset_worker.sh" script
ssh wickstjo@worker1
./reset_worker.sh
exit
# Repeat above for all workers
```



