#!/bin/bash
INSTANCE_NAME=$1
SIMULATION_DURATION=$2

if [ -z "$INSTANCE_NAME" ]; then
    echo "Please provide the instance name as an argument"
    exit 1
fi

if [ -z "$SIMULATION_DURATION" ]
then
    SIMULATION_DURATION=60
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

for exp_idx in {1..10}
do
    cd $base_dir/bin
    output_dir="results/${INSTANCE_NAME}/exp_${exp_idx}"
    log_file_name="../${output_dir}/${INSTANCE_NAME}.log"
    stat_file_name="../${output_dir}/stats_${INSTANCE_NAME}.json"
    mkdir -p ../$output_dir
    if [ ! -f $stat_file_name ]; then
        echo "Starting DMPC ${INSTANCE_NAME} experiment ${exp_idx}, simulation duration: $SIMULATION_DURATION"
        ./run "../config/config_${INSTANCE_NAME}.json" $SIMULATION_DURATION "../${output_dir}/trajectories_${INSTANCE_NAME}.txt" $stat_file_name > $log_file_name
        echo "Output saved in folder ${output_dir}"
    fi
    cd $base_dir
    python results/postprocess.py -o ${output_dir} -c config/config_${INSTANCE_NAME}.json
done

cd $base_dir
python results/stats.py -i results/${INSTANCE_NAME}

echo -e "--------------------END OF ${INSTANCE_NAME} EXPERIMENTS--------------------\n"