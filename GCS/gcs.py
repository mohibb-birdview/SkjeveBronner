#/usr/bin/python3

import datetime
import math
import random
import time
from tkinter import TclError as TclError
import serial.tools.list_ports

import matplotlib
import matplotlib.path as mplpath
import matplotlib.pyplot as plt
import numpy as np
# import wellhead_sim as wh

SECONDS_TO_SHOW = 30
MAX_ANGLE = 3


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
    timeline_x_ax.set_xlim([0, SECONDS_TO_SHOW])
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
    newax.imshow(im)
    newax.axis('off')

    """ Return figure, axes and lines """
    return {
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


if __name__ == '__main__':
    create_plots()
    plt.show()
