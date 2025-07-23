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
import cProfile
import pstats
import io


def plot_obstacle(obstacle_file_path, ax=None):
    obstacle_mesh = mesh.Mesh.from_file(obstacle_file_path)

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(
        Poly3DCollection(obstacle_mesh.vectors, facecolors="k", linewidths=1, alpha=0.1)
    )
    return ax


def plot_ellipsoid(center, radii, x_, y_, z_):
    x = radii[0] * x_ + center[0]
    y = radii[1] * y_ + center[1]
    z = radii[2] * z_ + center[2]
    return x, y, z


def extract_collisions(log_path):
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

    # sort the collisions by collision_t
    r1s, r2s, collision_t = zip(*sorted(zip(r1s, r2s, collision_t), key=lambda x: x[2]))

    return r1s, r2s, collision_t


def generateRGBColors(num_colors):
    output = []
    num_colors += 1  # to avoid the first color
    for index in range(1, num_colors):
        incremented_value = 1.0 * index / num_colors
        output.append(colorsys.hsv_to_rgb(incremented_value, 0.75, 0.75))
    return np.asarray(output)


def logistic(x, a=1, k=6, x0=0.5):
    return a / (1 + np.exp(-k * (x - x0)))


def scaled_logistic(f, f_max, a=1, k=6, x0=0.5):
    range = logistic(f_max, a, k, x0) - logistic(0, a, k, x0)
    f_ = a / range * (logistic(f, a, k, x0) - logistic(0, a, k, x0))
    return f_


