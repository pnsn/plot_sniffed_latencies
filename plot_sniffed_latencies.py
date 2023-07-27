#!/home/ahutko/miniconda3/envs/squac/bin/python

# Simple script that pulls measurement from the squac database of 10-minute-averaged
#   sniffed latencies and plots red/green for the maximum measurement within the
#   time window being above/below the threshold.
# Sniffed datacenters are eew-dev1 at MENLO, UCB, SCEDC and ewserver1 at PNSN.
#
# Usage:
# ./plot_sniffed_latencies.py starttime endtime datacenter threshold 'Fig title comment field'
#
# Example:
# ./plot_sniffed_latencies.py 2023-7-17T19:00 2023-7-17T19:40 UCB 60 'Fig title comment field'
#
# threshold is the maximum averaged latency in squac (sec)
# Datacenter options are: PNSN UCB SCEDC MENLO or All
# example output .png name: Sniffed_latencies_UCB_2023-07-17T1900_to_2023-07-17T1940.png
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

from squacapi_client import *
from squacapi_client.models import *
from squacapi_client.models.write_only_measurement_serializer import * 
from squacapi_client.pnsn_utilities import *

# Parse args
if len(sys.argv) > 4:
    try:
        T1str = sys.argv[1]
        T2str = sys.argv[2]
        datacenter = sys.argv[3]
        threshold = float(sys.argv[4])
        if ( len(sys.argv) > 5 ):
            strcomment = ' '.join(sys.argv[5:])
        else:
            strcomment = ''
    except:
        print("Need 4+ arguments: YYYY-MM-DDTHH:MM YYYY-MM-DDTHH:MM datacenter "+
              "threshold_in_sec (optional comments)")
        sys.exit()
else:
    print("Need 4+ arguments: YYYY-MM-DDTHH:MM YYYY-MM-DDTHH:MM datacenter "+
          "threshold_in_sec (optional comments)")
    sys.exit()
#print( T1str, T2str, datacenter )

# Import modules
try:
    from squacapi_client.models.write_only_measurement_serializer \
    import WriteOnlyMeasurementSerializer
    from squacapi_client.pnsn_utilities \
    import get_client, make_channel_map, make_metric_map, perform_bulk_create
    no_squacapi = False
except Exception as e:
    print("Info: squacapi_client not available, cannot use --squac option")
    no_squacapi = True

USER = os.environ['SQUACAPI_USER']
PASSWORD = os.environ['SQUACAPI_PASSWD']
#print(USER, PASSWORD)

# Choose production or staging server
HOST = 'https://squacapi.pnsn.org'

# Iniate the client
squac_client = get_client(USER, PASSWORD)

# Get all metrics; you'll need the right metric_id
squac_metrics = squac_client.api_measurement_metrics_list()
#print(squac_metrics[0])
metric_ids = []
metric_names = {}
for i in range(0,len(squac_metrics)):
    metric_ids.append(squac_metrics[i].id)
    #print(i,squac_metrics[i].id, squac_metrics[i].name)
    metric_names[squac_metrics[i].id] = squac_metrics[i].name

networks = [ 'AZ', 'BC', 'BK', 'CC', 'CE', 'CI', 'CN', 'IU', 'NC', 'NN', 'NP'
             'NV', 'OO', 'SB', 'UO', 'US', 'UW', 'WR', 'MB', 'IW' ]
if ( datacenter == 'PNSN' ):
    lonW, lonE, latS, latN = -127.4, -115., 41.3, 51.5
    latency_metric_id = [ 76 ]
    strdatacenter = 'PNSN ewserver1'
elif ( datacenter == 'MENLO' ):
    lonW, lonE, latS, latN = -125, -116, 33, 43
    latency_metric_id = [ 135 ]
    strdatacenter = 'Menlo dev1'
elif ( datacenter == 'SCEDC' ):
    lonW, lonE, latS, latN = -122, -113.5, 32, 38.
    latency_metric_id = [ 123 ]
    strdatacenter = 'Caltech dev1'
