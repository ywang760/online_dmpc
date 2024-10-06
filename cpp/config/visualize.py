import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import json

from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh


def plot_obstacle(obstacle_file_path, ax=None):
    obstacle_mesh = mesh.Mesh.from_file(obstacle_file_path)

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(
        Poly3DCollection(obstacle_mesh.vectors, facecolors="k", linewidths=1, alpha=0.1)
    )
    return ax


def plot_cube(ax, pmin, pmax, color="k"):
    # Define the 8 vertices of the cube
    vertices = np.array(
        [
            [pmin[0], pmin[1], pmin[2]],
            [pmax[0], pmin[1], pmin[2]],
            [pmax[0], pmax[1], pmin[2]],
            [pmin[0], pmax[1], pmin[2]],
            [pmin[0], pmin[1], pmax[2]],
            [pmax[0], pmin[1], pmax[2]],
            [pmax[0], pmax[1], pmax[2]],
            [pmin[0], pmax[1], pmax[2]],
        ]
    )

    # Define the 6 faces of the cube using the vertices
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # Bottom face
        [vertices[4], vertices[5], vertices[6], vertices[7]],  # Top face
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # Front face
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # Back face
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # Right face
        [vertices[4], vertices[7], vertices[3], vertices[0]],  # Left face
    ]

    # Create a Poly3DCollection object
    poly3d = Poly3DCollection(
        faces, facecolors=color, linewidths=1, edgecolors=color, alpha=0.1
    )

    ax.add_collection3d(poly3d)
    center = (pmin + pmax) / 2
    ax.scatter(*center, c=color)


def plot_ellipsoid(ax, center, radii, color="k"):
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    x = radii[0] * np.outer(np.cos(u), np.sin(v)) + center[0]
    y = radii[1] * np.outer(np.sin(u), np.sin(v)) + center[1]
    z = radii[2] * np.outer(np.ones_like(u), np.cos(v)) + center[2]
    ax.plot_surface(x, y, z, color=color, alpha=0.1)
    ax.scatter(*center, c=color)


def visualize_config(config_path, obstacle_stl_path=None):
    with open(config_path, "r") as f:
        config = json.load(f)

    # Load parameters from config
    po = np.array(config["po"])
    pf = np.array(config["pf"])
    N = config["N"]
    Ncmd = config["Ncmd"]
    assert len(po) == N, "po must have N elements"
    assert len(pf) == Ncmd, "pf must have Ncmd elements"
    assert po.shape[1] == pf.shape[1] == 3, "po and pf must have 3 columns"
    agent_count = config["Ncmd"]
    obstacle_count = N - agent_count
    print(f"Agent count: {agent_count}, Obstacle count: {obstacle_count}")
    pmin = config["pmin"]
    pmax = config["pmax"]
    agent_lw = config["rmin"]
    agent_h = config["height_scaling"] * agent_lw
    obstacle_lw = config["rmin_obs"]
    obstacle_h = config["height_scaling_obs"] * obstacle_lw

    agent_pos = po[:agent_count]
    obstacle_pos = po[agent_count:]

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.set_xlim(pmin[0], pmax[0])
    ax.set_ylim(pmin[1], pmax[1])
    ax.set_zlim(pmin[2], pmax[2])

    agent_bbox_dis = [agent_lw, agent_lw, agent_h]
    for i in range(agent_count):
        # plot_cube(ax, agent_pos[i] - agent_bbox_dis, agent_pos[i] + agent_bbox_dis, "b")
        plot_ellipsoid(ax, pf[i], agent_bbox_dis, "b")

    obstacle_bbox_dis = [obstacle_lw, obstacle_lw, obstacle_h]
    for i in range(obstacle_count):
        # plot_cube(
        #     ax,
        #     obstacle_pos[i] - obstacle_bbox_dis,
        #     obstacle_pos[i] + obstacle_bbox_dis,
        #     "r",
        # )
        plot_ellipsoid(ax, obstacle_pos[i], obstacle_bbox_dis, "r")

    if obstacle_stl_path:
        plot_obstacle(obstacle_stl_path, ax)  # Cross validate with the obstacle file

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.set_xlim(-6, 6)
    ax.set_ylim(-6, 6)
    ax.set_zlim(0, 12)
    ax.set_aspect("equal")
    # plt.show()


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Visualize DMPC config")
    parser.add_argument(
        "-i",
        "--instance_name",
        type=str,
        required=True,
        help="Name of the instance, i.e. SwapClose48",
    )
    args = parser.parse_args()
    instance_name = args.instance_name

    config_path = f"config_{instance_name}.json"
    # find the obstacle_stl_path by finding a *stl file in the instance_name folder
    obstacle_stl_path = f"{instance_name}/{[file for file in os.listdir(instance_name) if file.endswith('.stl')][0]}"

    instance_name = "SwapClose48"  # TODO: change this
    config_path = f"config_{instance_name}.json"
    obstacle_stl_path = f"{instance_name}/two_columns_close.stl"  # TODO: change this

    print(f"Visualizing config file: {config_path}, obstacle file: {obstacle_stl_path}")
    visualize_config(config_path=config_path, obstacle_stl_path=obstacle_stl_path)
    plt.show()
    plt.savefig(f"{instance_name}/config.png")
    print(f"Visualization saved at {instance_name}/config.png")
