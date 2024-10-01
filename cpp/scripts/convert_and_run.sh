# Assume the configs are copied from largescale_planning to configs/{instance_name}
INSTANCE_NAME=$1
SIMULATION_DURATION=$2

# Check if the instance name is provided
if [ -z "$INSTANCE_NAME" ]
then
    echo "Please provide the instance name"
    exit 1
fi

CURRENT_DIR=$(pwd)
cd ../config

echo "---------------Step 1: Converting configs to json"
python config.py --instance_name "$INSTANCE_NAME"

echo "---------------Step 2: Visualize the config"
python visualize.py --instance_name "$INSTANCE_NAME"

echo "---------------Step 3: Run the planner"
# check if the bin directory exist and the run executable is there, otherwise build the planner
cd $CURRENT_DIR
if [ -d "../bin" ] && [ -f "../bin/run" ]
then
    echo "Planner binary exists"
else
    echo "Planner binary does not exist, building the planner"
    cd ../
    mkdir -p build
    cd build
    cmake ..
    make
    cd ../bin
fi

cd $CURRENT_DIR
cd ../
mkdir -p results
mkdir -p log
cd bin

# set the simulation duration if provided, otherwise default to 60
if [ -z "$SIMULATION_DURATION" ]
then
    SIMULATION_DURATION=60
fi
echo "Start running the planner, simulation duration: $SIMULATION_DURATION"
./run "../config/config_${INSTANCE_NAME}.json" $SIMULATION_DURATION ../results/trajectories_${INSTANCE_NAME}.txt > ../log/${INSTANCE_NAME}.log
echo "Planner finished, results are saved in results/trajectories_${INSTANCE_NAME}.txt"
echo "Log is saved in log/${INSTANCE_NAME}.log"

cd $CURRENT_DIR

echo "---------------Step 4: Visualize the results"
cd ../results
python plot_results.py --instance_name "$INSTANCE_NAME" --save_name "DMPC_${INSTANCE_NAME}.mp4"

