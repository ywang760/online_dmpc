import os
import numpy as np
import json

import argparse


parser = argparse.ArgumentParser(description="Process trajectory.txt and fill in stats.json")

parser.add_argument(
    "-o",
    "--output_dir_name",
    type=str,
    required=True,
    help="Output directory name",
)
parser.add_argument(
    "-c",
    "--config_path",
    type=str,
    required=True,
    help="Path to the config file",
)

args = parser.parse_args()

output_dir_name = args.output_dir_name
config_path = args.config_path

# output_dir_name = "Circle50/exp_1"
# config_path = "../config/config_Circle50.json"


def get_file(output_dir_name, prefix):
    files = [
        file for file in os.listdir(output_dir_name) if file.startswith(prefix)
    ]
    assert len(files) == 1, f"Found {len(files)} files starting with {prefix}"
    
    return os.path.join(output_dir_name, files[0])

full_trajectory_path = get_file(output_dir_name, "trajectories")
full_stats_path = get_file(output_dir_name, "stats")

# process the log file to get collision data
# find the path in output_dir_name that ends in *.log
log_path = [file for file in os.listdir(output_dir_name) if file.endswith(".log")][0]
log_path = os.path.join(output_dir_name, log_path)


with open(config_path, "r") as f:
    config = json.load(f)
with open(full_stats_path, "r") as f:
    stats = json.load(f)

N = config["N"]
N_cmd = config["Ncmd"]
pmin = config["pmin"]
pmax = config["pmax"]
po = np.array(config["po"])
pf = np.array(config["pf"])
po = po.reshape((N, 3))
pf = pf.reshape((N_cmd, 3))

all_pos = np.loadtxt(full_trajectory_path)
pk = []
for i in range(N_cmd):
    pk.append(all_pos[3 * i : 3 * (i + 1), :])
pk = np.array(pk).transpose(2, 0, 1)


ts = config["ts"]

simulation_time = int(pk.shape[0] * ts)
# print(f"Simulation time: {simulation_time} seconds")


robot_arrival_time = [-1] * N_cmd

for k, position_data in enumerate(pk):
    for i, robot_position in enumerate(position_data):
        robot_final = pf[i]
        if np.linalg.norm(robot_position - robot_final) < 0.1: # goal tolerance is 0.1, same as in the cpp code -> can be changed
            if robot_arrival_time[i] == -1:
                robot_arrival_time[i] = k * ts


assert robot_arrival_time.count(-1) + stats["goal_reach_count"] == N_cmd, "Goal reach count mismatch, check the stats file"
print(f"{stats['goal_reach_count']} robots reached their goal")
    
stats["simulation_time"] = simulation_time
stats["robot_arrival_time"] = robot_arrival_time
stats["robot_count"] = N_cmd
stats["makespan"] = max(robot_arrival_time)

# read the log file, process collision stats to get success rate
with open(log_path, "r") as f:
    lines = f.readlines()
    collision_lines = [line for line in lines if line.startswith("Collision")]
import re
collision_pattern = re.compile(r"Vehicles (\d+) and (\d+) .* @ t = ([\d.]+)s")

r1s = []
r2s = []
collision_t = []
for line in collision_lines:
    match = collision_pattern.search(line)
    if match:
        r1s.append(int(match.group(1)))
        r2s.append(int(match.group(2)))
        collision_t.append(float(match.group(3)))

assert len(r1s) == len(r2s) == len(collision_t)

all_collided = set(r1s + r2s)
success_rate = len(set(range(N_cmd)) - all_collided) / N_cmd
stats["success_rate"] = success_rate

data = stats["simulation_data"]
all_solve_times = []
for j_data in data:
    solve_times = j_data["robot_data"]["solve_times"]
    all_solve_times.append(solve_times)
all_solve_times = np.array(all_solve_times)
qp_solve_time = {
    "mean": np.mean(all_solve_times),
    "std": np.std(all_solve_times),
    "max": np.max(all_solve_times),
    "min": np.min(all_solve_times),
}
stats["qp_solve_time"] = qp_solve_time

with open(full_stats_path, "w") as f:
    json.dump(stats, f, indent=4)