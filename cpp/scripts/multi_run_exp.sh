#!/bin/bash
INSTANCE_NAME=$1
SIMULATION_DURATION=$2



if [ -z "$INSTANCE_NAME" ]; then
    echo "Please provide the instance name as an argument"
    exit 1
fi

base_dir=$(dirname "$(pwd)")
config_dir=${base_dir}/config
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


mkdir -p results/${INSTANCE_NAME}

cd bin
if [ -z "$SIMULATION_DURATION" ]
then
    SIMULATION_DURATION=60
fi


for exp_idx in {1..3}
do
    output_dir="../results/${INSTANCE_NAME}/exp_${exp_idx}"
    log_file_name="${output_dir}/${INSTANCE_NAME}.log"
    stat_file_name="${output_dir}/stats_${INSTANCE_NAME}.json"
    mkdir -p $output_dir
    if [ ! -f $stat_file_name ]; then
        echo "Start running the planner, simulation duration: $SIMULATION_DURATION"
        ./run "../config/config_${INSTANCE_NAME}.json" $SIMULATION_DURATION "${output_dir}/trajectories_${INSTANCE_NAME}.txt" $stat_file_name > $log_file_name
        echo "Output saved in folder ${output_dir}"
    fi
done