import argparse
import numpy as np
from collections import defaultdict
import json
import os

# post process stats for num_robot_exp, for comparison plot with BVC and hierarchical

num_robots = list(range(10, 100, 10))
stats_dir_name = "stats"

aggregated_data = defaultdict(list)

stats_list = []
# read from stats_dir_name
for name in num_robots:

    stats_path = os.path.join(stats_dir_name, f"stats_Circle{name}.json")
    with open(stats_path, "r") as f:
        stats = json.load(f)
    stats_list.append(stats)

for stats in stats_list:
    for key, value in stats.items():
        aggregated_data[key].append(value)

with open("stats/dmpc_scalability_stats.json", "w") as f:
    json.dump(dict(aggregated_data), f, indent=4)