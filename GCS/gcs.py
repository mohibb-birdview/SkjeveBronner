#/usr/bin/python3

import datetime
import math
import random
import time
from tkinter import TclError as TclError
import serial.tools.list_ports

import pprint
import matplotlib
import matplotlib.path as mplpath
import matplotlib.pyplot as plt
import numpy as np

from Functions import functions
from GCS import wellhead_sim as wh


DEBUG_MODE = True

SECONDS_TO_SHOW = 30
MAX_ANGLE = 3

# TODO: Fix x+ and z+
# TODO: Let streaming go to log file, and then make separate process for plotting


def generate_polygon(ctr_x, ctr_y, ave_radius, irregularity, spikeyness, num_verts):
    """
    Start with the centre of the polygon at ctrX, ctrY,
    then creates the polygon by sampling points on a circle around the centre.
    Randon noise is added by varying the angular spacing between sequential points,
    and by varying the radial distance of each point from the centre.

    Params:
    ctr_x, ctr_y -    coordinates of the "centre" of the polygon
    ave-radius -     in px, the average radius of this polygon, this roughly controls how large the polygon is,
                    really only useful for order of magnitude.
    irregularity -  [0,1] indicating how much variance there is in the angular spacing of vertices.
                    [0,1] will map to [0, 2pi/numberOfVerts]
    spikeyness -    [0,1] indicating how much variance there is in each vertex from the circle of radius aveRadius.
                    [0,1] will map to [0, aveRadius]
    num_verts -      self-explanatory

    Returns a list of vertices, in CCW order.
    """

    def clip(xx, minimum, maximum):
        if minimum > maximum:
            return xx
        elif xx < minimum:
            return minimum
        elif xx > maximum:
            return maximum
        else:
            return xx

    irregularity = clip(irregularity, 0, 1) * 2 * math.pi / num_verts
    spikeyness = clip(spikeyness, 0, 1) * ave_radius

    # generate n angle steps
    angle_steps = []
    lower = (2 * math.pi / num_verts) - irregularity
    upper = (2 * math.pi / num_verts) + irregularity
    total = 0
    for i in range(num_verts):
        tmp = random.uniform(lower, upper)
        angle_steps.append(tmp)
        total += tmp

    # normalize the steps so that point 0 and point n+1 are the same
    k = total / (2 * math.pi)
    for i in range(num_verts):
        angle_steps[i] = angle_steps[i] / k

    # now generate the points
    points = []
    angle = random.uniform(0, 2*math.pi)
    for i in range(num_verts):
        r_i = clip(random.gauss(ave_radius, spikeyness), 0, 2 * ave_radius)
        x = ctr_x + r_i * math.cos(angle)
        y = ctr_y + r_i * math.sin(angle)
        points.append((int(x), int(y)))
        angle = angle + angle_steps[i]

    return points


def create_plots():
    fig = plt.gcf()
    # fig.set_size_inches(17, 8)
    # move_figure(fig, 1980, 0)

    """ Create subplots and axis objects """
    timeline_x_ax = plt.subplot(2, 2, 2)
    timeline_x_ax.set_xlim([-SECONDS_TO_SHOW, 0])
    timeline_x_ax.set_ylim([-5, 5])
    timeline_x_ax.grid(True)
    timeline_x_ax.set_ylabel("Wellhead Angle")
    # plt.setp(timeline_x_ax.get_xticklabels(), visible=False)

    timeline_s_ax = plt.subplot(2, 2, 4, sharex=timeline_x_ax)
    timeline_s_ax.set_ylim([-0.5, 2.5])
    timeline_s_ax.grid(True)
    timeline_s_ax.set_xlabel("Time (s)")
    timeline_s_ax.set_yticks([0, 1, 2])
    timeline_s_ax.set_yticklabels(["OK", "", "Not OK"], rotation=45)

    """ Wellhead plot """
    pos_ax = plt.subplot(1, 2, 1)
    pos_ax.axis("equal")
    lim = MAX_ANGLE+0.5
    pos_ax.set_xlim([-lim, lim])
    pos_ax.set_ylim([-lim, lim])
    pos_ax.get_xaxis().set_visible(False)
    pos_ax.get_yaxis().set_visible(False)

    """ Create center cross """
    line_length = MAX_ANGLE + 0.2
    pos_ax.plot([0, 0], [-line_length, line_length], "k", linewidth=0.5)
    pos_ax.plot([-line_length, line_length], [0, 0], "k", linewidth=0.5)

    """ Create Circles and annotation """
    t = np.linspace(0, 2 * np.pi, 51)
    for d in np.arange(0, MAX_ANGLE+0.1, 0.5):
        x = d * np.sin(t)
        y = d * np.cos(t)
        pos_ax.plot(x, y, "k:", linewidth=0.5)

        if d != int(d):
            pos_ax.annotate("{:0.1f}°".format(d + 0.5), xy=(0.1, d + 0.45))
            pos_ax.annotate("{:0.1f}°".format(d + 0.5), xy=(0.1, -d - 0.55))

    """ Define polygon """
    poly1 = [
        (-2, 2),
        (1.2, 2.2),
        (1, 0),
        (1.6, -1.8),
        (0, -2.5),
        (-1, -1.1),
        (-2.3, -1.1),
    ]
    poly1 = list(np.array(poly1) * 1)

    poly_sim = generate_polygon(
        ctr_x=0,
        ctr_y=0,
        ave_radius=MAX_ANGLE,
        irregularity=0.2,
        spikeyness=0.4,
        num_verts=9
    )
    poly = poly1
    poly.append(poly[0])

    """ Create empty line objects for later """
    wellhead, = pos_ax.plot([], [], "ro-", markersize=10, markevery=[-1])
    history_x_line, = timeline_x_ax.plot([], [], "k-")
    history_y_line, = timeline_x_ax.plot([], [], "r-")
    history_s_line, = timeline_s_ax.plot([], [], "k-")
    timeline_x_ax.legend(["X", "Z"], loc="upper left")

    """ Plot polygon """
    pos_ax.plot([p[0] for p in poly], [p[1] for p in poly], "k--")  # Plot polygon
    poly_path = mplpath.Path(np.array(poly))  # Polygon path for calculations

    """ Insert photo """
    im = plt.imread('logo/Birdview-Logo-LowRess-RGB-(Digital).png')
    newax = fig.add_axes([0.455, 0.9, 0.1, 0.1], anchor='NE', zorder=-1)
    #newax.imshow(im)
    newax.axis('off')

    """ Return figure, axes and lines """
    plots =  {
        "fig": fig,
        "axes": {
            "time_x": timeline_x_ax,
            "time_s": timeline_s_ax,
            "wellhead": pos_ax,
        },
        "lines": {
            "time_x": history_x_line,
            "time_y": history_y_line,
            "time_s": history_s_line,
            "wellhead": wellhead,
            "poly": poly_path,
        },
    }

    return plots


