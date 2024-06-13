cd app  # Change directory, as datasets are expected to be relative to current working directory
# Run three minutes long experiment with 15 mbps (15mbps should be visible on worker CPU utilization)
# NOTE: Kubernetes auto scaling might be too slow to react to such short test.
echo "Starting a 3 minute long test that should visibly stress all workers"
python3 feeder.py --max_mbps 15 --duration 180 --breakpoints 200 --n_cycles 6