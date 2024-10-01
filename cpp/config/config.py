import numpy as np
import json
from stl import mesh
import os
import sys


def process_obstacle(obstacle_file_path):
    obstacle_mesh = mesh.Mesh.from_file(obstacle_file_path)

    # Assuming each cube is represented by 8 vertices
    n_cubes = len(obstacle_mesh.vectors) // 12  # Each cube has 12 triangles

    cube_centers = []

    for i in range(n_cubes):
        # Extract the vertices of the current cube
        cube_vertices = obstacle_mesh.vectors[i * 12 : (i + 1) * 12].reshape(-1, 3)
        # Calculate the centroid of the cube
        centroid = np.mean(cube_vertices, axis=0).tolist()
        centroid = [round(x, 2) for x in centroid]
        cube_centers.append(centroid)

    rmin_obs_x = np.abs(cube_vertices[0][0] - cube_centers[-1][0])
    rmin_obs_y = np.abs(cube_vertices[0][1] - cube_centers[-1][1])
    assert np.allclose(
        rmin_obs_x, rmin_obs_y
    ), f"rmin_obs_x: {rmin_obs_x}, rmin_obs_y: {rmin_obs_y} is not close"
    rmin_obs = rmin_obs_x
    height_scaling_obs = np.abs(cube_vertices[0][2] - cube_centers[0][2]) / rmin_obs
    return cube_centers, round(rmin_obs, 2), height_scaling_obs


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
    obstacle_centers, rmin_obs, height_scaling_obs = process_obstacle(
        largescale_obstacle_file_path
    )
    obstacle_count = len(obstacle_centers)
    for i in range(obstacle_count):
        po.append(obstacle_centers[i])

    bbox_max = np.array(robot_config[0]["collision_shape_at_zero_max"])
    bbox_min = np.array(robot_config[0]["collision_shape_at_zero_min"])
    assert (
        np.all(bbox_max + bbox_min) == 0
    ), "The bounding box must be centered at the origin"
    assert bbox_max[0] == bbox_max[1], "The bounding box must be a cube"
    rmin = bbox_max[0]
    height_scaling = bbox_max[2] / rmin

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

    output_file_path = output_file_path or "config_updated.json"
    with open(output_file_path, "w") as f:
        json.dump(dmpc_original_config, f, indent=4)


if __name__ == "__main__":
    process_largescale_config(
        largescale_simulation_config_path="Swap48/simulation_config_swap.json",
        dmpc_original_config_path="config.json",
        output_file_path="config_Swap48.json",
    )
