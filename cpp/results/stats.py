import argparse
import json
import os
import numpy as np

parser = argparse.ArgumentParser(description="Process stats across multiple runs")

parser.add_argument(
    "-i",
    "--stats_dir_name",
    type=str,
    required=True,
    help="Directory to the stats files",
)

args = parser.parse_args()

stats_dir_name = args.stats_dir_name
instance_name = os.path.basename(stats_dir_name)
print(f"Processing stats for instance {instance_name}")

num_exps = len(os.listdir(stats_dir_name))

goal_reach_rates = []
collision_counts = []
success_rates = []
qp_solve_time_avgs = []
qp_solve_time_stds = []
makespans = []
robot_arrival_time_avgs = []
robot_arrival_time_stds = []

for root, dirs, files in os.walk(stats_dir_name):
    for subdir in dirs:
        subdir_path = os.path.join(stats_dir_name, subdir)
        stats_file = [file for file in os.listdir(subdir_path) if file.startswith(f"stats")][0]
        stats_path = os.path.join(subdir_path, stats_file)
        with open(stats_path, "r") as f:
            stats = json.load(f)
        goal_reach_rates.append(stats["goal_reach_count"] / stats["robot_count"])
        collision_counts.append(stats["collision_count"])
        success_rates.append(stats["success_rate"])
        qp_solve_time_avgs.append(stats["qp_solve_time"]["mean"])
        qp_solve_time_stds.append(stats["qp_solve_time"]["std"])
        makespans.append(stats["makespan"])
        
        robot_arrival_times = stats["robot_arrival_time"]
        robot_arrival_time_mean = np.mean(robot_arrival_times)
        robot_arrival_time_std = np.std(robot_arrival_times)
        robot_arrival_time_avgs.append(robot_arrival_time_mean)
        robot_arrival_time_stds.append(robot_arrival_time_std)
        

goal_reach_rate = np.mean(goal_reach_rates)
collision_count = np.mean(collision_counts)
success_rate = np.mean(success_rates)
qp_solve_time_avg = np.mean(qp_solve_time_avgs)
qp_solve_time_std = np.mean(qp_solve_time_stds)
makespan = np.mean(makespans)
robot_arrival_time_avg = np.mean(robot_arrival_time_avgs)
robot_arrival_time_std = np.mean(robot_arrival_time_stds)

print(f"Stats are averaged across {num_exps} experiments")
print(f"Goal reach rate: {goal_reach_rate}")
print(f"Collision count: {collision_count}")
print(f"Success rate (assuming all robots reach goal): {success_rate}")
print(f"QP solve time avg: {qp_solve_time_avg} (ms)")
print(f"QP solve time std: {qp_solve_time_std} (ms)")
print(f"Makespan (for ones reached goals): {makespan} (s)")
print(f"Robot arrival time avg: {robot_arrival_time_avg} (s)")
print(f"Robot arrival time std: {robot_arrival_time_std} (s)")

# check if the "stats" folder exists, if not, create it
if not os.path.exists("stats"):
    os.makedirs("stats")

stats = {
    "goal_reach_rate": goal_reach_rate,
    "collision_count": collision_count,
    "success_rate": success_rate,
    "qp_solve_time_avg": qp_solve_time_avg,
    "qp_solve_time_std": qp_solve_time_std,
    "makespan": makespan,
    "robot_arrival_time_avg": robot_arrival_time_avg,
    "robot_arrival_time_std": robot_arrival_time_std,
    "instance_name": instance_name,
}

stats_path = os.path.join("stats", f"stats_{instance_name}.json")

# save the stats to a file
with open(stats_path, "w") as f:
    json.dump(stats, f, indent=4)