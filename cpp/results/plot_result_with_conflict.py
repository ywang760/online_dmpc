import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import json
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh
from matplotlib import colormaps as mcm
import argparse
import os

import colorsys


def plot_obstacle(obstacle_file_path, ax=None):
    obstacle_mesh = mesh.Mesh.from_file(obstacle_file_path)

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(
        Poly3DCollection(obstacle_mesh.vectors, facecolors="k", linewidths=1, alpha=0.1)
    )

    return ax


def plot_ellipsoid(ax, center, radii, color="k", alpha=0.1):
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    x = radii[0] * np.outer(np.cos(u), np.sin(v)) + center[0]
    y = radii[1] * np.outer(np.sin(u), np.sin(v)) + center[1]
    z = radii[2] * np.outer(np.ones_like(u), np.cos(v)) + center[2]
    ax.plot_surface(x, y, z, color=color, alpha=alpha)
    ax.scatter(*center, color=color)
    
instance_name = "default"
experiment_name = "single_run" # can be exp_1, exp_2, exp_3, exp_4, or single_run

trajectory_path = f"{instance_name}/{experiment_name}/trajectories_{instance_name}.txt"
log_path = f"{instance_name}/{experiment_name}/{instance_name}.log"
config_path = f"../config/config_{instance_name}.json"

with open(config_path, "r") as f:
    config = json.load(f)

N = config["N"]
N_cmd = config["Ncmd"]
pmin = config["pmin"]
pmax = config["pmax"]
po = np.array(config["po"]).T
pf = np.array(config["pf"]).T
po = po.reshape(1, 3, N)
pf = pf.reshape(1, 3, N_cmd)

all_pos = np.loadtxt(trajectory_path)
pk = []
for i in range(N_cmd):
    pk.append(all_pos[3 * i : 3 * (i + 1), :])
pk = np.array(pk).transpose(0, 2, 1)
T = 0.01 * (pk.shape[1] - 1)
t = np.arange(0, T + 0.01, 0.01)

# read the log file, find lines that start with "Collision"
with open(log_path, "r") as f:
    lines = f.readlines()
    collision_lines = [line for line in lines if line.startswith("Collision")]

import re
collision_pattern = re.compile(r"Vehicles (\d+) and (\d+) .* @ t = ([\d.]+)s")

r1s = []
r2s = []
collision_t = []
for line in collision_lines:
    match = collision_pattern.search(line)
    if match:
        r1s.append(int(match.group(1)))
        r2s.append(int(match.group(2)))
        collision_t.append(float(match.group(3)))

assert len(r1s) == len(r2s) == len(collision_t)

pk = pk[:, ::10, :]  # downsample for visualization
fig = plt.figure(figsize=(20, 20))
ax = fig.add_subplot(111, projection="3d")

def generateRGBColors(num_colors):
    output = []
    num_colors += 1 # to avoid the first color
    for index in range(1, num_colors):
        incremented_value = 1.0 * index / num_colors
        output.append(colorsys.hsv_to_rgb(incremented_value, 0.75, 0.75))
    return np.asarray(output)
colors = generateRGBColors(N_cmd)
# shuffle the colors
np.random.shuffle(colors)


for i in range(N_cmd):
    ax.plot(pk[i, :, 0], pk[i, :, 1], pk[i, :, 2], color=colors[i])
    
obstacle_lw = config["rmin_obs"]
obstacle_h = config["height_scaling_obs"] * obstacle_lw
obstacle_bbox_dis = [obstacle_lw, obstacle_lw, obstacle_h]
for i in range(N):
    if i >= N_cmd:
        plot_ellipsoid(ax, po[0, :, i], obstacle_bbox_dis, "k", alpha=0.025)

# plot the robot final positions
robot_lw = config["rmin"]
robot_h = config["height_scaling"] * robot_lw
robot_bbox_dis = [robot_lw, robot_lw, robot_h]
for i in range(N_cmd):
    plot_ellipsoid(ax, pf[0, :, i], robot_bbox_dis, color=colors[i], alpha=0.5)
    
# plot the collision points
for r1, r2, t in zip(r1s, r2s, collision_t):
    ax.scatter(pk[r1, int(t * 10), 0], pk[r1, int(t * 10), 1], pk[r1, int(t * 10), 2], c="r")
    # print(pk[r1, int(t * 10)])
    ax.scatter(pk[r2, int(t * 10), 0], pk[r2, int(t * 10), 1], pk[r2, int(t * 10), 2], c="r")
    # print(pk[r2, int(t * 10)])
    
# set the aspect ratio of the plot
ax.set_xlim(-14, 14)
ax.set_ylim(-14, 14)
ax.set_zlim(0, 12)

ax.set_aspect("equal")
# set the view angle from top, x-axis to the right, y-axis to the top
ax.view_init(elev=90, azim=-90)

# remove all grid and axes
# ax.grid(False)
# ax.axis("off")
plt.show()
# save fig compactly
# plt.savefig(f"/mnt/c/Users/asdfw/Downloads/DMPCSwap48.pdf", bbox_inches="tight", pad_inches=0)