def main():
    instance_name = "SwapClose48"
    experiment_name = (
        "single_run-old"  # can be exp_1, exp_2, exp_3, exp_4, or single_run
    )
    trajectory_path = (
        f"{instance_name}/{experiment_name}/trajectories_{instance_name}.txt"
    )
    log_path = f"{instance_name}/{experiment_name}/{instance_name}.log"
    config_path = f"../config/config_{instance_name}.json"
    plot_collisions = True
    plot_animation = True

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
    T = 0.01 * (pk.shape[1] - 1)  # original frame rate is 1/0.01 = 100 Hz
    t = np.arange(0, T + 0.01, 0.01)
    factor = 4
    pk = pk[:, :2500, :]  # to remove the static part
    pk = pk[
        :, ::factor, :
    ]  # downsample for visualization, so that the frame rate is 25 Hz
    ts = 0.01 * factor
    sorted_indices = np.lexsort((pk[:, 0, 2], pk[:, 0, 1], pk[:, 0, 0]))
    pk = pk[sorted_indices, :, :]

    # cache some ellipsoid calculations
    u = np.linspace(0, 2 * np.pi, 48)
    v = np.linspace(0, np.pi, 48)
    x_ = np.outer(np.cos(u), np.sin(v))
    y_ = np.outer(np.sin(u), np.sin(v))
    z_ = np.outer(np.ones_like(u), np.cos(v))

    # colors = generateRGBColors(N_cmd)
    # np.random.shuffle(colors)
    colors = np.load("Swap48_colors.npy")

    fig = plt.figure(figsize=(20, 20))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_xlim3d([-5, 5])
    ax.set_ylim3d([-3.6, 3.6])
    ax.set_zlim3d([0, 5])
    ax.set_aspect("equal")
    ax.view_init(elev=90, azim=-90)
    ax.grid(False)
    ax.axis("off")

    TRAJ_FRAME_COUNT = pk.shape[1]

    # Plot the obstacles
    obstacle_lw = config["rmin_obs"]
    obstacle_h = config["height_scaling_obs"] * obstacle_lw
    obstacle_bbox_dis = [obstacle_lw, obstacle_lw, obstacle_h]
    for i in range(N):
        if i >= N_cmd:
            # x, y, z = plot_ellipsoid(po[0, :, i], obstacle_bbox_dis, x_, y_, z_)
            # ax.plot_surface(x, y, z, color="k", alpha=0.025)
            ax.plot(
                [po[0, 0, i]],
                [po[0, 1, i]],
                [po[0, 2, i]],
                "ko",
                alpha=0.05,
                markersize=170,
            )

    robot_lw = config["rmin"] / 2
    robot_h = config["height_scaling"] * robot_lw
    robot_bbox_dis = [robot_lw, robot_lw, robot_h]

    # plot the collision points
    if plot_collisions:
        r1s, r2s, collision_t = extract_collisions(log_path)
        # for r1, r2, t in zip(r1s, r2s, collision_t):
        #     ax.scatter(
        #         pk[r1, int(t * factor), 0],
        #         pk[r1, int(t * factor), 1],
        #         pk[r1, int(t * factor), 2],
        #         c="r",
        #     )
        #     ax.scatter(
        #         pk[r2, int(t * factor), 0],
        #         pk[r2, int(t * factor), 1],
        #         pk[r2, int(t * factor), 2],
        #         c="r",
        #     )

    if plot_animation:
        fps = 1 / ts
        collision_frames = [int(t * fps) for t in collision_t]

        def get_view_angles(frame_index, fps):
            if frame_index <= 1 * fps:
                elev = 90
                azim = -90
                f = 0
            elif 1 * fps < frame_index <= 5 * fps:
                # elev go from 90 to 15 during 1 to 5 seconds, azim don't change
                fmax = 1
                f = (frame_index - 1 * fps) / (4 * fps) * fmax
                elev = 90 + (15 - 90) * scaled_logistic(f, fmax)
                azim = -90
            elif 5 * fps < frame_index <= 15 * fps:
                # elev remain 0, azim go from -90 to 0 to 90 during 5 to 13 seconds
                fmax = 2
                f = (frame_index - 5 * fps) / (10 * fps) * fmax
                elev = 15
                azim = -90 + 90 * scaled_logistic(f, fmax, k=3, a=2, x0=1)
            else:
                elev = 15
                azim = 90
                f = 0
            return elev, azim

        past_lines = [ax.plot([], [], [], color=color, alpha=1)[0] for color in colors]
        points = [
            ax.plot([], [], [], color=color, alpha=0.7, marker="o", markersize=20)[0]
            for color in colors
        ]

        if plot_collisions:
            collisions = ax.scatter([], [], [], c="r", alpha=0.7)

        DISPLAY_FRAME_COUNT = int(fps * (1 + 4 + 10))

        def animate(i):
            if i % 10 == 0:
                print(f"Frame {i}")
            # pk is of shape robot_count, time_steps, 3
            frame = min(i, TRAJ_FRAME_COUNT - 1)
            for k in range(N_cmd):
                past_lines[k].set_data(pk[k, : frame + 1, 0], pk[k, : frame + 1, 1])
                past_lines[k].set_3d_properties(pk[k, : frame + 1, 2])
                points[k].set_data([pk[k, frame, 0]], [pk[k, frame, 1]])
                points[k].set_3d_properties([pk[k, frame, 2]])

            if plot_collisions:
                # find the index of the first number in collision_t that is greater than i
                for j, t in enumerate(collision_frames):
                    if t > i:
                        break
                collision_t_index = j - 1
                print(f"collision_t_index: {collision_t_index}")
                if collision_t_index >= 0:
                    collision_points = []
                    for index in range(collision_t_index + 1):
                        r1 = r1s[index]
                        r2 = r2s[index]
                        t = collision_frames[index]
                        collision_points.append(pk[r1, t])
                        collision_points.append(pk[r2, t])
                    collision_points = np.array(collision_points)
                    collisions._offsets3d = (
                        collision_points[:, 0],
                        collision_points[:, 1],
                        collision_points[:, 2],
                    )

            if i > TRAJ_FRAME_COUNT:
                elev, azim = get_view_angles(i - TRAJ_FRAME_COUNT, fps=fps)
                ax.view_init(elev=elev, azim=azim)
            return past_lines + points

        plt.tight_layout()
        print(f"total frames: {TRAJ_FRAME_COUNT + DISPLAY_FRAME_COUNT}")
        ani = FuncAnimation(
            fig,
            animate,
            frames=TRAJ_FRAME_COUNT + DISPLAY_FRAME_COUNT,
            blit=True,
            interval=ts * 1000,
        )

        # write to file
        ani.save(
            f"simulation_Swap48.mp4",
            writer="ffmpeg",
        )

    else:
        # Plot the trajectories
        for i in range(N_cmd):
            ax.plot(pk[i, :, 0], pk[i, :, 1], pk[i, :, 2], color=colors[i])
        for i in range(N_cmd):
            x, y, z = plot_ellipsoid(pf[0, :, i], robot_bbox_dis, x_, y_, z_)
            ax.plot_surface(x, y, z, color=colors[i], alpha=0.5)

        # plt.savefig(
        #     f"/mnt/c/Users/asdfw/Downloads/DMPCSwap48.png",
        #     bbox_inches="tight",
        #     pad_inches=0,
        # )
        plt.show()


if __name__ == "__main__":
    main()
