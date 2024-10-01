import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import json
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh
from matplotlib import colormaps as mcm


def plot_obstacle(obstacle_file_path, ax=None):
    obstacle_mesh = mesh.Mesh.from_file(obstacle_file_path)

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(
        Poly3DCollection(obstacle_mesh.vectors, facecolors="k", linewidths=1, alpha=0.1)
    )

    return ax


def plot_ellipsoid(ax, center, radii, color="k"):
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    x = radii[0] * np.outer(np.cos(u), np.sin(v)) + center[0]
    y = radii[1] * np.outer(np.sin(u), np.sin(v)) + center[1]
    z = radii[2] * np.outer(np.ones_like(u), np.cos(v)) + center[2]
    ax.plot_surface(x, y, z, color=color, alpha=0.1)
    ax.scatter(*center, c=color)


# TODO: modify this
instance_name = "Swap48"

view_states = False
view_animation = True

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

all_pos = np.loadtxt(f"trajectories_{instance_name}.txt")
pk = []
for i in range(N_cmd):
    pk.append(all_pos[3 * i : 3 * (i + 1), :])
pk = np.array(pk).transpose(1, 2, 0)
T = 0.01 * (pk.shape[1] - 1)
t = np.arange(0, T + 0.01, 0.01)

# This is not working
# if view_states:
#     for i in range(N_cmd):
#         plt.figure(1)
#         diff = pk[:, :, i] - np.tile(pf[:, :, i], (len(t), 1)).T
#         dist = np.sqrt(np.sum(diff**2, axis=0))
#         plt.plot(t, dist, linewidth=1.5)
#         plt.grid(True)
#         plt.xlabel("t [s]")
#         plt.ylabel("Distance to target [m]")
#         plt.figure(2)
#         plt.subplot(3, 1, 1)
#         plt.plot(t, pk[0, :, i], linewidth=1.5)
#         plt.plot(t, pmin[0] * np.ones(len(t)), "--r", linewidth=1.5)
#         plt.plot(t, pmax[0] * np.ones(len(t)), "--r", linewidth=1.5)
#         plt.ylabel("x [m]")
#         plt.xlabel("t [s]")
#         plt.grid(True)
#         plt.subplot(3, 1, 2)
#         plt.plot(t, pk[1, :, i], linewidth=1.5)
#         plt.plot(t, pmin[1] * np.ones(len(t)), "--r", linewidth=1.5)
#         plt.plot(t, pmax[1] * np.ones(len(t)), "--r", linewidth=1.5)
#         plt.ylabel("y [m]")
#         plt.xlabel("t [s]")
#         plt.grid(True)
#         plt.subplot(3, 1, 3)
#         plt.plot(t, pk[2, :, i], linewidth=1.5)
#         plt.plot(t, pmin[2] * np.ones(len(t)), "--r", linewidth=1.5)
#         plt.plot(t, pmax[2] * np.ones(len(t)), "--r", linewidth=1.5)
#         plt.ylabel("z [m]")
#         plt.xlabel("t [s]")
#         plt.grid(True)

# Downsample for better visualization
pk = pk[:, ::10, :]

if view_animation:
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    colormap = mcm["plasma"]
    colors = [colormap(i / N_cmd) for i in range(N_cmd)]

    # Initialize points list
    points = []

    # Initial plot to create the points
    for i in range(N):
        if i < N_cmd:
            (point_pk,) = ax.plot([], [], [], "o", linewidth=2, color=colors[i])
            (point_po,) = ax.plot([], [], [], "^", linewidth=2, color=colors[i])
            (point_pf,) = ax.plot([], [], [], "x", linewidth=2, color=colors[i])
            points.append((point_pk, point_po, point_pf))

    def update(frame):
        ax.set_xlim(pmin[0], pmax[0])
        ax.set_ylim(pmin[1], pmax[1])
        ax.set_zlim(0, pmax[2])
        for i in range(N):
            if i < N_cmd:
                points[i][0].set_data([pk[0, frame, i]], [pk[1, frame, i]])
                points[i][0].set_3d_properties(pk[2, frame, i])
                points[i][1].set_data([po[0, 0, i]], [po[0, 1, i]])
                points[i][1].set_3d_properties(po[0, 2, i])
                points[i][2].set_data([pf[0, 0, i]], [pf[0, 1, i]])
                points[i][2].set_3d_properties(pf[0, 2, i])
        return [point for sublist in points for point in sublist]

    # Plot the obstacles
    obstacle_lw = config["rmin_obs"]
    obstacle_h = config["height_scaling_obs"] * obstacle_lw
    obstacle_bbox_dis = [obstacle_lw, obstacle_lw, obstacle_h]
    for i in range(N):
        if i >= N_cmd:
            plot_ellipsoid(ax, po[0, :, i], obstacle_bbox_dis, "r")

    anim = FuncAnimation(fig, update, frames=range(pk.shape[1]), blit=True)
    # plt.show()
    # save animation
    anim.save("DMPC_Swap48.mp4", writer="ffmpeg", fps=30)
