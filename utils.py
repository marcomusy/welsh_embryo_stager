#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
from vedo.utils import sortByColumn
from vedo import Plotter, Points, Spline
from scipy.optimize import curve_fit
from scipy import signal
import os

#########################################################################
class SplinePlotter(Plotter):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cpoints = []
        self.points = None
        self.spline = None

    def onLeftClick(self, evt):
        if not evt.actor: return
        p = evt.picked3d + [0,0,1]
        self.cpoints.append(p)
        self.update()
        # printc("Added point:", precision(p[:2],4), c='g')

    def onRightClick(self, evt):
        if evt.actor and len(self.cpoints):
            self.cpoints.pop() # pop removes from the list the last pt
            self.update()
            # printc("Deleted last point", c="r")

    def update(self):
        self.remove([self.spline, self.points])  # remove old points and spline
        self.points = Points(self.cpoints).ps(10).c('purple5')
        self.points.pickable(False)  # avoid picking the same point
        if len(self.cpoints) > 2:
            self.spline = Spline(self.cpoints, closed=False).c('yellow5').lw(3)
            self.add([self.points, self.spline])
        else:
            self.add(self.points)

    def keyPress(self, evt):
        if evt.keyPressed == 'c':
            self.cpoints = []
            self.remove([self.spline, self.points]).render()
            # printc("==== Cleared all points ====", c="r", invert=True)

    def datapoints(self):
        if not len(self.cpoints):
            return []
        return np.array(self.cpoints)[:,(0,1)]


#################################################################################
class Limb:

    def __init__(self, source='', author="unknown"):

        self.author = author.lower()
        self.datapoints = []
        self.side = 'U'
        self.name = ''
        self.filename = source
        self.icp_score = 0
        self.day=0
        self.hour = 0
        self.ageAsString=''
        self.litterID=''
        self.embryoID = ''
        self.age=0
        self.ageIndex = None
        self.age_in_minutes = 0
        self.age_h_m = (0, 0)
        self.extra_scale_factor = 1

        self.Line = None     # holds the actors
        self.LineReg = None

        if self.author == "james":
            self.extra_scale_factor = 4.545 # DO NOT CHANGE, check out scaling_mistake.py

        # fitting info
        self.fit_age = 0
        self.fit_points = []
        self.fit_error = 0
        self.fit_chi2 = 0
        self.fit_side = 0
        self.fit_delta_length = 0

        if not source:
            return

        if 'RH' in source:
            self.side = 'R'
        elif 'LH' in source:
            self.side = 'L'
        elif 'right' in source:
            self.side = 'R'
        elif 'left' in source:
            self.side = 'L'

        f = open(source, "r")
        lines = f.readlines()
        f.close()

        self.name = source.split('/')[-1]

        for i in range(len(lines)):
            if i<1: continue
            line = lines[i]
            if ',' in line:
                line = lines[i].split(',')
            else:
                line = lines[i].split()

            if line[0] == "MEASURED":
                self.datapoints.append([float(line[1]), float(line[2]), 0.0])
            elif line[0] == "FITSHAPE":
                self.fit_points.append([float(line[1]), float(line[2]), 0.0])
            elif line[0] == "RESULT":
                self.fit_age   = float(line[1])
                self.fit_error = float(line[2])
                self.fit_chi2  = float(line[3])
            elif line[0] == "Total": #  pick "Total lengths different by X per cent"
                self.fit_delta_length = float(line[4])/100.

        if "MIRRORED" in lines[i]:
            if self.side == "R":
                print("WARNING: staging system detected left but filename contains right", source)
                self.side == "R" ### CORRECT IT! (staging sys is very reliable on this)

        self.datapoints = np.array(self.datapoints) * self.extra_scale_factor

        if len(self.fit_points):
            self.fit_points = np.array(self.fit_points) * self.extra_scale_factor

        if self.side == 'L':
            self.datapoints[:,0] *= -1

        if self.author == "heura":
            sfn = self.name.split('.')
            self.day = int(sfn[0].replace("E",""))
            self.hour = int(sfn[1].split('_')[0])
            self.ageAsString = str(self.day)+"."+sfn[1].split('_')[0]
            self.litterID = sfn[1].split('_')[1]
            self.embryoID = ""
        elif self.author == "welsh":
            sfn = self.name
            sfn = sfn.replace('E13.0', 'E13;00_')
            sfn = sfn.replace('E13.25','E13;06_')
            sfn = sfn.replace('E13.5', 'E13;12_')
            sfn = sfn.replace('E13.75','E13;18_')
            sfn = sfn.replace('E14.0', 'E14;00_')
            sfn = sfn.replace('E14.25','E14;06_')
            sfn = sfn.replace('E14.5', 'E14;12_')
            sfn = sfn.replace('E14.75','E14;18_')
            sfn = sfn.replace('__','_')
            sfn = sfn.split('_')
            self.age = 0
            self.day = int(sfn[0].split(';')[0].replace("E",""))
            self.hour = int(sfn[0].split(';')[1])
            self.ageAsString = "E"+str(self.day)+"."+sfn[0].split(';')[1]
            self.litterID = sfn[1]
        else:
            sfn = self.name.split('_')
            self.age = 0
            self.day = int(sfn[0].split(';')[0].replace("E",""))
            self.hour = int(sfn[0].split(';')[1])
            self.ageAsString = "E"+str(self.day)+"."+sfn[0].split(';')[1]
            self.litterID = sfn[1]
            self.embryoID = sfn[2]

        self.age = 24*self.day + self.hour