elif ( datacenter == 'UCB' ):
    lonW, lonE, latS, latN = -125, -117, 34, 43
    latency_metric_id = [ 129 ]
    strdatacenter = 'UCB dev1'
elif ( datacenter == 'All' ):
    lonW, lonE, latS, latN = -127.4, -113.5, 32, 53
    latency_metric_id = [ 76, 123, 129, 135 ]
    strdatacenter = 'PNSN ewserver1 & dev1 @ UCB, CIT, Menlo'
else:
    print("Invalid datacenter, choose: PNSN, MENLO, SCEDC, UCB, All")
    sys.exit()

# Read in baseline stations expected to be sniffed
f = open('stations.' + datacenter)
lines = f.readlines()
f.close()
baselinenetstacha = []
for line in lines:
    try:
        net = line.split('.')[0]
        sta = line.split('.')[1]
        cha = line.split('.')[2][0:3]
        if ( cha[2:3] == 'Z' and cha[0:2] in [ 'EN', 'HN', 'BH', 'HH', 'EH' ] ):
            baselinenetstacha.append(net + '.' + sta + '.' + cha)
    except:
        pass

# Read in file that has all the SNCLs and squac channel ids (faster than squac)
f = open('channels_squacids_west_coast')
lines = f.readlines()
f.close()
channels = {}
mychannels = []
stadict = {}
for line in lines:
    sncl = line.split()[0]
    chid = line.split()[1]
    stat = sncl.split('.')[1]
    channels[sncl] = [ chid, stat ]
    net = sncl.split('.')[0]
    chan = sncl.split('.')[3]
    lat = float(line.split()[4])
    lon = float(line.split()[5])
    stadict[sncl] = [ lat, lon ]
    netstacha = net + '.' + stat + '.' + chan
    if ( net in networks and 
         lat > latS and lat < latN and lon < lonE and lon > lonW and
         chan[0:2] in [ 'EN', 'HN', 'BH', 'HH', 'EH' ] and chan[2:3] == 'Z' and
         netstacha in baselinenetstacha ):
        mychannels.append(sncl)

# Make sure there is no redunancy
mychannels = list(set(mychannels))

T1 = datetime.datetime.strptime(T1str,'%Y-%m-%dT%H:%M')
T2 = datetime.datetime.strptime(T2str,'%Y-%m-%dT%H:%M')
#T1 = datetime.datetime(2022, 4, 20, 20, 30, 0)
#T2 = datetime.datetime(2022, 4, 20, 22, 50, 0)

values, latencies, counts = {}, {}, {}
for metric_id in latency_metric_id:
    metricname = metric_names[metric_id]
    for channel in mychannels:
        channel_id = channels[channel][0]
        sncl = channel
        net = sncl.split('.')[0]
        stat = sncl.split('.')[1]
        cha = sncl.split('.')[3]
        valuelist = []
        startlist = []
        n = 0
        valuelist = []
        startlist = []
        n = 0
        metricname = metric_names[metric_id]
        timebegin = timeit.default_timer()
        measurements = []
        try:
            print("QUERYING: ", sncl, metric_id, channel_id, T1, T2 )
            measurements = squac_client.api_measurement_measurements_list(metric=[metric_id], channel=[channel_id], starttime=T1, endtime=T2)
            timedone = timeit.default_timer()
            maxval = 0
            ncount = 0
            if ( sncl not in latencies ):
                if ( len(measurements) > 0 ):
                    for measurement in measurements:
                        valuelist.append(measurement.value)
                        startlist.append(measurement.starttime)
                        n += 1
                        ncount +=1
                        if ( sncl in latencies ):
                            if ( measurement.value > maxval ):
                                maxval = measurement.value
                                latencies[sncl] = [measurement.value, measurement.starttime, (measurement.endtime-measurement.starttime).total_seconds() ]
                        else:
                            maxval = measurement.value
                            latencies[sncl] = [ measurement.value, measurement.starttime, (measurement.endtime-measurement.starttime).total_seconds() ]
                        print('VALUES: ',sncl, channel_id, measurement.value, measurement.starttime, metricname, measurement.metric, ncount, maxval )
            if ( sncl not in counts ):
                counts[sncl] = ncount
            else:
                oldcount = counts[sncl]
                counts[sncl] = oldcount + ncount
        except:
            print("QUERY for measurements failed: ", metric_id, channel_id, T1, T2, sncl, channel )

