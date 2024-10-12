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

def CI_compute(sample_arr, axis=-1):
    mean = np.mean(sample_arr, axis=axis)
    std = np.std(sample_arr, axis=axis)
    ci = 1.96 * (std / np.sqrt(sample_arr.shape[axis]))
    return mean, ci

instance_name = os.path.basename(stats_dir_name)
print(f"Processing stats for instance {instance_name}")

num_exps = len(os.listdir(stats_dir_name))

goal_reach_rates = []
collision_counts = []
success_rates = []

run_times_all = []
qp_solve_times = []
makespans = []


ts = 0.1
# print a warning 
print(f"\033[91mAssuming the time step is {ts} s\033[0m")

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
        makespan = stats["makespan"]
        makespans.append(makespan)
        # cap runtimes to before makespan
        run_times = np.array(stats["qp_solve_time"])[:int(np.ceil(makespan / ts))]
        run_times = np.mean(run_times)
        run_times_all.append(run_times)
        
        qp_solve_times.append(stats["qp_solve_time"])

goal_reach_rate = np.mean(goal_reach_rates)
collision_count = np.mean(collision_counts)
success_rate = np.mean(success_rates)

run_times_all = np.array(run_times_all)
run_time_avg, run_time_ci = CI_compute(run_times_all)
makespan_avg, makespan_ci = CI_compute(np.array(makespans))

print(f"Stats are averaged across {num_exps} experiments")
print(f"Goal reach rate: {goal_reach_rate}")
print(f"Collision count: {collision_count}")
print(f"Success rate (assuming all robots reach goal): {success_rate}")
# print(f"QP solve time avg: {qp_solve_time_avg} (ms)")
# print(f"QP solve time std: {qp_solve_time_std} (ms)")
print(f"Makespan (for ones reached goals): {makespan} (s)")
# check if the "stats" folder exists, if not, create it
if not os.path.exists("stats"):
    os.makedirs("stats")

stats = {
    "goal_reach_rate": goal_reach_rate,
    "collision_count": collision_count,
    "success_rate": success_rate,
    "runtime_avg": run_time_avg,
    "runtime_ci": run_time_ci,
    "makespan": makespan_avg,
    "makespan_ci": makespan_ci,
    "instance_name": instance_name,
}

stats_path = os.path.join("stats", f"stats_{instance_name}.json")

# save the stats to a file
with open(stats_path, "w") as f:
    json.dump(stats, f, indent=4)