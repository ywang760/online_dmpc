import numpy as np
import json
from stl import mesh
import os
import sys

def create_cube_centers(instance="forest_small_5"):
    if instance == "forest_small_5":
        xy_cent = [[-2.15, -6.95], [-7.95, -5.85], [5.55, -2.55], [7.65, -5.75], [9.15, -3.75], [-7.65, 5.85], [-6.15, 6.55], [-3.15, 7.25], [6.25, 1.15], [2.35, 5.95], [8.25, 2.85], [0.55, 8.95], [3.15, -3.45], [-4.15, -2.75], [0.65, -6.45], [1.85, -0.65], [0.35, -3.25], [0.75, -3.55], [3.25, -8.65], [3.35, -7.95]]
        cube_centers = []
        for i in range(11):
            z = round(i * 0.9 + 0.45, 2)
            for item in xy_cent:
                cube_centers.append([item[0], item[1], z])
        return cube_centers, 0.45, 1.0
    
def process_obstacle(obstacle_file_path, r_obs=1.0, height_scaling_obs=1.0):
    # Model the obstacle as a union of spheres with radius rmin_obs and height_scaling_obs
    obstacle_mesh = mesh.Mesh.from_file(obstacle_file_path)

    # Assuming each cube is represented by 8 vertices
    n_cubes = len(obstacle_mesh.vectors) // 12  # Each cube has 12 triangles
    d_obs = 2 * r_obs
    h_obs = 2 * r_obs * height_scaling_obs

    cube_centers = []

    for i in range(n_cubes):
        # Extract the vertices of the current cube
        cube_vertices = obstacle_mesh.vectors[i * 12 : (i + 1) * 12].reshape(-1, 3)
        xmin, xmax = np.min(cube_vertices[:, 0]), np.max(cube_vertices[:, 0])
        ymin, ymax = np.min(cube_vertices[:, 1]), np.max(cube_vertices[:, 1])
        zmin, zmax = np.min(cube_vertices[:, 2]), np.max(cube_vertices[:, 2])
        # print(
        #     f"Cube {i}: xmin={xmin}, xmax={xmax}, ymin={ymin}, ymax={ymax}, zmin={zmin}, zmax={zmax}"
        # )
        length, width, height = xmax - xmin, ymax - ymin, zmax - zmin
        print(f"Cube {i}: dx={length}, dy={width}, dz={height}")

        # Calculate the centers of the smaller spheres
        x = np.arange(xmin + r_obs, xmax, r_obs)
        y = np.arange(ymin + r_obs, ymax, r_obs)
        z = np.arange(zmin + r_obs, zmax, r_obs)
        xx, yy, zz = np.meshgrid(x, y, z)
        centers = np.vstack([xx.ravel(), yy.ravel(), zz.ravel()]).T
        cube_centers.extend(centers.tolist())

    return cube_centers, r_obs, height_scaling_obs


def process_largescale_config(
    largescale_simulation_config_path,
    dmpc_original_config_path,
    output_file_path=None,
):
    # Generate a DMPC config file from the large-scale config file by updating the start/goal position of agents, while retaining other parameters
    with open(largescale_simulation_config_path, "r") as f:
        simulation_config = json.load(f)
    largescale_robot_config_path = os.path.join(
        os.path.dirname(largescale_simulation_config_path),
        os.path.basename(simulation_config["robot_config_filename"]),
    )
    largescale_obstacle_file_path = os.path.join(
        os.path.dirname(largescale_simulation_config_path),
        os.path.basename(simulation_config["octomap_filename"])[:-2] + "stl",
    )

    with open(largescale_robot_config_path, "r") as f:
        robot_config = json.load(f)
    with open(dmpc_original_config_path, "r") as f:
        dmpc_original_config = json.load(f)

    # Update agent positions
    agent_count = len(robot_config)
    po = []
    pf = []
    for i, agent in enumerate(robot_config):
        po.append(agent["start_position"])
        pf.append(agent["goal_position"])
    if "forest_small_5" in largescale_obstacle_file_path:
        obstacle_centers, rmin_obs, height_scaling_obs = create_cube_centers()
        print(f"Octomap is forest_small_5, using predefined cube centers")
    else:
        obstacle_centers, rmin_obs, height_scaling_obs = process_obstacle(
            largescale_obstacle_file_path, r_obs=0.8, height_scaling_obs=1.0
        )
        print("\033[91mConstructing obstacle centers from the octomap file, may not be accurate\033[0m")
    obstacle_count = len(obstacle_centers)
    for i in range(obstacle_count):
        po.append(obstacle_centers[i])
        
    bbox = np.array(simulation_config["collision_shape"])
    assert bbox[0] == bbox[1], "The bounding box must be a cube"
    rmin = bbox[0] * 2
    height_scaling = bbox[2] / bbox[0]

    dmpc_original_config["po"] = po
    dmpc_original_config["pf"] = pf
    dmpc_original_config["N"] = agent_count + obstacle_count
    dmpc_original_config["Ncmd"] = agent_count
    dmpc_original_config["rmin"] = rmin
    dmpc_original_config["height_scaling"] = height_scaling
    dmpc_original_config["rmin_obs"] = rmin_obs
    dmpc_original_config["height_scaling_obs"] = height_scaling_obs
    dmpc_original_config["pmin"] = simulation_config["workspace_min"]
    dmpc_original_config["pmax"] = simulation_config["workspace_max"]
    
    # maybe also change khor
    
    acc = simulation_config["max_derivatives"][1][1]
    dmpc_original_config["amin"] = [-acc] * 3
    dmpc_original_config["amax"] = [acc] * 3
    # dmpc_original_config["std_position"] = 0
    # dmpc_original_config["std_velocity"] = 0

    output_file_path = output_file_path or "config_updated.json"
    with open(output_file_path, "w") as f:
        json.dump(dmpc_original_config, f, indent=4)
    print(f"Updated config file saved at {output_file_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Process large-scale simulation config"
    )
    parser.add_argument(
        "-i",
        "--instance_name",
        type=str,
        required=True,
        help="Name of the instance, i.e. SwapClose48",
    )
    args = parser.parse_args()
    instance_name = args.instance_name

    # find the path of the large-scale simulation config file, which is in the folder "instance_name" and start with "simulation" and end with ".json"
    largescale_simulation_config_path = os.path.join(
        instance_name,
        [
            file
            for file in os.listdir(instance_name)
            if file.startswith("simulation") and file.endswith(".json")
        ][0],
    )
    # print(f"Large-scale simulation config path: {largescale_simulation_config_path}")
    dmpc_original_config_path = "config.json"
    output_file_path = f"config_{instance_name}.json"

    # largescale_simulation_config_path="SwapClose48/simulation_config_swap.json"
    # dmpc_original_config_path="config.json"
    # output_file_path="config_SwapClose48.json"
    process_largescale_config(
        largescale_simulation_config_path,
        dmpc_original_config_path,
        output_file_path,
    )
    print(f"Successfully converted instance {instance_name}")
