#!/bin/bash

INSTANCE_NAME=$1
SIMULATION_DURATION=$2
VIZ=false

# Parse arguments
shift 2
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --viz) VIZ=true ;;
        *) echo "Unknown option: $1" ;;
    esac
    shift
done

if [ -z "$INSTANCE_NAME" ]; then
    echo "Please provide the instance name as an argument"
    exit 1
fi


base_dir=$(dirname "$(pwd)")
config_dir=${base_dir}/config

echo "-------Step 1: Syncing $INSTANCE_NAME from largescale-planning repo"
LARGESCALE_DIR="/root/projects/largescale-planning"
robot_config_dir="$LARGESCALE_DIR/lib/spawner/config_json/$INSTANCE_NAME"
obs_config_dir="$LARGESCALE_DIR/lib/map/examples"

for json_file in "$robot_config_dir"/simulation*.json; do
    if [ -f "$json_file" ]; then
        octomap_filename=$(jq -r '.octomap_filename' "$json_file")
        # set octomap_filename to the basename of the octomap_filename
        octomap_filename=$(basename "$octomap_filename")
        # change the file extension from .bt to .stl
        octomap_filename="${octomap_filename%.bt}.stl"
        echo "Found octomap_filename: $octomap_filename"
    fi
done

mkdir -p "${config_dir}/${INSTANCE_NAME}"

echo "Copying simulation and robot configurations from $robot_config_dir"
echo "Copying obstacle from: $obs_config_dir"
cp -r "$robot_config_dir/." "${config_dir}/${INSTANCE_NAME}"
cp "$obs_config_dir/$octomap_filename" "${config_dir}/${INSTANCE_NAME}"

echo "-------Step 2: Converting configs to DMPC format"
cd $config_dir
python convert.py --instance_name "$INSTANCE_NAME"

if [ "$VIZ" = true ]; then
    python visualize.py --instance_name "$INSTANCE_NAME"
fi

echo "-------Step 3: Running the planner"
cd $base_dir/scripts
bash run_single_exp.sh $INSTANCE_NAME $SIMULATION_DURATION