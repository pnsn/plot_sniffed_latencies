plot_sniffed_latencies.py

Simple script to plot sniffed latencies from the SQUAC db.

The measurements considered are 10-minute averages of sniffed latencies (end of packet time minus now, plus half-packet length).
Sniffed servers at datacenters are eew-dev1 at MENLO, UCB, SCEDC and ewserver1 at PNSN.

This script collects the measurements of averaged latencies within the time window specified and simply asks is that average above or below the user specified threshold.
Green is a station whose average was always below the threshold, Red is a station whos maximum average is above the threshold.
Black is a station that was sniffed in the past, but not within the specified time-window, e.g. the station had been down for months.

Usage:<br>
  ./plot_sniffed_latencies.py starttime endtime datacenter threshold 'Fig title comment field'

Example:<br>
  ./plot_sniffed_latencies.py 2023-7-17T19:00 2023-7-17T19:40 UCB 60 'Fig title comment field'

threshold is the maximum averaged latency in squac (sec) <br>
Datacenter options are: PNSN UCB SCEDC MENLO or All <br>
example output .png name: Sniffed_latencies_UCB_2023-07-17T1900_to_2023-07-17T1940.png

