# script to run multiple experiments

import os
import subprocess
instance_names = [
    "Circle10",
    "Circle20",
    "Circle30",
    "Circle40",
    "Circle50",
    "Circle60",
    "Circle70",
    "Circle80",
    "Circle90",
    # "Circle74"
]

simulation_time = 60

for instance_name in instance_names:
    result = subprocess.run(
        f"bash sync_and_run.sh {instance_name} {simulation_time}",
        shell=True,
        stdout=subprocess.DEVNULL,  # Suppress stdout
        stderr=subprocess.PIPE      # Capture stderr
    )

    if result.stderr:
        print(result.stderr.decode())
    else:
        print(f"Successfully synced {instance_name}")
        
        result = subprocess.run(
            f"bash multi_run_exp.sh {instance_name} {simulation_time}",
            shell=True,
            stderr=subprocess.PIPE      # Capture stderr
        )