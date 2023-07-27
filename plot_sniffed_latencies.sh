#!/bin/sh

cd /home/ahutko/proj/STATION_REPORT/DATA_MINING/PLOT_SNIFFED_LATENCIES/plot_sniffed_latencies

for datacenter in PNSN UCB MENLO SCEDC All
  do

date
echo '--------------'
./plot_sniffed_latencies.py 2023-7-17T19:00 2023-7-17T19:40 $datacenter 60 'During July 17 imports outage ~19:00-19:20'
echo '--------------'
date

done

