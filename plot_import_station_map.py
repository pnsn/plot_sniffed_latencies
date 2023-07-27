#!/home/ahutko/miniconda3/envs/squac/bin/python

# Simple script to plot up station map(s) by import machine.
#
# Alex Hutko July 2023

import os
import sys
import argparse
import datetime
from pytz import timezone
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.dates import DateFormatter,drange
import timeit
from cartopy import crs
from cartopy import feature
import geopy

todaystr = datetime.date.today().strftime("%B %d, %Y")

# AE.113A.--.HHZ 39492 2015-03-27T00:00:00 2599-12-31T23:59:59 32.768299 -113.766701 100.0 118.0
f = open('channels_squacids_west_coast')
lines = f.readlines()
coordinatesdic = {}
for line in lines:
    try:
        sncl = line.split()[0]
        lat = float(line.split()[4])
        lon = float(line.split()[5])
        coordinatesdic[sncl] = [ lat, lon ]
    except:
        pass

lonW, lonE, latS, latN = -125., -112.5, 41.3, 50.2
imports = [ 'importAll', 'import01', 'import02', 'import03', 'import04', 'import05', 'import06', 'importEHZ' ]

importdic = {}
xdic, ydic  = {}, {}
for machine in imports:
    print('Doing: ', machine)
    importdic[machine] = []
    f = open(machine + '.all')
    lines = f.readlines()
    f.close()
    xdic[machine], ydic[machine] = [], []
    for line in lines:
        try:
            sncl = line.split()[2] + '.' + line.split()[0] + '.' + line.split()[3] + '.' + line.split()[1]
            xdic[machine].append(coordinatesdic[sncl][1])
            ydic[machine].append(coordinatesdic[sncl][0])
        except:
            pass
    print('LEN: ', len(xdic[machine]) )
#    print(x)
#    print(y)
    fig = plt.figure(figsize=(6,8),dpi=180)
    plt.clf()
    gs1 = gridspec.GridSpec(1,1)
    gs1.update(left=0.05,right=0.95,bottom=0.02,top=0.89,wspace=0.01)
    size = 80
    latmid,lonmid = 45.8,-120.4
    proj = crs.LambertConformal(central_longitude = lonmid, central_latitude = latmid)
    res = '50m'  # 50m or 10m
    ax1 = plt.subplot(gs1[:,:],projection=proj)
    ax1.set_extent([ lonW, lonE, latS, latN ])
    ax1.add_feature (feature.LAND.with_scale(res),facecolor='white')
    ax1.add_feature (feature.OCEAN.with_scale(res),facecolor='lightblue',alpha=0.25)
    ax1.add_feature(feature.COASTLINE.with_scale(res))
    ax1.add_feature (feature.LAKES.with_scale(res),facecolor='lightblue',alpha = 0.25)
    ax1.add_feature (feature.STATES.with_scale(res));
    size = 10
    if ( machine != 'importAll' ):
        scatplot = ax1.scatter(xdic['importAll'],ydic['importAll'],c='pink',marker='^',s=size,edgecolor='pink',transform=crs.PlateCarree(),label='other',alpha=0.5);
    scatplot = ax1.scatter(xdic[machine],ydic[machine],c='b',marker='^',s=size,edgecolor='b',transform=crs.PlateCarree(),label=machine);
    ax1.set_title(machine + '     ' + todaystr )
    ax1.legend(loc='upper right')
    plt.savefig(machine+ '.png')

