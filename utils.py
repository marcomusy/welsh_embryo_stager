#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import numpy as np
from vedo.utils import sort_by_column
from scipy import signal


#################################################################################
class Limb:
    def __init__(self, source="", author="unknown"):

        self.author = author.lower()
        self.datapoints = []
        self.side = "U"
        self.name = ""
        self.filename = source
        self.icp_score = 0
        self.day = 0
        self.hour = 0
        self.age_as_string = ""
        self.litterID = ""
        self.embryoID = ""
        self.age = 0
        self.ageIndex = None
        self.age_in_minutes = 0
        self.age_h_m = (0, 0)
        self.extra_scale_factor = 1

        self.Line = None  # holds the actors
        self.LineReg = None

        if self.author == "james":
            self.extra_scale_factor = 4.545  # DO NOT CHANGE, check out scaling_mistake.py

        # fitting info
        self.fit_age = 0
        self.fit_points = []
        self.fit_error = 0
        self.fit_chi2 = 0
        self.fit_side = 0
        self.fit_delta_length = 0

        if not source:
            return

        if "RH" in source:
            self.side = "R"
        elif "LH" in source:
            self.side = "L"
        elif "right" in source:
            self.side = "R"
        elif "left" in source:
            self.side = "L"

        f = open(source, "r")
        lines = f.readlines()
        f.close()

        self.name = source.split("/")[-1]

        for i in range(len(lines)):
            if i < 1:
                continue
            line = lines[i]
            if "," in line:
                line = lines[i].split(",")
            else:
                line = lines[i].split()

            if line[0] == "MEASURED":
                self.datapoints.append([float(line[1]), float(line[2]), 0.0])
            elif line[0] == "FITSHAPE":
                self.fit_points.append([float(line[1]), float(line[2]), 0.0])
            elif line[0] == "RESULT":
                self.fit_age = float(line[1])
                self.fit_error = float(line[2])
                self.fit_chi2 = float(line[3])
            elif line[0] == "Total":  #  pick "Total lengths different by X per cent"
                self.fit_delta_length = float(line[4]) / 100.0

        if "MIRRORED" in lines[i]:
            if self.side == "R":
                print("WARNING: staging system detected left but filename contains right", source)
                self.side == "R"  ### CORRECT IT! (staging sys is very reliable on this)

        self.datapoints = np.array(self.datapoints) * self.extra_scale_factor

        if len(self.fit_points):
            self.fit_points = np.array(self.fit_points) * self.extra_scale_factor

        if self.side == "L":
            self.datapoints[:, 0] *= -1

        if self.author == "heura":
            sfn = self.name.split(".")
            self.day = int(sfn[0].replace("E", ""))
            self.hour = int(sfn[1].split("_")[0])
            self.age_as_string = str(self.day) + "." + sfn[1].split("_")[0]
            self.litterID = sfn[1].split("_")[1]
            self.embryoID = ""
        elif self.author == "welsh":
            sfn = self.name
            sfn = sfn.replace("E13.0", "E13;00_")
            sfn = sfn.replace("E13.25", "E13;06_")
            sfn = sfn.replace("E13.5", "E13;12_")
            sfn = sfn.replace("E13.75", "E13;18_")
            sfn = sfn.replace("E14.0", "E14;00_")
            sfn = sfn.replace("E14.25", "E14;06_")
            sfn = sfn.replace("E14.5", "E14;12_")
            sfn = sfn.replace("E14.75", "E14;18_")
            sfn = sfn.replace("__", "_")
            sfn = sfn.split("_")
            self.age = 0
            try:
                self.day = int(sfn[0].split(";")[0].replace("E", ""))
                self.hour = int(sfn[0].split(";")[1])
                self.age_as_string = "E" + str(self.day) + "." + sfn[0].split(";")[1]
                self.litterID = sfn[1]
            except:
                # not in the usual format E...
                pass
        else:
            sfn = self.name.split("_")
            self.age = 0
            self.day = int(sfn[0].split(";")[0].replace("E", ""))
            self.hour = int(sfn[0].split(";")[1])
            self.age_as_string = "E" + str(self.day) + "." + sfn[0].split(";")[1]
            self.litterID = sfn[1]
            self.embryoID = sfn[2]

        self.age = 24 * self.day + self.hour


#################################################################################
def load_welsh_limbs(source="data/staged_welsh/"):
    limbs = []
    if source.endswith(".npy"):
        llist = np.load(source, allow_pickle=True)
        for dlimb in llist:
            if "kevin" not in dlimb["author"]:
                continue
            lm = Limb(dlimb)
            limbs.append(lm)
    else:
        for fn in sorted(os.listdir(source)):
            if not fn.endswith(".txt"):
                continue
            lm = Limb(source + fn, author="welsh")
            limbs.append(lm)
    return limbs, ["13.00", "13.06", "13.12", "13.18", "14.00", "14.06", "14.12", "14.18"]


###############################################
def read_measured_points(filename):
    # read txt file points

    with open(filename, "r") as f:
        lines = f.readlines()

    datapoints = []
    for i, line in enumerate(lines):
        if not i:
            continue
        if "," in line:
            line = lines[i].split(",")
        else:
            line = lines[i].split()

        if line[0] == "MEASURED":
            datapoints.append([float(line[1]), float(line[2]), 0.0])

    return np.array(datapoints)


###############################################
def age_as_string(agehour):
    day = int(agehour / 24.0)
    h = int(agehour) - 24 * day
    s = "0" if h < 10 else ""
    return "E" + str(day) + ":" + s + str(h)

def age_in_hours(name):
    age = os.path.basename(name).split("_")[0]
    age = age.replace("E", "")
    agehour = float(age)*24
    return np.round(agehour).astype(int)

def fdays(agehour):
    # days as float: compute age as e.g. E12.75
    agedec = agehour / 24
    serie = np.linspace(8, 20, num=(20 - 8) * 20, endpoint=False)
    idmin = np.argmin(np.abs(serie - agedec))
    return np.round(serie[idmin], 2)


def fit_parabola(x, y):
    x = np.asarray(x)
    y = np.asarray(y)

    fit = np.polyfit(x, y, 2)
    f = np.poly1d(fit)

    xx = np.linspace(0, 200)
    yy = f(xx)
    pts = np.c_[xx, yy]
    return fit, pts


########################################
def find_extrema(data, n=5, distance=20, invert=False):
    # find the n largest peaks or valleys
    if invert:
        peak_ids = signal.find_peaks(-data, distance=distance)[0]
    else:
        peak_ids = signal.find_peaks(data, distance=distance)[0]
    peak_x = peak_ids
    peak_y = data[peak_ids]
    peaks = np.c_[peak_x, peak_y]
    peaks = sort_by_column(peaks, 1, invert=True)[:n]
    peaks = sort_by_column(peaks, 0)
    peak_x, peak_y = peaks.T
    peak_ids = peak_x.astype(int)
    return peak_ids, peaks
