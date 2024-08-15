cd app  # Change directory, as datasets are expected to be relative to current working directory
# Run three minutes long experiment with 5 mbps (15.5 mbps is roughly the limit of the cluster)
# NOTE: Kubernetes auto scaling might be too slow to react to such short test.
echo "Starting a 3 minute long test that should somewhat stress all workers"
python3 feeder.py --max_mbps 2 --duration 3600 --breakpoints 200 --n_cycles 6

