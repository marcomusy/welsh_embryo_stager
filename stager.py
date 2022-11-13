#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
from glob import glob
from datetime import datetime
import numpy as np
from vedo import __version__ as _vedo_version
from vedo import settings, mag, precision, load, sys_platform, show
from vedo import fit_circle, printc, Plotter, Text2D, Sphere
from vedo import Line, Ribbon, Spline, Points, Axes, Circle, Point, Picture
from vedo.utils import sort_by_column
from vedo.pyplot import plot, histogram
from vedo.applications import SplinePlotter
from utils import Limb, read_measured_points
from utils import find_extrema, fit_parabola, age_as_string, fdays

_version = "welsh_stager v0.4"

##################################################################### plots
datadir = "data/staged_welsh_reduced/"  # for training only


def plot_stats(do_plots=0):
    ages = []
    nominal_ages = []
    errors = []
    scores = []
    for f in glob(os.path.join(datadir, "*.txt")):
        embryo = Limb(f, author="welsh")
        result = predict(embryo.datapoints, do_plots=0)
        pic_array, best_age, sigma, best_score = result
        ages.append(best_age)
        nominal_ages.append(embryo.age)
        errors.append(sigma)
        scores.append(best_score)
        # if sigma<2:  print(embryo.filename, sigma)

    histogram(ages, xlim=(320, 370), bins=25, xtitle="age").show().close()
    histogram(scores, xtitle="scores", c="r4").show().close()
    histogram(errors, xtitle="age uncertainty /h", c="p4").show().close()

    fig = plot(nominal_ages, ages, "o", lw=0, title="nominal ages vs ages")
    fig += Line([310, 310], [370, 370], lw=2, c="r4")
    fig.show().close()

    fig = plot(sorted(ages), "o", lw=0, ms=0.8, title="ordered ages vs index (a bit meaningless)",)
    fig += Line([40, 320], [190, 360], lw=2, c="g4")
    fig.show().close()
    exit(0)


###################
def plot_2d_cloud():
    tits = "area", "aratio", "parabolic"
    limb_desc = []
    for filename in glob(os.path.join(datadir, "*.txt")):
        embryo = Limb(filename, author="welsh")
        spline = Spline(embryo.datapoints, res=200)
        area, aratio, parabolic = descriptors(spline.points(), do_plots=0)
        if area:
            limb_desc.append([area, aratio, embryo.age])
        else:
            print("zero area for", filename)
    limb_desc = np.array(limb_desc)

    rl = Points(limb_desc, r=12, c="g4").cmap("Reds", limb_desc[:, 2]).add_scalarbar3d()
    rl.scalarbar.use_bounds()
    show(
        rl, zoom=1.8, size=(1200, 900), axes=dict(xtitle=tits[0], ytitle=tits[1], ztitle="age/h"),
    )
    exit(0)


