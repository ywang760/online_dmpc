#!/bin/bash

INSTANCE_NAME=$1
SIMULATION_DURATION=$2
LARGESCALE_DIR=$3
VIZ=false
RUN=false

# Parse arguments
shift 3
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --viz) VIZ=true ;;
        --r) RUN=true ;;
    esac
    shift
done

if [ -z "$INSTANCE_NAME" ] || [ -z "$SIMULATION_DURATION" ] || [ -z "$LARGESCALE_DIR" ]; then
    echo "Usage: $0 <instance_name> <simulation_duration> <largescale_dir> [--viz] [--r]"
    exit 1
fi

if [ ! -d "$LARGESCALE_DIR" ]; then
    echo "Error: LARGESCALE_DIR '$LARGESCALE_DIR' does not exist"
    exit 1
fi


base_dir=$(dirname "$(pwd)")
config_dir=${base_dir}/config

echo "-------Step 1: Syncing $INSTANCE_NAME from largescale-planning repo"
robot_config_dir="$LARGESCALE_DIR/lib/spawner/config_json/$INSTANCE_NAME"
obs_config_dir="$LARGESCALE_DIR/lib/map/examples"

if [ ! -d "$robot_config_dir" ]; then
    echo "Error: Robot config directory '$robot_config_dir' does not exist"
    exit 1
fi

if [ ! -d "$obs_config_dir" ]; then
    echo "Error: Obstacle config directory '$obs_config_dir' does not exist"
    exit 1
fi

for json_file in "$robot_config_dir"/simulation*.json; do
    if [ -f "$json_file" ]; then
        octomap_filename=$(jq -r '.octomap_filename' "$json_file")
        if [ "$octomap_filename" = "null" ]; then
            echo "Warning: No octomap_filename found in $json_file"
            continue
        fi
        # set octomap_filename to the basename of the octomap_filename
        octomap_filename=$(basename "$octomap_filename")
        # change the file extension from .bt to .stl
        octomap_filename="${octomap_filename%.bt}.stl"
        echo "Found octomap_filename: $octomap_filename"
    fi
done

if [ -z "$octomap_filename" ]; then
    echo "Error: No valid octomap filename found"
    exit 1
fi

mkdir -p "${config_dir}/${INSTANCE_NAME}"

echo "Copying simulation and robot configurations from $robot_config_dir"
echo "Copying obstacle from: $obs_config_dir"
cp -r "$robot_config_dir/." "${config_dir}/${INSTANCE_NAME}"

if [ ! -f "$obs_config_dir/$octomap_filename" ]; then
    echo "Error: Obstacle file '$obs_config_dir/$octomap_filename' not found"
    exit 1
fi
cp "$obs_config_dir/$octomap_filename" "${config_dir}/${INSTANCE_NAME}"

echo "-------Step 2: Converting configs to DMPC format"
cd $config_dir
python convert.py --instance_name "$INSTANCE_NAME"
# rm -r "${config_dir}/${INSTANCE_NAME}"

if [ "$VIZ" = true ]; then
    python visualize.py --instance_name "$INSTANCE_NAME"
fi

if [ "$RUN" = true ]; then
    echo "-------Step 3: Running DMPC for $INSTANCE_NAME"
    cd $base_dir/scripts
    if [ "$VIZ" = true ]; then
        bash run_single_exp.sh $INSTANCE_NAME $SIMULATION_DURATION --viz
    else
        bash run_single_exp.sh $INSTANCE_NAME $SIMULATION_DURATION
    fi
fi