def update_wellhead_plot(x, y, s, line):
    line.set_xdata([0, x])
    line.set_ydata([0, y])

    colors = [
        [0, 1, 0, 1],
        [0.8, 0.8, 0, 1],
        [1, 0, 0, 1],
    ]

    line.set_color(colors[s])


def update_history_plot(hx, hy, hs, ht, data):
    data["lines"]["time_x"].set_ydata(hx)
    data["lines"]["time_x"].set_xdata(ht)
    data["lines"]["time_y"].set_ydata(hy)
    data["lines"]["time_y"].set_xdata(ht)
    data["lines"]["time_s"].set_ydata(hs)
    data["lines"]["time_s"].set_xdata(ht)

    data["axes"]["time_x"].set_xlim([ht[-1] - SECONDS_TO_SHOW, ht[-1]])


def get_wellhead_status(pos, poly=None):
    if poly:
        if poly.contains_point(pos):
            return 0
        else:
            return 2

    distance_to_center = pos[0] * pos[0] + pos[1] * pos[1]
    if distance_to_center >= 4:
        return 2
    else:
        return 0


def main():
    try:
        data = create_plots()
        port = functions.get_port("GCS-UAV:", 1)
        wellhead = wh.Wellhead(port, 19200)

        """ Activate figure window """
        plt.ion()
        plt.show()

        """ Time keeping"""
        t_start = time.time()
        t_now = time.time() - t_start


        """ Objects for history plotting"""
        history_x = []
        history_y = []
        history_s = []
        history_t = []

        """ Get first position for calibration """
        first_position = wellhead.get_positions(t_now)

        """ Create log and write first lines """
        if DEBUG_MODE:
            log_name = "logs/DEBUG_LOG.csv"
        else:
            log_name = "logs/log_" + datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S") + ".csv"

        with open(log_name, "w+") as file:
            file.write("t,X,Y,status\n")
            status = get_wellhead_status(first_position, poly=data["lines"]["poly"])
            file.write("{:0.2f},{:0.3f},{:0.3f},{:d}\n".format(-1, *first_position, status))

        """ Main loop """
        while True:
            if plt.fignum_exists(data["fig"].number):
                pass
            else:
                exit(9)

            """ Update every 5 seconds """
            t_now = time.time() - t_start
            if int(t_now) % 5 == 0:
                positions = wellhead.get_positions(t_now)
                positions = tuple([positions[i] - first_position[i] for i in range(len(positions))])
                plt.pause(1)
                print(positions)
            else:
                plt.pause(0.1)
                continue

            """ Update histories """
            history_x.append(positions[0])
            history_y.append(positions[1])
            history_s.append(get_wellhead_status(positions, data["lines"]["poly"]))
            history_t.append(t_now)

            while history_t[0] < history_t[-1] - SECONDS_TO_SHOW - 5:
                history_t.pop(0)
                history_x.pop(0)
                history_s.pop(0)
                history_y.pop(0)

            """ Write to log """
            with open(log_name, "a+") as file:
                file.write("{:0.2f},{:0.3f},{:0.3f},{:d}\n".format(t_now, *positions, status))

            """ Update plots """
            update_wellhead_plot(history_x[-1], history_y[-1], history_s[-1], data["lines"]["wellhead"])
            update_history_plot(history_x, history_y, history_s, history_t, data)
            data["fig"].canvas.flush_events()

    except:
        raise

if __name__ == '__main__':
    main()