##################################################################
def generate_calibration_welsh(selected_agegroup=348, smooth=0.1):

    settings.use_parallel_projection = True  # press u to toggle

    ####### my imperfect timecourse (just for viz)
    tc = None
    # ref_shapes = load("data/marco/timecourse1d/*.vtk")
    # desc = []
    # for age in range(309, 361):
    #     eline = ref_shapes[age-249]
    #     eline = Spline(eline.cutWithPlane(origin=(1.5,0,0)), res=200) ### TEST CUT
    #     area, aratio, parabolic = descriptors(eline.points())[0]
    #     desc.append([area, aratio, parabolic])
    # tc = Line(desc).lw(1).c('k4')

    ####### welsh data
    tits = "area", "aspect ratio", "parabolic"

    limb_desc, ages, names, agegroup_pts = [], [], [], []
    for filename in glob(os.path.join(datadir, "*.txt")):
        embryo = Limb(filename, author="welsh")
        spline = Spline(embryo.datapoints, res=200)

        result, vobj = descriptors(spline.points())
        if result[0]:
            if embryo.age == selected_agegroup:
                agegroup_pts.append(result)
                n = os.path.basename(filename)
                n = n.replace(".txt", "").replace("_LHL", "").replace("_RHL", "").replace("_", "\_")
                names.append(n)
            limb_desc.append(result)
            ages.append(embryo.age)
        else:
            print("Error: zero area for", filename)

    rl = Points(limb_desc, r=12, c="g4").c("k").alpha(0.1)
    # rl.cmap('gist_ncar_r', ages).alpha(1).add_scalarbar3d()

    ag = Points(agegroup_pts, r=14, c="k2")
    labs = ag.labels(names, scale=0.15)

    # work out the average of the point cloud
    pts = rl
    for i in range(1, 3):
        pts = pts.clone().smoothMLS1D(f=1.2)
    pts.subsample(0.05)  # heavily subsample

    # order points by increasing area (axis=x=0)
    pts = sort_by_column(pts.points(), 0)
    aveline = Line(pts, lw=1, c="k1")

    aveline_s = Spline(aveline, res=100, smooth=smooth)  ###### DONT CHANGE 100
    aveline_s.c("k1").lw(4).pickable(True)

    # save this curve
    aveline_s.write("calibration_spline_welsh.vtk")
    printc("calibration SPLINE saved to: calibration_spline_welsh.vtk", c="g")

    ht = f"age group {age_as_string(selected_agegroup)} ({selected_agegroup}h)"

    ######### GENERATE and save the calibration curve
    # (the first and last agegroups are extrapolations)
    ids       = np.array([  0,   6,  11,  21,  44,  64,  77,  99]) # step along the aveline_s
    agegroups = np.array([318, 324, 330, 336, 342, 348, 354, 366]) # average age at that point
    index = np.where(agegroups==selected_agegroup)[0][0]

    calib = np.c_[ids, agegroups]
    calib_s = Spline(calib, res=100).c("b3")
    calib_s.write("calibration_table_welsh.vtk")
    printc("calibration TABLE  saved to: calibration_table_welsh.vtk", c="g")

    fig = plot(
        calib,
        "-o",
        xtitle="time course path length (steps)",
        ytitle="age (h)",
        title=ht,
        titleColor="r4",
        la=0.1,
        ma=1,
    )
    fig += calib_s
    fig += Point([ids[index], selected_agegroup], r=15, c="r4")
    fig.show(zoom=1.5, size=(1100, 825), title="CALIBRATION CURVE").close()

    aveline_pt = Point(aveline_s.points()[ids[index]], r=25, c="r4")

    show(
        tc, rl, ag, labs,
        aveline, aveline_s, aveline_pt,
        zoom=1.6, size=(1800, 1200),
        new=True,
        axes=dict(xtitle=tits[0], ytitle=tits[1], ztitle=tits[2], htitle=ht),
    )
    exit(0)


