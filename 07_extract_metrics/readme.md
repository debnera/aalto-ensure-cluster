## Overview

- `Prometheus` is designed to only store data for a few days before log rotating.
- After an experiment, we want to extract all data from both `Prometheus` instances for later analysis.
    - Even relatively short few hour experiments can produce multiple gigabytes of different metrics data.
    - Most of it is useless, but none of it should be discarded before analysis.
- This turned out to be much more difficult/messy than expected.
    - Snapshotting binary blobs from `Prometheus` makes is annoying to explore data.
    - Third-party scripts did not work paricularly well.
    - The experiment machines had low-end hardware, making it very easy to run out of memory and crash.
        - In the future, I suggest performing this extraction process on an entirely separate machine.
- We ended up writing our own extraction script.
    - The first version had its own data schema and ended up being way too convoluted.
    - The second and final version extracts and dumps the raw `Prometheus` response data into JSON files.

<!-- ########################################################################################################## -->
## Table of Contents

1. [Subdir Purpose](#)
2. [Input Parameters](#)
3. [Points of Interest](#)
    1. [Controlling Memory Usage](#)
    2. [Filter Metrics](#)

<!-- ########################################################################################################## -->
## 1. Input Parameters

- `--start` `(str)`: Starting timestamp of the experiment.
- `--end` `(str)`: Ending timestamp of the experiment.
    - Copy/paste these timestamps from the `Grafana` UI.
- `--sampling` `(int)`: The sampling rate to aggregate the data over.
    - Group and average the next `n` sequential values, and use this value instead.
    - Reduces the amount of scraped and stored data by a factor of `n`.
    - The "correct" value depend on your `Prometheus` and `Kepler` scraping intervals.
- `--n_threads` `(int)`: How many concurrent threads to scrape with.
    - A high value will cause the machine to run out of memory.
    - A low value will cause a very long runtime.
- `--segment_size` `(int)`: How many data points each individual Prometheus query segment will contain.
    - Prometheus limit is `~11 000`, but this will cause memory issues.
    - I generally kept this at `~2000` to be safe.
    - The "correct" value depends on how many threads you are using.

```bash
# FOR EXAMPLE
python3 extractor.py
    --start "2024-01-30 19:10:15"
    --end "2024-01-31 03:10:15"
    --sampling 5
    --n_threads 8
    --segment_size 2000
```

<!-- ########################################################################################################## -->
## 2. Points of Interest

<!-- ########################################################################################################## -->
### 2.1. Controlling Memory Usage
---

- Prometheus is limited to how many data points it can return in one query.
    - This limit is easy to exceed with small sample rates.
    - Naturally, large queries require much memory, which is problematic on the `NUC` machines.
- To address this, the script splits large queries into many smaller segments.
    - For example, a `1000` second experiment is split into `10*100` second segments.
- Each segment is saved as its own JSON file, and must be re-assembled retroactively for analysis.
    - The segments are labeled with a chronological timestamp.

<!-- ########################################################################################################## -->
### 2.2. Filter Metrics
---

- Most of the scraped metrics are completely irrelevant, but discarding data is:
    - Dangerous as you might lose critical information you may have not currently realize is important.
    - Greatly reduces the size of datasets, making it easier to find valuable patterns.
- If you eventually want to ignore certain metrics, you can either blacklist or whitelist their prefix.
    - Wrap the entire expression in a lambda function.
        - Use logical operators to exclude certain metrics.
        - Use the `not` to only include certain metrics.
    - For example:
        - [`extractor.py #row-44`](`extractor.py#r44`)
        - [`extractor.py #row-50`](`extractor.py#r50`)

```python
# EXCLUDE PROMETHEUS_, GRAFANA_ AND ALERTMANAGER_ PREFIXES
s1_filter = lambda metric: metric.startswith('prometheus_') or metric.startswith('grafana_') or metric.startswith('alertmanager_')
```

```python
# EXCLUDE EVERYTHING EXCEPT THE KAFKA PREFIX
s2_filter = lambda metric: not metric.startswith('kafka_')
```