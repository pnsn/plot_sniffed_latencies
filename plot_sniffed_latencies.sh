#!/bin/sh

cd /home/ahutko/proj/STATION_REPORT/DATA_MINING/PLOT_SNIFFED_LATENCIES/plot_sniffed_latencies

starttime=`date -d "-1 days" +%Y-%m-%dT%H:00:00`
endtime=`date +%Y-%m-%dT%H:00:00`

for datacenter in PNSN UCB MENLO SCEDC All
  do

date
echo '--------------'
./plot_sniffed_latencies.py $starttime $endtime $datacenter 60 ' '
#./plot_sniffed_latencies.py 2023-7-17T19:00 2023-7-17T19:40 $datacenter 60 'During July 17 imports outage ~19:00-19:20'
echo '--------------'
date

done

dir=`date -u +%Y-%m`
mkdir $dir
ssh ahutko@seismo "mkdir -p /home/ahutko/public_html/IMPORT_CHANNELS/Sniffed_latencies/$dir"
/bin/cp Sniffed_latencies*$dir*.png $dir
rsync $dir/Sniffed_late*.png ahutko@seismo:/home/ahutko/public_html/IMPORT_CHANNELS/Sniffed_latencies/$dir