#####################################################################
def descriptors(datapoints, do_plots=False):

    eline = Spline(datapoints, res=200).c("b3").lw(4)
    eline.scale(1 / eline.average_size())

    ## first round ##
    cm1 = eline.center_of_mass()
    epts = eline.points()
    data_y = mag(epts - cm1)
    # Find peaks and valleys
    peak_x, green_peaks = find_extrema(data_y, n=5)
    valley_x, red_valleys = find_extrema(data_y, n=6, invert=True)
    if len(peak_x) == 0 or len(valley_x) == 0:
        return (0, 0, 0), []

    ## second round ##
    cm2, r2, _ = fit_circle(epts[peak_x])
    if not r2:
        return (0, 0, 0), []
    data_y = mag(epts - cm2)
    # Find peaks and valleys
    peak_x, green_peaks = find_extrema(data_y, n=5)
    valley_x, red_valleys = find_extrema(data_y, n=6, invert=True)
    if len(peak_x) == 0 or len(valley_x) == 0:
        return (0, 0, 0), []

    ## third round ##
    cm3, r3, _ = fit_circle(epts[peak_x])
    if not r3:
        return (0, 0, 0), []
    data_y = mag(epts - cm3)
    # Find peaks and valleys
    peak_x, green_peaks = find_extrema(data_y, n=5)
    valley_x, red_valleys = find_extrema(data_y, n=6, invert=True)
    if len(peak_x) == 0 or len(valley_x) == 0:
        return (0, 0, 0), []

    rib = Ribbon(green_peaks, red_valleys, alpha=0.1).z(0.1).lighting("off")
    area = rib.clean().triangulate().area() / r3 / 10
    xb = rib.xbounds()
    yb = rib.ybounds()
    aratio = 1000 * (yb[1] - yb[0]) / (xb[1] - xb[0]) / r3

    fitpar, parabolapts = fit_parabola(valley_x, red_valleys[:, 1])
    parabolic = 2e04 * fitpar[0] + 1

    ############ generate vedo obects for viz
    vobjs = []
    if do_plots:
        t = f"area={precision(area,3)},"
        t += f" a\_ratio={precision(aratio,3)},"
        t += f" parabolic={precision(parabolic,3)}"
        fig = plot(data_y, "-b", xtitle="index", ytitle="CM distance", title=t)
        fig += plot(green_peaks, "-g", like=fig)
        fig += plot(red_valleys, "-r", like=fig)
        fig += rib
        fig += Line(parabolapts)

        ptsg = Points(epts[peak_x], r=15, c="g5").lighting("off")
        ptsr = Points(epts[valley_x], r=15, c="r5").lighting("off")
        circle = Circle(cm3, r3, c="k6").z(-0.01).use_bounds(False)
        cm1 = Point(cm1, c="k4", r=4).lighting("off")
        cm2 = Point(cm2, c="k3", r=4).lighting("off")
        cm3 = Point(cm3, c="k1", r=5).lighting("off")
        rib2 = Ribbon(epts[valley_x], epts[valley_x[0] : valley_x[-1]], c="k5")
        rib2.lighting("off")

        vobjs = [eline, Axes(eline), rib2, circle, cm1, cm2, cm3, ptsg, ptsr, fig]

        # plt = Plotter(N=2, sharecam=False).background([250,250,255], at=0)
        # plt.show(eline, Axes(eline), rib2, circle, cm1, cm2, cm3, ptsg, ptsr, at=0)
        # plt.show(fig, at=1, zoom=1.15, mode='image').interactive().close()
    ########################

    result = np.array([area, aratio, parabolic]) * 10
    return result, vobjs


