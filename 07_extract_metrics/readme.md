## Purpose

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

## Input Parameters

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

For example:
```bash
python3 extractor.py
    --start "2024-01-30 19:10:15"
    --end "2024-01-31 03:10:15"
    --sampling 5
    --n_threads 8
```