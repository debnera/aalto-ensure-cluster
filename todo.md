## OpenVino experiments

Motivation: PyTorch-based experiments give unusable QoS metrics, leading to low-quality results and analysis.

On the other hand, OpenVino seems to give much more stable QoS metrics.

TODO: 

[] Get local Kafka + image setup working
[] Get multiple OV YOLO models working
[] Run linear experiments to figure out limits of each model
[] Run day-night-cycle to figure out how each model acts with dynamic workloads
[] Analyze results and figure out where to go next


Future work options:
- Adjust node configurations (e.g., power limits, ...)
- More in-depth measurements of previous experiments
- Load-balancing (fixed ratios with different model sizes -> propose ML-based load-balancer)