#!/bin/bash

# script to run multiple experiments

# TODO: change these parameters as needed
instance_names=(
    "Circle10"
    "Circle20"
    "Circle30"
    "Circle40"
    "Circle50"
    "Circle60"
    "Circle70"
    "Circle80"
    "Circle90"
    # "Circle74"
    # "Move192"
    # "Swap48"
)
simulation_time=60
LARGESCALE_DIR="/root/projects/largescale-planning"  # Set this path as needed

for instance_name in "${instance_names[@]}"; do
    echo "Processing $instance_name..."
    
    bash sync_and_run.sh "$instance_name" "$simulation_time" "$LARGESCALE_DIR"
    bash multi_run_exp.sh "$instance_name" "$simulation_time"
    
    echo "Completed $instance_name"
done

# run postprocess_stats to aggregate all stats
cd "$(dirname "$(pwd)")"
python3 results/postprocess_stats.py