#####################################################################
def predict(datapoints, embryoname="", do_plots=True):

    result, vobj = descriptors(datapoints, do_plots=do_plots)

    tcourse = load(os.path.join("tuning", "calibration_spline.vtk")).c("k").lw(5)
    # tcourse = load('https://github.com/marcomusy/welsh_embryo_stager/blob/main/tuning/calibration_spline.vtk').c('k').lw(5)

    # the id (or step) is what we need to map to age
    idn = tcourse.closest_point(result, return_point_id=True)
    q = tcourse.points()[idn]

    # find the closest entry in the calibration curve
    calib = load(os.path.join("tuning", "calibration_table.vtk")).points()
    # calib = load('https://github.com/marcomusy/welsh_embryo_stager/blob/main/tuning/calibration_table.vtk').points()

    idt = (np.abs(calib[:, 0] - idn)).argmin()
    best_age = round(calib[idt][1])
    best_score = mag(result - q)

    r = best_score * 1.2
    sigma = len(tcourse.closest_point(result, radius=r, return_point_id=True))
    sigma = round((sigma + 1) / 2)  # heuristic
    pic_array = None

    if do_plots:
        err_sphere = Sphere(result, r=r, c="r5", alpha=0.1)
        axes = Axes(
            tcourse,
            xtitle="area",
            ytitle="aspect ratio",
            ztitle="parabolic",
            xtitle_backface_color="t",
            ytitle_backface_color="t",
            ztitle_backface_color="t",
        )
        pt = Point(result, r=15, c="r5")
        zshad = tcourse.zbounds()[0]

        joinline = Line(result, q).lw(3).c("g5")

        tcourse.add_shadow(plane="z", point=zshad).lw(1)
        tcourse_shad = tcourse.shadows[0].lw(1)
        ribtc = Ribbon(tcourse, tcourse_shad).c("k").alpha(0.1).lighting("off")

        txtf = Text2D(
            f"{embryoname}\nEmbryo is"
            f" {age_as_string(best_age)} \pm{sigma}h"
            f" (or E{fdays(best_age)}, {int(best_age+0.5)}h) ",
            pos="top-left",
            bg="purple6",
            s=1.2,
            alpha=0.7,
        )

        now = Text2D(
            f'User: {os.getlogin()}, {datetime.now().strftime("%c")}', pos="bottom-left", s=0.8,
        )
        vers = Text2D(f"{_version}, vedo {_vedo_version}", pos="bottom-right", s=0.7)
        chi2msg = Text2D(
            f"\chi\^2 = {precision(best_score,2)}", pos="top-right", s=1.1, font="Kanopus",
        )

        if not len(vobj):
            print("\nERROR: Could not find a solution. Try again with new points!\n")
            return [], 0, 0, 0

        plt = Plotter(
            size=(1800, 1000),
            shape="1|2",
            sharecam=False,
            title="Welsh Embryonic Mouse Staging System",
        )

        plt.at(0).show(vobj[:-1] + [txtf, now, vers], zoom="tight")
        plt.at(1).show(vobj[-1], zoom="tight")

        cam = dict(
            pos=(66.85, -24.10, 42.42),
            focalPoint=(34.89, 20.37, 9.009),
            viewup=(-0.2861, 0.4357, 0.8534),
            distance=64.14,
        )
        plt.at(2).show(
            tcourse, pt, joinline, tcourse_shad, ribtc, err_sphere, axes, chi2msg, camera=cam,
        )
        plt.background("w", "#dceef4")

        # create a png and text file
        if os.path.isdir("output"):
            basename, file_extension = os.path.splitext(embryoname)

            outf = os.path.join("output", embryoname.replace(file_extension, "_staging.png"))
            plt.screenshot(outf)
            # pic_array = plt.screenshot(asarray=True)

            # create a txt file
            outf = os.path.join("output", embryoname.replace(file_extension, ".txt"))
            with open(outf, "w") as f:
                f.write(f"{os.getlogin()} {basename}  u 1.0  0 0 0 0 {len(datapoints)}\n")
                for p in datapoints:
                    f.write(f"MEASURED {p[0]} {p[1]}\n")
            print(f"Output image and txt data saved to output/{basename}*")
        else:
            print("\nYou don't have a local directory 'output' so cannot write to it. Skip.\n")
            # pic_array = plt.screenshot(asarray=True)

        plt.interactive().close()

    return pic_array, best_age, sigma, best_score


#####################################################################
if __name__ == "__main__":

    settings.default_font = "Calco"
    settings.use_depth_peeling = sys_platform != "Darwin"

    # only for calibration:
    # generate_calibration_welsh()
    # plot_stats()

    if len(sys.argv):
        settings.window_splitting_position = 0.5
        settings.enable_default_mouse_callbacks = False

        filename = sys.argv[1]
        if not os.path.isfile(filename):
            print("\nPlease use an image or txt file as argument.\n")
            exit(0)

        if filename.lower().endswith(".txt"):
            name = os.path.basename(filename)
            datapoints = read_measured_points(filename)
            predict(datapoints, embryoname=name)
        else:
            try:
                pic = Picture(filename, channels=(0, 1, 2))
            except:
                print("\nPlease use a valid image or txt file with points coords.\n")
                exit(0)

            t = "Click to add a point\n"
            t+= "Right-click to remove it\n"
            t+= "Drag mouse to change constrast\n"
            t+= "Press c to clear points\n"
            t+= "Press q to proceed"
            instrucs = Text2D(t, pos="bottom-left", c="k1", bg="g9", font="Quikhand", alpha=0.5)

            plt = SplinePlotter(pic, size=(1200, 1000), title="Welsh Mouse Staging System")
            plt.mode = 'image'
            plt.verbose = False
            plt.start()
            datapoints = plt.points()
            # plt.close() # close the picture window

            if len(datapoints) > 5:
                name = os.path.basename(filename)
                result = predict(datapoints, embryoname=name)
            else:
                print("ERROR: not enough points to stage a limb!", len(datapoints))