StaLatGood, StaLonGood, StaLatBad, StaLonBad = [], [], [], []
StaLatGoodEHZ, StaLonGoodEHZ, StaLatBadEHZ, StaLonBadEHZ = [], [], [], []
StaLatDown, StaLonDown, StaLatDownEHZ, StaLonDownEHZ = [], [], [], []
for sncl in latencies:
    print(sncl, latencies[sncl][0], counts[sncl] )
    maxlatency = latencies[sncl][0]
    if ( sncl[-3:] != 'EHZ' ):
        if ( counts[sncl] > 0 and maxlatency <= threshold ):
            StaLatGood.append(stadict[sncl][0])
            StaLonGood.append(stadict[sncl][1])
        elif ( counts[sncl] > 0 and maxlatency > threshold ):
            StaLatBad.append(stadict[sncl][0])
            StaLonBad.append(stadict[sncl][1])
    else:
        if ( counts[sncl] > 0 and maxlatency <= threshold ):
            StaLatGoodEHZ.append(stadict[sncl][0])
            StaLonGoodEHZ.append(stadict[sncl][1])
        elif ( counts[sncl] > 0 and maxlatency > threshold ):
            StaLatBadEHZ.append(stadict[sncl][0])
            StaLonBadEHZ.append(stadict[sncl][1])
    if ( counts[sncl] > 0 and counts[sncl] < 5 ):
        print("WARNING ", counts[sncl], maxlatency, sncl )

for sncl in mychannels:
    if ( counts[sncl] == 0 ):
        if ( sncl[-3:] != 'EHZ' ):
            StaLatDown.append(stadict[sncl][0])
            StaLonDown.append(stadict[sncl][1])
        else:
            StaLatDownEHZ.append(stadict[sncl][0])
            StaLonDownEHZ.append(stadict[sncl][1])

#----- Make new map for Renate

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
scatplot = ax1.scatter(StaLonDown,StaLatDown,c='k',marker='^',s=size,edgecolor='k',transform=crs.PlateCarree(),label='Not sniffed ');
scatplot = ax1.scatter(StaLonBad,StaLatBad,c='r',marker='^',s=size,edgecolor='r',transform=crs.PlateCarree(),label='at one point > '+str(threshold)+'s');
scatplot = ax1.scatter(StaLonGood,StaLatGood,c='g',marker='^',s=size,edgecolor='g',transform=crs.PlateCarree(),label='always < '+str(threshold)+'s');
size=20
scatplot = ax1.scatter(StaLonDownEHZ,StaLatDownEHZ,c='k',marker='+',s=size,edgecolor='k',transform=crs.PlateCarree(),label='EHZ not sniffed ',linewidth=0.4);
scatplot = ax1.scatter(StaLonBadEHZ,StaLatBadEHZ,c='r',marker='+',s=size,edgecolor='r',transform=crs.PlateCarree(),label='EHZ at one point > '+str(threshold)+'s',linewidth=0.4);
scatplot = ax1.scatter(StaLonGoodEHZ,StaLatGoodEHZ,c='g',marker='+',s=size,edgecolor='g',transform=crs.PlateCarree(),label='EHZ always < '+str(threshold)+'s',linewidth=0.4);
ax1.legend(loc='upper right')

T1str = T1.strftime("%Y-%m-%dT%H:%M")
T2str = T2.strftime("%Y-%m-%dT%H:%M")
T1strfig = T1.strftime("%Y-%m-%dT%H%M")
T2strfig = T2.strftime("%Y-%m-%dT%H%M")
ax1.set_title('Sniffed latencies (averaged over 10-min) \n' + T1str + ' to ' + T2str + '\n' + 'on ' + strdatacenter + '\n' + strcomment )
plt.savefig('Sniffed_latencies_' + datacenter + '_' + T1strfig + '_to_' + T2strfig + '.png')