#################################################################################
def load_welsh_limbs(source='data/staged_welsh/'):
    limbs = []
    if source.endswith(".npy"):
        llist = np.load(source, allow_pickle=True)
        for dlimb in llist:
            if "kevin" not in dlimb["author"]: continue
            lm = Limb(dlimb)
            limbs.append(lm)
    else:
        for fn in sorted(os.listdir(source)):
            if not fn.endswith(".txt"): continue
            lm = Limb(source+fn, author="welsh")
            limbs.append(lm)
    return limbs, ['13.00','13.06','13.12','13.18','14.00','14.06', '14.12', '14.18']


############################################### staging
def reposition(lines):
    # rigidly put a whole set of limb outlines about horizontal and their base
    # at (0,0,0) without modifying their relative positioning
    p0s = []
    p1s = []
    pvs = []
    for l in lines:
        pts = l.points()
        p0s.append(pts[0])
        p1s.append(pts[-1])
        pvs.append(pts[int(l.N()/2)])

    p0 = np.mean(np.array(p0s), axis=0)
    p1 = np.mean(np.array(p1s), axis=0)
    pm = (p0+p1)/2
    pv = np.mean(np.array(pvs), axis=0)
    v = (pv-pm)/ np.linalg.norm(pv-pm)

    cr = np.cross(v, [0,1,0])[2]
    a = np.arccos(np.dot([0,1,0], v)) * 57.3 * cr/abs(cr)
    for l in lines: #all get same shift and rotation
        l.shift(-pm).rotateZ(-90 + a)

###############################################
def read_measured_points(filename):
    # read txt file points

    f = open(filename, "r")
    lines = f.readlines()
    f.close()

    datapoints = []
    for i in range(len(lines)):
        if i<1: continue
        line = lines[i]
        if ',' in line:
            line = lines[i].split(',')
        else:
            line = lines[i].split()

        if line[0] == "MEASURED":
            datapoints.append([float(line[1]), float(line[2]), 0.0])

    return np.array(datapoints)


###############################################
def ageAsString(agehour):
    day = int(agehour/24.0)
    h   = int(agehour) - 24*day
    s = "0" if h<10 else ""
    return "E"+str(day)+":"+s+str(h)

def fdays(agehour):
    # days as float: compute age as e.g. E12.75
    agedec = agehour/24
    serie = np.linspace(8,20, num=(20-8)*20, endpoint=False)
    idmin = np.argmin(np.abs(serie-agedec))
    return np.round(serie[idmin], 2)

def fit_gauss(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    ids = np.where(y>0.1)[0].astype(int)

    x = x[ids]
    y = y[ids]
    mean = np.mean(x)
    sigma = 10

    def gaus(x, a, x0, sigma):
        return a * np.exp(-((x - x0) ** 2) / (2 * sigma ** 2))

    try:
        popt, pcov = curve_fit(gaus, x, y, p0=[1, mean, sigma])
    except:
        return 0, [], []

    #import matplotlib.pyplot as plt
    #plt.plot(x, y, "b+:", label="data")
    #plt.plot(x, gaus(x, *popt), "r-", label="fit")
    #plt.legend()
    #plt.show()

    return abs(popt[2]), x, gaus(x, *popt)


def fit_parabola(x, y):
    x = np.asarray(x)
    y = np.asarray(y)

    fit = np.polyfit(x, y, 2)
    f = np.poly1d(fit)

    # import matplotlib.pyplot as plt
    # plt.scatter(x,y)
    # plt.plot(x,f(x))
    # plt.show()
    # print(f)
    xx = np.linspace(0, 200)
    yy = f(xx)
    pts = np.c_[xx,yy]
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
    peaks = sortByColumn(peaks, 1, invert=True)[:n]
    peaks = sortByColumn(peaks, 0)
    peak_x, peak_y = peaks.T
    peak_ids = peak_x.astype(int)
    return peak_ids, peaks
