#!/bin/bash

INSTANCE_NAME=$1
SIMULATION_DURATION=$2
VIZ=false

# Parse arguments
shift 2
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --viz) VIZ=true ;;
    esac
    shift
done

if [ -z "$INSTANCE_NAME" ]; then
    echo "Please provide the instance name as an argument"
    exit 1
fi

base_dir=$(dirname "$(pwd)")

cd $base_dir

if [ -d "bin" ] && [ -f "bin/run" ]; then
    echo "Planner binary exists"
else
    echo "Planner binary does not exist, building the planner"
    cd build
    cmake ..
    make
    cd ..
fi

output_dir="results/${INSTANCE_NAME}/single_run"
mkdir -p results/${INSTANCE_NAME}/single_run

cd bin
if [ -z "$SIMULATION_DURATION" ]
then
    SIMULATION_DURATION=60
fi
echo "Start running the planner, simulation duration: $SIMULATION_DURATION"
./run "../config/config_${INSTANCE_NAME}.json" $SIMULATION_DURATION ../${output_dir}/trajectories_${INSTANCE_NAME}.txt > ../${output_dir}/${INSTANCE_NAME}.log
echo "Planner finished, results are saved in ${output_dir}/trajectories_${INSTANCE_NAME}.txt"
echo "Log is saved in ${output_dir}/${INSTANCE_NAME}.log"

cd $base_dir

if [ "$VIZ" = true ]; then
    python results/plot_results.py -p "${output_dir}/trajectories_${INSTANCE_NAME}.txt" --save_name "DMPC_${INSTANCE_NAME}.mp4"
fi